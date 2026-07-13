"""Calculs statistiques partages entre le Dashboard et la page Statistiques.

Toutes les fonctions sont pures : elles ne font aucune requete, elles operent
uniquement sur des listes deja recuperees aupres des Services existants (une
seule fois par module, cote appelant). Objectif : le Dashboard et les
Statistiques ne recalculent jamais deux fois la meme information (cf.
Sprint 12.2).

Volontairement independant de PySide6 : ce module reste dans la couche
Services (aucune dependance a l'interface), reutilisable par n'importe quelle
page.
"""

from __future__ import annotations

from datetime import date, datetime
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
    """Montant facture non encore encaisse (peut etre negatif en cas de
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
