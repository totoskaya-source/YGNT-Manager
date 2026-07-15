from .database import Database


SCHEMA_VERSION = 1


class MigrationManager:

    def __init__(self):
        self.db = Database.instance()

    def migrate(self):
        self._create_schema_version()
        version = self._current_version()

        if version < 1:
            self._migration_v1()
        else:
            self._ensure_v1_schema()

    def _create_schema_version(self):
        self.db.execute("""
        CREATE TABLE IF NOT EXISTS schema_version(
            version INTEGER NOT NULL
        )
        """)

        row = self.db.fetchone(
            "SELECT version FROM schema_version LIMIT 1"
        )

        if row is None:
            self.db.execute(
                "INSERT INTO schema_version(version) VALUES(0)"
            )

    def _current_version(self):
        row = self.db.fetchone(
            "SELECT version FROM schema_version LIMIT 1"
        )
        return row["version"] if row else 0

    def _set_version(self, version):
        self.db.execute(
            "UPDATE schema_version SET version=?",
            (version,)
        )

    def _migration_v1(self):
        self._ensure_v1_schema()
        self._set_version(1)

    def _ensure_v1_schema(self):

        self.db.execute("""
        CREATE TABLE IF NOT EXISTS artists(

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            stage_name TEXT NOT NULL,

            legal_name TEXT,

            address TEXT,

            postal_code TEXT,

            city TEXT,

            email TEXT,

            phone TEXT,

            instrument TEXT,

            status TEXT,

            fee REAL DEFAULT 0,

            birth_date TEXT,

            social_number TEXT,

            siren TEXT,

            siret TEXT,

            ape TEXT,

            licence TEXT,

            iban TEXT,

            bic TEXT,

            notes TEXT,

            created_at TEXT DEFAULT CURRENT_TIMESTAMP,

            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """)

        self._ensure_columns("artists", {
            "instrument": "TEXT",
            "status": "TEXT",
            "fee": "REAL DEFAULT 0",
            "updated_at": "TEXT",
            "style_musical": "TEXT",
            "description": "TEXT",
            "logo_path": "TEXT",
            "photo_path": "TEXT",
            "site_internet": "TEXT",
            "facebook": "TEXT",
            "instagram": "TEXT",
            "youtube": "TEXT",
            "birth_place": "TEXT",
            "conges_spectacle_number": "TEXT",
            "first_name": "TEXT",
            "secondary_instruments": "TEXT",
            "comments": "TEXT",
            "qualification": "TEXT",
        })

        self.db.execute("""
        CREATE TABLE IF NOT EXISTS organizations(

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            name TEXT NOT NULL,

            legal_form TEXT,

            address TEXT,

            postal_code TEXT,

            city TEXT,

            siret TEXT,

            ape TEXT,

            licence TEXT,

            email TEXT,

            phone TEXT,

            iban TEXT,

            bic TEXT,

            president TEXT,

            notes TEXT,

            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """)

        self._ensure_columns("organizations", {
            "tva": "TEXT",
            "fonction": "TEXT",
            "site_internet": "TEXT",
        })

        self.db.execute("""
        CREATE TABLE IF NOT EXISTS contracts(

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            contract_number TEXT,

            artist_id INTEGER,

            organization_id INTEGER,

            prestation_id INTEGER,

            event_name TEXT,

            venue TEXT,

            event_date TEXT,

            start_time TEXT,

            end_time TEXT,

            gross_salary REAL,

            employer_cost REAL,

            travel_cost REAL,

            accommodation_cost REAL,

            catering_cost REAL,

            comments TEXT,

            docx_path TEXT,

            pdf_path TEXT,

            status TEXT DEFAULT 'draft',

            created_at TEXT DEFAULT CURRENT_TIMESTAMP,

            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,

            generated_at TEXT,

            organisateur_structure TEXT,

            organisateur_forme TEXT,

            organisateur_adresse TEXT,

            organisateur_postal_code TEXT,

            organisateur_city TEXT,

            organisateur_siret TEXT,

            organisateur_phone TEXT,

            organisateur_email TEXT,

            organisateur_ape TEXT,

            organisateur_licence TEXT,

            organisateur_tva TEXT,

            organisateur_representant TEXT,

            organisateur_fonction TEXT,

            spectacle_nom TEXT,

            spectacle_duree TEXT,

            prestation_date TEXT,

            prestation_adresse TEXT,

            prestation_convocation TEXT,

            prestation_horaire TEXT,

            cession_montant REAL DEFAULT 0,

            mode_paiement TEXT,

            hebergement INTEGER DEFAULT 0,

            restauration INTEGER DEFAULT 0,

            kilometrage INTEGER DEFAULT 0,

            FOREIGN KEY(artist_id)
                REFERENCES artists(id)
                ON DELETE CASCADE,

            FOREIGN KEY(organization_id)
                REFERENCES organizations(id)
                ON DELETE CASCADE,

            FOREIGN KEY(prestation_id)
                REFERENCES prestations(id)
                ON DELETE SET NULL
        )
        """)

        self.db.execute("""
        CREATE TABLE IF NOT EXISTS contract_templates(

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            name TEXT NOT NULL,

            path TEXT NOT NULL
        )
        """)

        self.db.execute("""
        CREATE TABLE IF NOT EXISTS settings(

            key TEXT PRIMARY KEY,

            value TEXT
        )
        """)

        self._ensure_columns("contracts", {
            "prestation_id": "INTEGER",
            "updated_at": "TEXT",
            "generated_at": "TEXT",
            "producteur_id": "INTEGER",
            "producteur_nom": "TEXT",
            "producteur_forme_juridique": "TEXT",
            "producteur_adresse": "TEXT",
            "producteur_code_postal": "TEXT",
            "producteur_ville": "TEXT",
            "producteur_siret": "TEXT",
            "producteur_ape": "TEXT",
            "producteur_licence": "TEXT",
            "producteur_tva_intracommunautaire": "TEXT",
            "producteur_telephone": "TEXT",
            "producteur_email": "TEXT",
            "producteur_site": "TEXT",
            "producteur_representant": "TEXT",
            "producteur_fonction": "TEXT",
            "producteur_iban": "TEXT",
            "producteur_bic": "TEXT",
            "organisateur_structure": "TEXT",
            "organisateur_forme": "TEXT",
            "organisateur_adresse": "TEXT",
            "organisateur_postal_code": "TEXT",
            "organisateur_city": "TEXT",
            "organisateur_siret": "TEXT",
            "organisateur_phone": "TEXT",
            "organisateur_email": "TEXT",
            "organisateur_ape": "TEXT",
            "organisateur_licence": "TEXT",
            "organisateur_tva": "TEXT",
            "organisateur_representant": "TEXT",
            "organisateur_fonction": "TEXT",
            "organisateur_iban": "TEXT",
            "organisateur_bic": "TEXT",
            "organisateur_site_internet": "TEXT",
            "organisateur_notes": "TEXT",
            "artiste_nom": "TEXT",
            "artiste_adresse": "TEXT",
            "artiste_postal_code": "TEXT",
            "artiste_city": "TEXT",
            "artiste_phone": "TEXT",
            "artiste_email": "TEXT",
            "artiste_siren": "TEXT",
            "artiste_siret": "TEXT",
            "artiste_ape": "TEXT",
            "artiste_licence": "TEXT",
            "artiste_iban": "TEXT",
            "artiste_bic": "TEXT",
            "artiste_social_number": "TEXT",
            "artiste_notes": "TEXT",
            "spectacle_nom": "TEXT",
            "spectacle_duree": "TEXT",
            "prestation_date": "TEXT",
            "prestation_lieu": "TEXT",
            "prestation_adresse": "TEXT",
            "prestation_postal_code": "TEXT",
            "prestation_city": "TEXT",
            "prestation_convocation": "TEXT",
            "prestation_horaire": "TEXT",
            "cession_montant": "REAL DEFAULT 0",
            "acompte": "REAL DEFAULT 0",
            "cachet_tva": "TEXT",
            "echeance": "TEXT",
            "observations": "TEXT",
            "mode_paiement": "TEXT",
            "hebergement": "INTEGER DEFAULT 0",
            "restauration": "INTEGER DEFAULT 0",
            "kilometrage": "INTEGER DEFAULT 0",
            "formation_id": "INTEGER",
        })

        self.db.execute("""
        CREATE TABLE IF NOT EXISTS contract_history(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            contract_id INTEGER NOT NULL,
            action TEXT NOT NULL,
            details TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(contract_id)
                REFERENCES contracts(id)
                ON DELETE CASCADE
        )
        """)

        self.db.execute("""
        CREATE TABLE IF NOT EXISTS prestations(

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            reference TEXT UNIQUE NOT NULL,

            type_evenement TEXT,

            nom TEXT NOT NULL,

            statut TEXT DEFAULT 'prospection',

            date_debut TEXT NOT NULL,

            date_fin TEXT,

            artist_id INTEGER,

            organization_id INTEGER,

            lieu_nom TEXT,

            lieu_adresse TEXT,

            lieu_postal_code TEXT,

            lieu_city TEXT,

            notes TEXT,

            created_at TEXT DEFAULT CURRENT_TIMESTAMP,

            updated_at TEXT,

            FOREIGN KEY(artist_id)
                REFERENCES artists(id)
                ON DELETE SET NULL,

            FOREIGN KEY(organization_id)
                REFERENCES organizations(id)
                ON DELETE SET NULL
        )
        """)

        self._ensure_columns("prestations", {
            "updated_at": "TEXT",
            "formation_id": "INTEGER",
        })

        self.db.execute("""
        CREATE TABLE IF NOT EXISTS formations(

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            nom TEXT NOT NULL,

            logo_path TEXT,

            photo_path TEXT,

            description TEXT,

            style TEXT,

            created_at TEXT DEFAULT CURRENT_TIMESTAMP,

            updated_at TEXT
        )
        """)

        self._ensure_columns("formations", {
            "address": "TEXT",
            "postal_code": "TEXT",
            "city": "TEXT",
            "phone": "TEXT",
            "email": "TEXT",
            "siret": "TEXT",
            "ape": "TEXT",
            "licence": "TEXT",
            "iban": "TEXT",
            "bic": "TEXT",
        })

        self.db.execute("""
        CREATE TABLE IF NOT EXISTS formation_artistes(

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            formation_id INTEGER NOT NULL,

            artiste_id INTEGER NOT NULL,

            role TEXT,

            ordre INTEGER,

            created_at TEXT DEFAULT CURRENT_TIMESTAMP,

            updated_at TEXT,

            UNIQUE(formation_id, artiste_id),

            FOREIGN KEY(formation_id)
                REFERENCES formations(id)
                ON DELETE CASCADE,

            FOREIGN KEY(artiste_id)
                REFERENCES artists(id)
                ON DELETE CASCADE
        )
        """)

        self.db.execute("""
        CREATE TABLE IF NOT EXISTS producteurs(

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            nom TEXT NOT NULL,

            forme_juridique TEXT,

            adresse TEXT,

            postal_code TEXT,

            city TEXT,

            siret TEXT,

            ape TEXT,

            licence TEXT,

            tva TEXT,

            iban TEXT,

            bic TEXT,

            representant TEXT,

            fonction TEXT,

            logo_path TEXT,

            site_internet TEXT,

            email TEXT,

            phone TEXT,

            notes TEXT,

            actif INTEGER DEFAULT 0,

            created_at TEXT DEFAULT CURRENT_TIMESTAMP,

            updated_at TEXT
        )
        """)

        self._ensure_columns("producteurs", {
            "convention_collective": "TEXT",
        })

        self.db.execute("""
        CREATE TABLE IF NOT EXISTS devis(

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            devis_number TEXT,

            formation_id INTEGER,

            organization_id INTEGER,

            prestation_id INTEGER,

            producteur_id INTEGER,

            producteur_nom TEXT,
            producteur_forme_juridique TEXT,
            producteur_adresse TEXT,
            producteur_code_postal TEXT,
            producteur_ville TEXT,
            producteur_siret TEXT,
            producteur_ape TEXT,
            producteur_licence TEXT,
            producteur_tva_intracommunautaire TEXT,
            producteur_telephone TEXT,
            producteur_email TEXT,
            producteur_site TEXT,
            producteur_representant TEXT,
            producteur_fonction TEXT,
            producteur_iban TEXT,
            producteur_bic TEXT,

            organisateur_structure TEXT,
            organisateur_forme TEXT,
            organisateur_adresse TEXT,
            organisateur_postal_code TEXT,
            organisateur_city TEXT,
            organisateur_siret TEXT,
            organisateur_phone TEXT,
            organisateur_email TEXT,
            organisateur_ape TEXT,
            organisateur_licence TEXT,
            organisateur_tva TEXT,
            organisateur_representant TEXT,
            organisateur_fonction TEXT,
            organisateur_iban TEXT,
            organisateur_bic TEXT,
            organisateur_site_internet TEXT,
            organisateur_notes TEXT,

            formation_nom TEXT,
            formation_adresse TEXT,
            formation_postal_code TEXT,
            formation_city TEXT,
            formation_phone TEXT,
            formation_email TEXT,
            formation_site_internet TEXT,
            formation_siren TEXT,
            formation_siret TEXT,
            formation_ape TEXT,
            formation_licence TEXT,
            formation_iban TEXT,
            formation_bic TEXT,
            formation_social_number TEXT,
            formation_notes TEXT,

            spectacle_nom TEXT,
            spectacle_duree TEXT,

            prestation_date TEXT,
            prestation_lieu TEXT,
            prestation_adresse TEXT,
            prestation_postal_code TEXT,
            prestation_city TEXT,
            prestation_convocation TEXT,
            prestation_horaire TEXT,

            montant REAL DEFAULT 0,
            acompte REAL DEFAULT 0,
            tva TEXT,
            mode_paiement TEXT,
            echeance TEXT,
            date_validite TEXT,
            observations TEXT,
            comments TEXT,

            hebergement INTEGER DEFAULT 0,
            restauration INTEGER DEFAULT 0,
            kilometrage INTEGER DEFAULT 0,

            docx_path TEXT,
            pdf_path TEXT,

            status TEXT DEFAULT 'draft',

            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT,
            generated_at TEXT,

            FOREIGN KEY(formation_id)
                REFERENCES artists(id)
                ON DELETE SET NULL,

            FOREIGN KEY(organization_id)
                REFERENCES organizations(id)
                ON DELETE SET NULL,

            FOREIGN KEY(prestation_id)
                REFERENCES prestations(id)
                ON DELETE SET NULL,

            FOREIGN KEY(producteur_id)
                REFERENCES producteurs(id)
                ON DELETE SET NULL
        )
        """)

        self._ensure_columns("devis", {
            "formation_site_internet": "TEXT",
            "producteur_logo_path": "TEXT",
        })

        self.db.execute("""
        CREATE TABLE IF NOT EXISTS factures(

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            facture_number TEXT,

            prestation_id INTEGER,

            contract_id INTEGER,

            producteur_id INTEGER,

            formation_id INTEGER,

            organization_id INTEGER,

            producteur_nom TEXT,
            producteur_forme_juridique TEXT,
            producteur_adresse TEXT,
            producteur_code_postal TEXT,
            producteur_ville TEXT,
            producteur_siret TEXT,
            producteur_ape TEXT,
            producteur_licence TEXT,
            producteur_tva_intracommunautaire TEXT,
            producteur_telephone TEXT,
            producteur_email TEXT,
            producteur_site TEXT,
            producteur_representant TEXT,
            producteur_fonction TEXT,
            producteur_iban TEXT,
            producteur_bic TEXT,
            producteur_logo_path TEXT,

            organisateur_structure TEXT,
            organisateur_forme TEXT,
            organisateur_adresse TEXT,
            organisateur_postal_code TEXT,
            organisateur_city TEXT,
            organisateur_siret TEXT,
            organisateur_phone TEXT,
            organisateur_email TEXT,
            organisateur_ape TEXT,
            organisateur_licence TEXT,
            organisateur_tva TEXT,
            organisateur_representant TEXT,
            organisateur_fonction TEXT,
            organisateur_iban TEXT,
            organisateur_bic TEXT,
            organisateur_site_internet TEXT,
            organisateur_notes TEXT,

            formation_nom TEXT,
            formation_adresse TEXT,
            formation_postal_code TEXT,
            formation_city TEXT,
            formation_phone TEXT,
            formation_email TEXT,
            formation_site_internet TEXT,
            formation_siren TEXT,
            formation_siret TEXT,
            formation_ape TEXT,
            formation_licence TEXT,
            formation_iban TEXT,
            formation_bic TEXT,
            formation_social_number TEXT,
            formation_notes TEXT,

            spectacle_nom TEXT,
            spectacle_duree TEXT,

            prestation_date TEXT,
            prestation_lieu TEXT,
            prestation_adresse TEXT,
            prestation_postal_code TEXT,
            prestation_city TEXT,
            prestation_convocation TEXT,
            prestation_horaire TEXT,

            montant REAL DEFAULT 0,
            tva TEXT,
            acompte REAL DEFAULT 0,
            total REAL DEFAULT 0,
            mode_paiement TEXT,
            echeance TEXT,
            observations TEXT,
            comments TEXT,

            docx_path TEXT,
            pdf_path TEXT,

            status TEXT DEFAULT 'pending',

            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT,
            generated_at TEXT,

            FOREIGN KEY(prestation_id)
                REFERENCES prestations(id)
                ON DELETE SET NULL,

            FOREIGN KEY(contract_id)
                REFERENCES contracts(id)
                ON DELETE SET NULL,

            FOREIGN KEY(producteur_id)
                REFERENCES producteurs(id)
                ON DELETE SET NULL,

            FOREIGN KEY(organization_id)
                REFERENCES organizations(id)
                ON DELETE SET NULL
        )
        """)

        self.db.execute("""
        CREATE TABLE IF NOT EXISTS paiements(

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            reference TEXT,

            facture_id INTEGER NOT NULL,

            date_paiement TEXT,

            montant REAL DEFAULT 0,

            mode_paiement TEXT,

            reference_bancaire TEXT,

            observations TEXT,

            status TEXT DEFAULT 'pending',

            created_at TEXT DEFAULT CURRENT_TIMESTAMP,

            updated_at TEXT,

            FOREIGN KEY(facture_id)
                REFERENCES factures(id)
                ON DELETE CASCADE
        )
        """)

        self.db.execute("""
        CREATE TABLE IF NOT EXISTS contrats_cddu(

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            numero TEXT UNIQUE,

            prestation_id INTEGER,

            artist_id INTEGER,

            producteur_id INTEGER,

            producteur_nom TEXT,
            producteur_forme_juridique TEXT,
            producteur_adresse TEXT,
            producteur_postal_code TEXT,
            producteur_city TEXT,
            producteur_siret TEXT,
            producteur_ape TEXT,
            producteur_licence TEXT,
            producteur_convention_collective TEXT,
            producteur_representant TEXT,
            producteur_fonction TEXT,
            producteur_email TEXT,
            producteur_phone TEXT,

            artiste_nom TEXT,
            artiste_adresse TEXT,
            artiste_postal_code TEXT,
            artiste_city TEXT,
            artiste_phone TEXT,
            artiste_email TEXT,
            artiste_date_naissance TEXT,
            artiste_lieu_naissance TEXT,
            artiste_numero_secu TEXT,
            artiste_numero_conges_spectacle TEXT,
            artiste_fonction TEXT,

            prestation_reference TEXT,
            prestation_objet TEXT,
            prestation_lieu TEXT,
            prestation_ville TEXT,

            numero_objet TEXT DEFAULT '',

            remuneration_brute REAL DEFAULT 0,

            defraiement_deplacement REAL,
            defraiement_hebergement REAL,
            defraiement_repas REAL,
            defraiement_autres_libelle TEXT,
            defraiement_autres_montant REAL,
            defraiement_montant_libre_libelle TEXT,
            defraiement_montant_libre_montant REAL,

            observations TEXT,

            docx_path TEXT,
            pdf_path TEXT,

            status TEXT DEFAULT 'draft',

            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT,
            generated_at TEXT,

            FOREIGN KEY(prestation_id)
                REFERENCES prestations(id)
                ON DELETE SET NULL,

            FOREIGN KEY(artist_id)
                REFERENCES artists(id)
                ON DELETE SET NULL,

            FOREIGN KEY(producteur_id)
                REFERENCES producteurs(id)
                ON DELETE SET NULL
        )
        """)

        self._ensure_columns("contrats_cddu", {
            "ville_signature": "TEXT",
            "date_signature": "TEXT",
            "artiste_prenom": "TEXT",
            "artiste_qualification": "TEXT",
        })

        self.db.execute("""
        CREATE TABLE IF NOT EXISTS contrat_cddu_dates(

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            contrat_cddu_id INTEGER NOT NULL,

            prestation_id INTEGER,

            date_travaillee TEXT NOT NULL,

            nombre_cachets INTEGER DEFAULT 1,

            FOREIGN KEY(contrat_cddu_id)
                REFERENCES contrats_cddu(id)
                ON DELETE CASCADE,

            FOREIGN KEY(prestation_id)
                REFERENCES prestations(id)
                ON DELETE SET NULL
        )
        """)

        self.db.execute("""
        CREATE TABLE IF NOT EXISTS prestation_participants(

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            prestation_id INTEGER NOT NULL,

            artiste_id INTEGER NOT NULL,

            role TEXT,

            ordre INTEGER,

            created_at TEXT DEFAULT CURRENT_TIMESTAMP,

            updated_at TEXT,

            UNIQUE(prestation_id, artiste_id),

            FOREIGN KEY(prestation_id)
                REFERENCES prestations(id)
                ON DELETE CASCADE,

            FOREIGN KEY(artiste_id)
                REFERENCES artists(id)
                ON DELETE CASCADE
        )
        """)

        self.db.execute("""
        CREATE TABLE IF NOT EXISTS contrat_cddu_history(

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            contrat_cddu_id INTEGER NOT NULL,

            action TEXT NOT NULL,

            details TEXT,

            created_at TEXT DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY(contrat_cddu_id)
                REFERENCES contrats_cddu(id)
                ON DELETE CASCADE
        )
        """)

        self._fix_factures_formation_fk()

    def _fix_factures_formation_fk(self):
        """Corrige une contrainte de cle etrangere devenue incorrecte sur
        factures.formation_id : a l'origine (avant l'entite Formation),
        formation_id designait toujours un artiste, d'ou
        `REFERENCES artists(id)`. Depuis que FactureService.build_from_prestation()
        y ecrit un vrai formations.id quand la prestation utilise la nouvelle
        entite Formation (bugfix facture-depuis-prestation), cette contrainte
        rejette l'insertion (sqlite3.IntegrityError). formation_id est
        desormais polymorphe (artiste OU formation) : aucune contrainte FK
        unique ne peut valider les deux, exactement comme
        contracts.formation_id et prestations.formation_id qui n'en ont
        jamais porte. Idempotent : ne reconstruit la table que si l'ancienne
        contrainte est encore presente ; ne touche a aucune autre table, ne
        perd aucune ligne ni aucune colonne."""
        foreign_keys = self.db.fetchall("PRAGMA foreign_key_list(factures)")
        has_bad_fk = any(
            fk["table"] == "artists" and fk["from"] == "formation_id"
            for fk in foreign_keys
        )
        if not has_bad_fk:
            return

        self.db.execute("ALTER TABLE factures RENAME TO factures_pre_formation_fk_fix")

        self.db.execute("""
        CREATE TABLE factures(

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            facture_number TEXT,

            prestation_id INTEGER,

            contract_id INTEGER,

            producteur_id INTEGER,

            formation_id INTEGER,

            organization_id INTEGER,

            producteur_nom TEXT,
            producteur_forme_juridique TEXT,
            producteur_adresse TEXT,
            producteur_code_postal TEXT,
            producteur_ville TEXT,
            producteur_siret TEXT,
            producteur_ape TEXT,
            producteur_licence TEXT,
            producteur_tva_intracommunautaire TEXT,
            producteur_telephone TEXT,
            producteur_email TEXT,
            producteur_site TEXT,
            producteur_representant TEXT,
            producteur_fonction TEXT,
            producteur_iban TEXT,
            producteur_bic TEXT,
            producteur_logo_path TEXT,

            organisateur_structure TEXT,
            organisateur_forme TEXT,
            organisateur_adresse TEXT,
            organisateur_postal_code TEXT,
            organisateur_city TEXT,
            organisateur_siret TEXT,
            organisateur_phone TEXT,
            organisateur_email TEXT,
            organisateur_ape TEXT,
            organisateur_licence TEXT,
            organisateur_tva TEXT,
            organisateur_representant TEXT,
            organisateur_fonction TEXT,
            organisateur_iban TEXT,
            organisateur_bic TEXT,
            organisateur_site_internet TEXT,
            organisateur_notes TEXT,

            formation_nom TEXT,
            formation_adresse TEXT,
            formation_postal_code TEXT,
            formation_city TEXT,
            formation_phone TEXT,
            formation_email TEXT,
            formation_site_internet TEXT,
            formation_siren TEXT,
            formation_siret TEXT,
            formation_ape TEXT,
            formation_licence TEXT,
            formation_iban TEXT,
            formation_bic TEXT,
            formation_social_number TEXT,
            formation_notes TEXT,

            spectacle_nom TEXT,
            spectacle_duree TEXT,

            prestation_date TEXT,
            prestation_lieu TEXT,
            prestation_adresse TEXT,
            prestation_postal_code TEXT,
            prestation_city TEXT,
            prestation_convocation TEXT,
            prestation_horaire TEXT,

            montant REAL DEFAULT 0,
            tva TEXT,
            acompte REAL DEFAULT 0,
            total REAL DEFAULT 0,
            mode_paiement TEXT,
            echeance TEXT,
            observations TEXT,
            comments TEXT,

            docx_path TEXT,
            pdf_path TEXT,

            status TEXT DEFAULT 'pending',

            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT,
            generated_at TEXT,

            FOREIGN KEY(prestation_id)
                REFERENCES prestations(id)
                ON DELETE SET NULL,

            FOREIGN KEY(contract_id)
                REFERENCES contracts(id)
                ON DELETE SET NULL,

            FOREIGN KEY(producteur_id)
                REFERENCES producteurs(id)
                ON DELETE SET NULL,

            FOREIGN KEY(organization_id)
                REFERENCES organizations(id)
                ON DELETE SET NULL
        )
        """)

        columns = ", ".join(
            row["name"] for row in self.db.fetchall("PRAGMA table_info(factures_pre_formation_fk_fix)")
        )
        self.db.execute(
            f"INSERT INTO factures ({columns}) SELECT {columns} FROM factures_pre_formation_fk_fix"
        )

        # ATTENTION (lecon retenue) : `ALTER TABLE factures RENAME TO ...`
        # reecrit silencieusement les references FK des AUTRES tables (ici
        # paiements.facture_id) pour qu'elles pointent vers le nouveau nom.
        # `DROP TABLE` sur une table encore referencee par une contrainte
        # `ON DELETE CASCADE` declenche cette cascade et supprime les lignes
        # dependantes - meme un simple DROP, sans aucun DELETE explicite.
        # paiements doit donc etre re-alignee sur `factures` AVANT de
        # supprimer factures_pre_formation_fk_fix, sous peine de perdre tous
        # les paiements enregistres.
        dependents = [
            row["name"]
            for row in self.db.fetchall("SELECT name FROM sqlite_master WHERE type='table'")
            if row["name"] not in ("factures", "factures_pre_formation_fk_fix")
            and any(
                fk["table"] == "factures_pre_formation_fk_fix"
                for fk in self.db.fetchall(f"PRAGMA foreign_key_list({row['name']})")
            )
        ]

        if dependents == ["paiements"]:
            self.db.execute("ALTER TABLE paiements RENAME TO paiements_pre_formation_fk_fix")

            self.db.execute("""
            CREATE TABLE paiements(

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                reference TEXT,

                facture_id INTEGER NOT NULL,

                date_paiement TEXT,

                montant REAL DEFAULT 0,

                mode_paiement TEXT,

                reference_bancaire TEXT,

                observations TEXT,

                status TEXT DEFAULT 'pending',

                created_at TEXT DEFAULT CURRENT_TIMESTAMP,

                updated_at TEXT,

                FOREIGN KEY(facture_id)
                    REFERENCES factures(id)
                    ON DELETE CASCADE
            )
            """)

            paiement_columns = ", ".join(
                row["name"] for row in self.db.fetchall("PRAGMA table_info(paiements_pre_formation_fk_fix)")
            )
            self.db.execute(
                f"INSERT INTO paiements ({paiement_columns}) "
                f"SELECT {paiement_columns} FROM paiements_pre_formation_fk_fix"
            )

            self.db.execute("DROP TABLE paiements_pre_formation_fk_fix")
        elif dependents:
            # Aucune autre table ne devrait dependre de factures dans ce
            # schema (verifie) : si une table inattendue apparaissait, on
            # arrete ici plutot que de risquer une perte de donnees
            # silencieuse via CASCADE au DROP TABLE suivant.
            raise RuntimeError(
                "Migration factures.formation_id : tables dependantes inattendues "
                f"{dependents} - correction manuelle requise avant de continuer."
            )

        self.db.execute("DROP TABLE factures_pre_formation_fk_fix")

    def _ensure_columns(self, table, columns):
        existing = {
            row["name"]
            for row in self.db.fetchall(f"PRAGMA table_info({table})")
        }

        for name, definition in columns.items():
            if name not in existing:
                self.db.execute(
                    f"ALTER TABLE {table} ADD COLUMN {name} {definition}"
                )
        
