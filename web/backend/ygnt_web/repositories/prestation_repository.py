from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from ygnt_web.domain.prestation import Prestation, PrestationStatut, TypeEvenement
from ygnt_web.storage.connection import DatabaseConnection

# Whitelist stricte : les noms de colonnes ne proviennent jamais directement
# de l'entrée utilisateur dans la requête SQL (protection contre l'injection
# via le paramètre de tri).
COLONNES_TRI_AUTORISEES = {
    "nom": "nom",
    "reference": "reference",
    "date_debut": "date_debut",
    "statut": "statut",
    "type_evenement": "type_evenement",
    "date_creation": "date_creation",
}

TAILLE_PAGE_MAX = 100


@dataclass(frozen=True)
class PagePrestations:
    items: list[Prestation]
    total: int
    page: int
    taille_page: int


def _row_to_prestation(row: Any) -> Prestation:
    return Prestation(
        id=row["id"],
        societe_id=row["societe_id"],
        reference=row["reference"],
        type_evenement=TypeEvenement(row["type_evenement"]),
        nom=row["nom"],
        statut=PrestationStatut(row["statut"]),
        date_debut=row["date_debut"],
        date_fin=row["date_fin"],
        lieu_nom=row["lieu_nom"],
        lieu_adresse=row["lieu_adresse"],
        lieu_code_postal=row["lieu_code_postal"],
        lieu_ville=row["lieu_ville"],
        notes=row["notes"],
        date_creation=datetime.fromisoformat(row["date_creation"]),
        supprime_le=datetime.fromisoformat(row["supprime_le"]) if row["supprime_le"] else None,
    )


class PrestationRepository:
    def __init__(self, connection: DatabaseConnection):
        self._connection = connection

    def ajouter(
        self,
        societe_id: int,
        reference: str,
        type_evenement: TypeEvenement,
        nom: str,
        statut: PrestationStatut,
        date_debut: str,
        date_fin: str | None = None,
        lieu_nom: str | None = None,
        lieu_adresse: str | None = None,
        lieu_code_postal: str | None = None,
        lieu_ville: str | None = None,
        notes: str | None = None,
    ) -> Prestation:
        date_creation = datetime.now(timezone.utc)
        cursor = self._connection.execute(
            """
            INSERT INTO prestations (
                societe_id, reference, type_evenement, nom, statut, date_debut,
                date_fin, lieu_nom, lieu_adresse, lieu_code_postal, lieu_ville,
                notes, date_creation
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                societe_id,
                reference,
                type_evenement.value,
                nom,
                statut.value,
                date_debut,
                date_fin,
                lieu_nom,
                lieu_adresse,
                lieu_code_postal,
                lieu_ville,
                notes,
                date_creation.isoformat(),
            ),
        )
        return self.obtenir(societe_id, cursor.lastrowid)

    def obtenir(self, societe_id: int, prestation_id: int) -> Prestation | None:
        """Toujours filtré par Société et jamais une Prestation déjà
        supprimée logiquement : garantie identique aux autres Repositories
        (isolation multi-tenant, T4)."""
        row = self._connection.execute(
            """
            SELECT * FROM prestations
            WHERE id = ? AND societe_id = ? AND supprime_le IS NULL
            """,
            (prestation_id, societe_id),
        ).fetchone()
        return _row_to_prestation(row) if row else None

    def modifier(self, societe_id: int, prestation_id: int, **champs) -> Prestation | None:
        if not champs:
            return self.obtenir(societe_id, prestation_id)

        colonnes = ", ".join(f"{cle} = ?" for cle in champs)
        valeurs = [
            valeur.value if isinstance(valeur, (TypeEvenement, PrestationStatut)) else valeur
            for valeur in champs.values()
        ]
        cursor = self._connection.execute(
            f"""
            UPDATE prestations SET {colonnes}
            WHERE id = ? AND societe_id = ? AND supprime_le IS NULL
            """,
            (*valeurs, prestation_id, societe_id),
        )
        if cursor.rowcount == 0:
            return None
        return self.obtenir(societe_id, prestation_id)

    def supprimer(self, societe_id: int, prestation_id: int) -> bool:
        """Suppression logique (02_DOMAIN_MODEL §5 règle 7) : jamais un
        DELETE SQL."""
        cursor = self._connection.execute(
            """
            UPDATE prestations SET supprime_le = ?
            WHERE id = ? AND societe_id = ? AND supprime_le IS NULL
            """,
            (datetime.now(timezone.utc).isoformat(), prestation_id, societe_id),
        )
        return cursor.rowcount > 0

    def lister(
        self,
        societe_id: int,
        page: int = 1,
        taille_page: int = 20,
        recherche: str | None = None,
        statut: PrestationStatut | None = None,
        type_evenement: TypeEvenement | None = None,
        tri: str = "date_debut",
        ordre: str = "desc",
    ) -> PagePrestations:
        conditions = ["societe_id = ?", "supprime_le IS NULL"]
        parametres: list = [societe_id]

        if recherche:
            motif = f"%{recherche}%"
            conditions.append("(nom LIKE ? OR reference LIKE ? OR lieu_ville LIKE ?)")
            parametres.extend([motif, motif, motif])
        if statut is not None:
            conditions.append("statut = ?")
            parametres.append(statut.value)
        if type_evenement is not None:
            conditions.append("type_evenement = ?")
            parametres.append(type_evenement.value)

        where_clause = " AND ".join(conditions)

        total = self._connection.execute(
            f"SELECT COUNT(*) AS total FROM prestations WHERE {where_clause}",
            parametres,
        ).fetchone()["total"]

        colonne_tri = COLONNES_TRI_AUTORISEES.get(tri, "date_debut")
        direction = "ASC" if str(ordre).lower() == "asc" else "DESC"
        page = max(1, page)
        taille_page = max(1, min(taille_page, TAILLE_PAGE_MAX))
        decalage = (page - 1) * taille_page

        rows = self._connection.execute(
            f"""
            SELECT * FROM prestations
            WHERE {where_clause}
            ORDER BY {colonne_tri} {direction}, id {direction}
            LIMIT ? OFFSET ?
            """,
            (*parametres, taille_page, decalage),
        ).fetchall()

        return PagePrestations(
            items=[_row_to_prestation(row) for row in rows],
            total=total,
            page=page,
            taille_page=taille_page,
        )

    def prochaine_sequence(self, societe_id: int, annee: str) -> int:
        """Se base sur la dernière référence attribuée pour l'année en cours
        au sein de la Société (jamais un comptage total), pour rester
        correcte après suppression logique (05_DATABASE §2.8)."""
        prefixe = f"PREST-{annee}-"
        rows = self._connection.execute(
            "SELECT reference FROM prestations WHERE societe_id = ? AND reference LIKE ?",
            (societe_id, f"{prefixe}%"),
        ).fetchall()

        sequence_max = 0
        for row in rows:
            suffixe = row["reference"][len(prefixe):]
            if suffixe.isdigit():
                sequence_max = max(sequence_max, int(suffixe))
        return sequence_max + 1
