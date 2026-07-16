"""Calculs statistiques partages entre le Dashboard et la page Statistiques.

Toutes les fonctions sont pures : elles ne font aucune requete, elles operent
uniquement sur des listes déjà recuperees aupres des Services existants (une
seule fois par module, cote appelant). Objectif : le Dashboard et les
Statistiques ne recalculent jamais deux fois la meme information (cf.
Sprint 12.2).

Volontairement independant de PySide6 : ce module reste dans la couche
Services (aucune dependance a l'interface), reutilisable par n'importe quelle
page.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any

FACTURE_STATUSES = ("pending", "partial", "paid", "cancelled")
DEVIS_STATUSES = ("draft", "sent", "accepted", "refused", "expired")


def ca_facture(factures: list[Any]) -> float:
    """Chiffre d'affaires facture : somme des montants des factures non
    annulees."""
    return round(sum(float(f.montant or 0) for f in factures if f.status != "cancelled"), 2)


def ca_encaisse(paiements: list[Any]) -> float:
    """Chiffre d'affaires encaisse : somme des paiements non annules (meme
    regle que PaiementService.total_paid(), appliquee globalement)."""
    return round(sum(float(p.montant or 0) for p in paiements if p.status != "cancelled"), 2)


def montant_restant_a_encaisser(factures: list[Any], paiements: list[Any]) -> float:
    """Montant facture non encore encaisse (peut être negatif en cas de
    trop-percu global)."""
    return round(ca_facture(factures) - ca_encaisse(paiements), 2)


def count_factures_by_status(factures: list[Any]) -> dict[str, int]:
    counts = {status: 0 for status in FACTURE_STATUSES}
    for facture in factures:
        if facture.status in counts:
            counts[facture.status] += 1
    return counts


def count_devis_by_status(devis_list: list[Any]) -> dict[str, int]:
    counts = {status: 0 for status in DEVIS_STATUSES}
    for devis in devis_list:
        if devis.status in counts:
            counts[devis.status] += 1
    return counts


def factures_impayees_count(factures: list[Any]) -> int:
    return sum(1 for facture in factures if facture.status in ("pending", "partial"))


def paiements_en_attente_count(paiements: list[Any]) -> int:
    return sum(1 for paiement in paiements if paiement.status == "pending")


def _parse_date(value: str) -> date | None:
    try:
        return datetime.strptime(value, "%d/%m/%Y").date()
    except (TypeError, ValueError):
        return None


def upcoming_prestations(prestations: list[Any], limit: int | None = None) -> list[Any]:
    """Prestations a venir (date_debut >= aujourd'hui), les annulees
    exclues, triees par date croissante."""
    today = date.today()
    entries = []

    for prestation in prestations:
        if prestation.statut == "annulee":
            continue
        parsed = _parse_date(prestation.date_debut)
        if parsed is not None and parsed >= today:
            entries.append((parsed, prestation))

    entries.sort(key=lambda entry: entry[0])
    result = [prestation for _parsed, prestation in entries]
    return result[:limit] if limit is not None else result


def top_organisateurs(prestations: list[Any], organizations: list[Any], limit: int = 10) -> list[tuple[str, int]]:
    """Les organisateurs ayant le plus de prestations, classes par ordre
    decroissant. Les prestations sans organisateur rattache sont ignorees."""
    names_by_id = {organization.id: (organization.name or f"Organisateur #{organization.id}") for organization in organizations}
    counts: dict[str, int] = {}

    for prestation in prestations:
        name = names_by_id.get(prestation.organization_id)
        if name is None:
            continue
        counts[name] = counts.get(name, 0) + 1

    ranked = sorted(counts.items(), key=lambda entry: entry[1], reverse=True)
    return ranked[:limit]


# ===== Bloc "A traiter" (v1.1) =====
#
# Calculs partages entre le Dashboard et une future page dediee : chaque
# fonction opere uniquement sur des listes deja recuperees aupres des
# Services existants (meme principe que le reste de ce module), jamais de
# requete SQL ici.

def jours_de_retard(echeance: str, today: date | None = None) -> int | None:
    """Nombre de jours ecoules depuis une echeance depassee (None si la
    date est vide ou non reconnue)."""
    parsed = _parse_date(echeance)
    if parsed is None:
        return None
    return ((today or date.today()) - parsed).days


def jours_avant_expiration(date_validite: str, today: date | None = None) -> int | None:
    """Nombre de jours restants avant une date de validite (None si la date
    est vide ou non reconnue)."""
    parsed = _parse_date(date_validite)
    if parsed is None:
        return None
    return (parsed - (today or date.today())).days


def factures_en_retard(factures: list[Any], today: date | None = None) -> list[Any]:
    """Factures non soldees (pending/partial) dont l'echeance est depassee,
    triees de la plus en retard a la moins en retard."""
    today = today or date.today()
    entries = []

    for facture in factures:
        if facture.status not in ("pending", "partial"):
            continue
        parsed = _parse_date(facture.echeance)
        if parsed is not None and parsed < today:
            entries.append((parsed, facture))

    entries.sort(key=lambda entry: entry[0])
    return [facture for _parsed, facture in entries]


def devis_expirant_bientot(devis_list: list[Any], within_days: int = 7, today: date | None = None) -> list[Any]:
    """Devis envoyes (status "sent") dont la date de validite arrive a
    echeance sous `within_days` jours (aujourd'hui inclus), tries par
    date de validite croissante. Un devis deja expire (date depassee) n'est
    pas remonte ici : voir la transition vers le status "expired"."""
    today = today or date.today()
    horizon = today + timedelta(days=within_days)
    entries = []

    for devis in devis_list:
        if devis.status != "sent":
            continue
        parsed = _parse_date(devis.date_validite)
        if parsed is not None and today <= parsed <= horizon:
            entries.append((parsed, devis))

    entries.sort(key=lambda entry: entry[0])
    return [devis for _parsed, devis in entries]


def prestations_sans_facture(prestations: list[Any], factures: list[Any]) -> list[Any]:
    """Prestations confirmees ou realisees sans facture active (non annulee)
    associee - un evenement honore qui n'a pas encore ete facture."""
    facturees = {
        facture.prestation_id
        for facture in factures
        if facture.prestation_id is not None and facture.status != "cancelled"
    }
    return [
        prestation
        for prestation in prestations
        if prestation.statut in ("confirmee", "realisee") and prestation.id not in facturees
    ]


def cddu_a_preparer(prestations: list[Any], contrats_cddu: list[Any]) -> list[Any]:
    """Prestations confirmees ou realisees impliquant un artiste ou une
    formation, sans CDDU cree pour cette prestation - un contrat de travail
    qui reste a etablir."""
    couvertes = {
        contrat.prestation_id
        for contrat in contrats_cddu
        if contrat.prestation_id is not None
    }
    return [
        prestation
        for prestation in prestations
        if prestation.statut in ("confirmee", "realisee")
        and prestation.id not in couvertes
        and (prestation.artist_id is not None or prestation.formation_id is not None)
    ]


def documents_a_generer(
    devis_list: list[Any],
    contracts: list[Any],
    factures: list[Any],
    contrats_cddu: list[Any],
) -> list[tuple[str, Any]]:
    """Enregistrements actifs sans document DOCX genere (docx_path vide) -
    des documents qu'il reste materiellement a produire, tous modules
    confondus. Chaque entree est un couple (type, objet)."""
    entries: list[tuple[str, Any]] = []

    for devis in devis_list:
        if devis.status in ("draft", "sent", "accepted") and not devis.docx_path:
            entries.append(("Devis", devis))
    for contract in contracts:
        if contract.status in ("draft", "validated", "signed") and not contract.docx_path:
            entries.append(("Contrat", contract))
    for facture in factures:
        if facture.status in ("pending", "partial", "paid") and not facture.docx_path:
            entries.append(("Facture", facture))
    for contrat in contrats_cddu:
        if contrat.status != "archived" and not contrat.docx_path:
            entries.append(("CDDU", contrat))

    return entries


# ===== Chiffre d'affaires par periode (v1.1) =====

def ca_facture_periode(factures: list[Any], prefix: str) -> float:
    """CA facture (hors annulees) dont created_at commence par `prefix`
    (ex. "2026" pour l'annee, "2026-07" pour le mois) - le format
    CURRENT_TIMESTAMP (AAAA-MM-JJ HH:MM:SS) se compare directement en
    texte, sans avoir besoin de parser la date."""
    return round(
        sum(
            float(facture.montant or 0)
            for facture in factures
            if facture.status != "cancelled" and (facture.created_at or "").startswith(prefix)
        ),
        2,
    )


def ca_facture_du_mois(factures: list[Any], today: date | None = None) -> float:
    today = today or date.today()
    return ca_facture_periode(factures, today.strftime("%Y-%m"))


def ca_facture_annuel(factures: list[Any], today: date | None = None) -> float:
    today = today or date.today()
    return ca_facture_periode(factures, today.strftime("%Y"))
