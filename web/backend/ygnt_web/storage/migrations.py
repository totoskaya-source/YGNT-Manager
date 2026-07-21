from ygnt_web.storage.connection import DatabaseConnection
from ygnt_web.storage.database import get_connection

SCHEMA_VERSION = 3

# Aucune syntaxe propre à SQLite : pas d'AUTOINCREMENT (non nécessaire, un
# simple INTEGER PRIMARY KEY suffit), pas d'idiome SQLite-only (INSERT OR
# IGNORE...) dans les statements ci-dessous. Ce schéma n'a jamais été
# déployé hors des tests automatisés : la colonne societe_id de
# refresh_tokens (nécessaire à l'isolation multi-tenant, T4) est ajoutée
# directement à sa définition plutôt que via une migration incrémentale —
# une fois un environnement partagé alimenté, tout nouveau changement de ce
# type devra passer par une nouvelle version plutôt que d'amender celle-ci.
SCHEMA_STATEMENTS = """
CREATE TABLE IF NOT EXISTS societes (
    id INTEGER PRIMARY KEY,
    nom TEXT NOT NULL,
    forme_juridique TEXT,
    siret TEXT,
    adresse TEXT,
    code_postal TEXT,
    ville TEXT,
    email_contact TEXT,
    statut TEXT NOT NULL DEFAULT 'active',
    date_creation TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS utilisateurs (
    id INTEGER PRIMARY KEY,
    societe_id INTEGER NOT NULL REFERENCES societes(id),
    nom TEXT NOT NULL,
    prenom TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    statut TEXT NOT NULL DEFAULT 'invite',
    date_creation TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS roles (
    id INTEGER PRIMARY KEY,
    societe_id INTEGER NOT NULL REFERENCES societes(id),
    nom TEXT NOT NULL,
    description TEXT,
    date_creation TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS role_permissions (
    role_id INTEGER NOT NULL REFERENCES roles(id),
    permission TEXT NOT NULL,
    PRIMARY KEY (role_id, permission)
);

CREATE TABLE IF NOT EXISTS utilisateur_roles (
    utilisateur_id INTEGER NOT NULL REFERENCES utilisateurs(id),
    role_id INTEGER NOT NULL REFERENCES roles(id),
    PRIMARY KEY (utilisateur_id, role_id)
);

-- Identifiants de connexion : distincts de la fiche Utilisateur (02_DOMAIN_MODEL
-- ne porte pas le mot de passe comme attribut métier), propriété du module
-- Authentification.
CREATE TABLE IF NOT EXISTS identifiants (
    utilisateur_id INTEGER PRIMARY KEY REFERENCES utilisateurs(id),
    mot_de_passe_hash TEXT NOT NULL,
    date_creation TEXT NOT NULL
);

-- Jetons de rafraîchissement : seule leur empreinte est stockée, jamais la
-- valeur en clair, pour qu'une fuite de la base ne permette pas de les
-- rejouer. societe_id est dénormalisé ici (dupliqué depuis l'Utilisateur au
-- moment de l'émission) pour que le rafraîchissement d'un jeton n'ait
-- jamais besoin d'une lecture non filtrée par Société de la table
-- utilisateurs (T4, isolation multi-tenant).
CREATE TABLE IF NOT EXISTS refresh_tokens (
    id INTEGER PRIMARY KEY,
    utilisateur_id INTEGER NOT NULL REFERENCES utilisateurs(id),
    societe_id INTEGER NOT NULL REFERENCES societes(id),
    token_hash TEXT NOT NULL UNIQUE,
    date_creation TEXT NOT NULL,
    date_expiration TEXT NOT NULL,
    revoque_le TEXT
);

-- Prestation (02_DOMAIN_MODEL.md §3.8) : entité centrale du Cœur métier.
-- Organisateur et Formation n'existent pas encore comme modules (sprints
-- ultérieurs) : leurs colonnes de rattachement ne sont donc pas créées ici
-- plutôt que de référencer des tables inexistantes — ajout additif prévu
-- quand ces modules seront construits, conformément à 02_DOMAIN_MODEL.md
-- (« Organisateur et Formation ne sont pas obligatoires à la création »).
-- supprime_le porte la suppression logique (jamais physique) : distincte du
-- statut Annulee, qui reste une valeur métier du cycle de vie.
CREATE TABLE IF NOT EXISTS prestations (
    id INTEGER PRIMARY KEY,
    societe_id INTEGER NOT NULL REFERENCES societes(id),
    reference TEXT NOT NULL,
    type_evenement TEXT NOT NULL,
    nom TEXT NOT NULL,
    statut TEXT NOT NULL DEFAULT 'prospection',
    date_debut TEXT NOT NULL,
    date_fin TEXT,
    lieu_nom TEXT,
    lieu_adresse TEXT,
    lieu_code_postal TEXT,
    lieu_ville TEXT,
    notes TEXT,
    date_creation TEXT NOT NULL,
    supprime_le TEXT,
    UNIQUE (societe_id, reference)
);

CREATE INDEX IF NOT EXISTS idx_prestations_societe ON prestations(societe_id);
"""


def apply_schema(connection: DatabaseConnection) -> None:
    connection.executescript(SCHEMA_STATEMENTS)


def migrate() -> None:
    with get_connection() as connection:
        connection.execute(
            "CREATE TABLE IF NOT EXISTS schema_version (version INTEGER NOT NULL)"
        )
        row = connection.execute("SELECT version FROM schema_version").fetchone()
        version = row["version"] if row else 0
        if row is None:
            connection.execute("INSERT INTO schema_version(version) VALUES (0)")

        if version < SCHEMA_VERSION:
            apply_schema(connection)
            connection.execute(
                "UPDATE schema_version SET version = ?", (SCHEMA_VERSION,)
            )


if __name__ == "__main__":
    migrate()
