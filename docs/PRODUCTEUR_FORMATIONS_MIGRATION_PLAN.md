# YGNT Manager — Plan officiel de migration vers Producteur / Formations

Feuille de route officielle du projet. Document de planification uniquement :
aucun code, aucune base, aucun commit ne sont réalisés ici. Il exécute, sprint
par sprint, l'architecture décrite dans `PRODUCTEUR_FORMATIONS_ARCHITECTURE.md`,
en complément de `PROJECT.md`, `CODING_RULES.md`, `BUSINESS_RULES.md`,
`ROADMAP.md` et `PRESTATIONS_ARCHITECTURE.md`.

Chaque étape ci-dessous est **indépendante** et **livrable seule**, dans
l'esprit déjà appliqué depuis le Sprint 8.1 : migrations additives et
rétrocompatibles, jamais de suppression de colonne, jamais de régression sur
les contrats/DOCX/PDF existants, application testée et démarrée sans erreur à
la fin de chaque sprint.

---

## Architecture cible

```
🏢 Producteur
      ↓
🎵 Formation  ──→  👤 Membres (gestion interne uniquement)
      ↓
🏛 Organisateur
      ↓
🎪 Prestation
      ↓
📄 Devis
      ↓
📃 Contrat
      ↓
🧾 Facture
      ↓
💳 Paiement
```

- **Producteur** et **Organisateur** sont les deux parties juridiques de tout
  document commercial.
- **Formation** est l'entité artistique engagée — jamais signataire.
- **Membres** ne sortent jamais du périmètre de gestion interne de leur
  Formation.
- **Prestation** reste le pivot : Devis, Contrat, Facture et Paiement s'y
  rattachent tous (`prestation_id`), conformément à `PRESTATIONS_ARCHITECTURE.md`.

---

## 1. Étapes de migration (vue d'ensemble)

| Sprint | Objectif |
|---|---|
| 8.5 | Producteur (fondations, plusieurs producteurs possibles, un seul actif) |
| 8.6 | Renommer Artistes → Formations |
| 8.7 | Retirer le cachet habituel de la Formation |
| 8.8 | Champs internes et marketing de la Formation |
| 8.9 | Module Membres |
| 8.10 | Producteur dans les Prestations |
| 8.11 | Producteur dans les Contrats (+ template DOCX) |
| 9 | Devis |
| 9.x | Factures |
| 9.x | Paiements |
| 1.0 | Stabilisation et packaging |

Chaque sprint est détaillé ci-dessous avec : objectif, fichiers concernés,
migrations SQLite, impacts, risques, tests à effectuer.

---

## 2. Détail de chaque étape

### Sprint 8.5 — Producteur (fondations)

**Objectif**
Créer le Producteur comme entité réelle en base, avec la possibilité de gérer
plusieurs producteurs à terme (multi-sociétés), mais un seul actif à la fois.
Aucune interface graphique à ce stade (comme l'a été Sprint 8.1 pour les
Prestations).

**Fichiers concernés**
- `app/models/producteur.py` *(nouveau)*
- `app/repositories/producteur_repository.py` *(nouveau)*
- `app/services/producteur_service.py` *(nouveau)*
- `app/database/migrations.py` *(modifié — ajout de table uniquement)*

**Migrations SQLite**
```
CREATE TABLE IF NOT EXISTS producteurs(
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    nom              TEXT NOT NULL,
    forme_juridique  TEXT,
    adresse          TEXT,
    postal_code      TEXT,
    city             TEXT,
    siret            TEXT,
    ape              TEXT,
    licence          TEXT,
    tva              TEXT,
    iban             TEXT,
    bic              TEXT,
    representant     TEXT,
    fonction         TEXT,
    logo_path        TEXT,
    site_internet    TEXT,
    email            TEXT,
    phone            TEXT,
    notes            TEXT,
    actif            INTEGER DEFAULT 0,
    created_at       TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at       TEXT
)
```
Aucune modification d'une table existante.

**Impacts**
Aucun sur l'existant : nouvelle table isolée, aucun module ne la référence
encore.

**Risques**
Faible. Point d'attention unique : garantir qu'un seul producteur est
`actif = 1` à la fois. `ProducteurService.set_active(producteur_id)` doit
désactiver tous les autres avant d'activer celui demandé (transaction unique,
même connexion SQLite).

**Tests à effectuer**
- Création de plusieurs producteurs (ex. "YGNT Production" et une société
  secondaire fictive de test).
- Activation de l'un désactive automatiquement les autres.
- Lecture du producteur actif (`get_active()`).
- Suppression, modification, recherche.
- Démarrage complet de l'application, aucune régression sur les modules
  existants (aucun ne dépend encore du Producteur).

---

### Sprint 8.6 — Renommer Artistes → Formations

**Objectif**
Faire évoluer le vocabulaire du logiciel pour refléter la réalité métier :
« Formation » remplace « Artiste » partout où c'est pertinent, sans perdre de
données ni casser les contrats déjà liés.

**Fichiers concernés**
- `app/models/artist.py` → `app/models/formation.py`
- `app/repositories/artist_repository.py` → `app/repositories/formation_repository.py`
- `app/services/artist_service.py` → `app/services/formation_service.py`
- `app/ui/artistes.py` → `app/ui/formations.py`
- `app/ui/artist_dialog.py` → `app/ui/formation_dialog.py`
- `app/ui/main_window.py` (libellé de menu, routage)
- `app/ui/contract_dialog.py`, `app/ui/prestation_dialog.py` (import du service renommé)
- `app/repositories/artists_repository.py` *(adaptateur déjà mort — supprimé à cette
  occasion, conformément à l'audit initial du projet, puisqu'il n'est utilisé
  nulle part)*

**Migrations SQLite**
```
ALTER TABLE artists RENAME TO formations;
```
SQLite met à jour automatiquement les clauses `FOREIGN KEY ... REFERENCES
artists(id)` des tables `contracts` et `prestations` pour qu'elles pointent
vers `formations` — aucune perte de données, aucun identifiant modifié.

**Impacts**
- Toutes les références `artist_id` dans `contracts`/`prestations` continuent
  de fonctionner à l'identique (nom de colonne inchangé à ce stade — seul le
  nom de la table cible change).
- Les libellés d'interface (`Artistes` → `Formations`, `Nouvel artiste` →
  `Nouvelle formation`, etc.) changent partout.

**Risques**
Moyen : c'est le renommage le plus large de tout le plan (fichiers, classes,
imports). À faire en un seul sprint dédié, sans mélanger d'autre changement
fonctionnel (règle : ne jamais renommer et modifier le comportement en même
temps).

**Tests à effectuer**
- Migration : table `formations` présente, `artists` absente, données intactes
  (mêmes id, mêmes valeurs).
- Contrats et Prestations existants toujours liés à la bonne Formation après
  renommage (vérifier `artist_id` sur quelques enregistrements réels).
- CRUD complet sur Formations (créer, lire, modifier, supprimer, rechercher).
- Génération DOCX et export PDF sur un contrat existant : aucune régression.
- Démarrage complet de l'application, menu affichant « Formations ».

---

### Sprint 8.7 — Retirer le cachet habituel de la Formation

**Objectif**
Le prix n'appartient plus qu'à la Prestation, au Devis ou au Contrat — jamais à
la Formation elle-même.

**Fichiers concernés**
- `app/services/formation_service.py` (ne plus lire/écrire `fee`)
- `app/ui/formation_dialog.py` (retrait du champ « Cachet » du formulaire)
- `app/ui/contract_dialog.py` (le pré-remplissage du cachet ne peut plus venir
  de la Formation — cf. risques)

**Migrations SQLite**
Aucune. La colonne `formations.fee` (ex `artists.fee`) **n'est pas supprimée** :
conformément au principe déjà appliqué dans tout le projet, on cesse de la
lire/l'écrire, sans jamais faire de `DROP COLUMN`.

**Impacts**
- Le dialogue Contrat perd le pré-remplissage automatique du cachet depuis la
  Formation sélectionnée (fonctionnalité introduite au Sprint 6 — « Contrats
  intelligents »). C'est un changement de comportement assumé et voulu par ce
  ticket, à documenter clairement dans `BUSINESS_RULES.md` au moment du sprint.
- Le cachet reste pré-rempli depuis la Prestation si un devis/contrat en
  découle (le montant y sera défini une fois le module Devis livré).

**Risques**
Le principal risque est la régression perçue par l'utilisateur (« je n'ai plus
le cachet habituel proposé automatiquement »). À anticiper avec une
communication claire dans le résumé du sprint ; aucun risque technique
(suppression de lecture d'un champ, pas de suppression de données).

**Tests à effectuer**
- Création d'un contrat sans Formation reliée à un cachet : le champ Montant
  démarre à 0, modifiable normalement.
- Formulaire Formation : plus de champ Cachet visible, sauvegarde toujours
  fonctionnelle.
- Non-régression sur les contrats déjà existants (leur `cession_montant` reste
  inchangé, il n'a jamais été recalculé depuis la Formation après coup).
- Démarrage complet de l'application.

---

### Sprint 8.8 — Champs internes et marketing de la Formation

**Objectif**
Ajouter les informations utiles à la fiche artistique, au site web et aux
documents marketing — jamais aux documents juridiques.

**Fichiers concernés**
- `app/models/formation.py`
- `app/database/migrations.py` (colonnes additives)
- `app/ui/formation_dialog.py`
- `app/ui/formations.py` (colonnes de tableau éventuelles)

**Migrations SQLite**
```
ALTER TABLE formations ADD COLUMN configuration TEXT;     -- solo, duo, trio, quartet, variable
ALTER TABLE formations ADD COLUMN style_musical TEXT;
ALTER TABLE formations ADD COLUMN description TEXT;
ALTER TABLE formations ADD COLUMN logo_path TEXT;
ALTER TABLE formations ADD COLUMN photo_path TEXT;
ALTER TABLE formations ADD COLUMN site_internet TEXT;
ALTER TABLE formations ADD COLUMN reseaux_sociaux TEXT;
```
Toutes nullables, additives.

**Impacts**
Aucun sur les contrats/devis/factures : ces champs ne sont référencés par
**aucun** template de document juridique. Ils alimentent uniquement l'affichage
interne (fiche Formation) et serviront de source pour un futur export
« fiche artistique » ou pour le site web, hors périmètre de ce plan.

**Risques**
Faible, à une vigilance près : s'assurer qu'aucun développeur futur n'ajoute
par erreur `{{configuration}}` ou `{{nombre_musiciens}}` dans un template de
contrat — à rappeler explicitement dans `BUSINESS_RULES.md` (section 4 de ce
document).

**Tests à effectuer**
- Ajout des nouvelles informations sur une Formation existante, sauvegarde,
  relecture.
- Génération DOCX d'un contrat lié à cette Formation : aucun de ces champs
  n'apparaît dans le document généré.
- Démarrage complet de l'application.

---

### Sprint 8.9 — Module Membres

**Objectif**
Gérer les personnes qui composent une Formation, pour un usage strictement
interne.

**Fichiers concernés**
- `app/models/membre.py` *(nouveau)*
- `app/repositories/membre_repository.py` *(nouveau)*
- `app/services/membre_service.py` *(nouveau)*
- `app/ui/membres.py` *(nouveau — liste, rattachée à une Formation)*
- `app/ui/membre_dialog.py` *(nouveau)*
- `app/ui/formations.py` (point d'entrée « Membres » depuis une fiche Formation)

**Migrations SQLite**
```
CREATE TABLE IF NOT EXISTS membres(
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    formation_id  INTEGER NOT NULL,
    nom           TEXT NOT NULL,
    prenom        TEXT,
    telephone     TEXT,
    email         TEXT,
    instrument    TEXT,
    fonction      TEXT,
    actif         INTEGER DEFAULT 1,
    notes         TEXT,
    created_at    TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(formation_id)
        REFERENCES formations(id)
        ON DELETE CASCADE
)
```
`actif`/`inactif` permet de conserver l'historique d'un ancien membre sans le
supprimer.

**Impacts**
Aucun sur les documents commerciaux : aucune colonne `membre_id` n'est ajoutée
à `contracts`, `prestations`, ni aux futures tables `devis`/`factures`. Le
module est une extension pure d'une fiche Formation.

**Risques**
Faible. Seul point d'attention : `ON DELETE CASCADE` supprime réellement les
membres si la Formation est supprimée — cohérent car un Membre n'a aucune
existence en dehors de sa Formation (contrairement à une Prestation, qui
survit à la suppression d'un artiste ou d'un organisateur lié).

**Tests à effectuer**
- Création de plusieurs membres pour une même Formation.
- Marquage d'un membre en inactif : reste visible/filtrable, n'est plus proposé
  par défaut.
- Suppression d'une Formation : ses membres disparaissent (comportement
  attendu, à vérifier explicitement).
- Génération DOCX d'un contrat lié à cette Formation : aucun membre n'apparaît
  nulle part dans le document.
- Démarrage complet de l'application.

---

### Sprint 8.10 — Producteur dans les Prestations

**Objectif**
Alimenter automatiquement chaque Prestation avec le Producteur actif.

**Fichiers concernés**
- `app/models/prestation.py`
- `app/database/migrations.py`
- `app/services/prestation_service.py` (associe le producteur actif à la création)
- `app/ui/prestation_dialog.py` (affichage informatif, non modifiable a priori)

**Migrations SQLite**
```
ALTER TABLE prestations ADD COLUMN producteur_id INTEGER;
```
Nullable, additive. Pas de contrainte `FOREIGN KEY` ajoutable a posteriori par
`ALTER TABLE` sur la base existante (limitation SQLite déjà rencontrée au
Sprint 8.4 pour `contracts.prestation_id`) — une base neuve la porterait
nativement dans la clause `CREATE TABLE`.

**Impacts**
Les prestations déjà existantes gardent `producteur_id = NULL` ; elles
restent lisibles et fonctionnelles à l'identique.

**Risques**
Faible. Vérifier que la création d'une prestation ne plante pas si aucun
Producteur actif n'existe encore (cas d'une base fraîchement migrée avant le
Sprint 8.5) : `producteur_id` doit alors simplement rester `NULL`, sans lever
d'erreur bloquante.

**Tests à effectuer**
- Création d'une prestation avec un Producteur actif défini : `producteur_id`
  correctement renseigné.
- Création sans Producteur actif défini : aucune erreur, `producteur_id` reste
  `NULL`.
- Prestations existantes toujours lisibles.
- Démarrage complet de l'application.

---

### Sprint 8.11 — Producteur dans les Contrats (+ template DOCX)

**Objectif**
Remplacer le texte figé du Producteur dans le contrat par de vraies données,
sans jamais casser un contrat déjà généré.

**Fichiers concernés**
- `app/models/contract.py` (ajout `producteur_id` + instantané `producteur_*`)
- `app/database/migrations.py`
- `app/repositories/contract_repository.py`
- `app/services/contract_service.py` (associe le producteur actif, instantané
  figé au même principe que `organisateur_*`/`artiste_*`)
- `app/ui/contract_dialog.py` (affichage informatif du Producteur, cf. risques)
- `templates/contrat_cession.docx` (remplacement du texte figé par les
  placeholders `{{producteur_*}}`)

**Migrations SQLite**
```
ALTER TABLE contracts ADD COLUMN producteur_id INTEGER;
ALTER TABLE contracts ADD COLUMN producteur_structure TEXT;
ALTER TABLE contracts ADD COLUMN producteur_forme TEXT;
ALTER TABLE contracts ADD COLUMN producteur_adresse TEXT;
ALTER TABLE contracts ADD COLUMN producteur_postal_code TEXT;
ALTER TABLE contracts ADD COLUMN producteur_city TEXT;
ALTER TABLE contracts ADD COLUMN producteur_siret TEXT;
ALTER TABLE contracts ADD COLUMN producteur_licence TEXT;
ALTER TABLE contracts ADD COLUMN producteur_tva TEXT;
ALTER TABLE contracts ADD COLUMN producteur_iban TEXT;
ALTER TABLE contracts ADD COLUMN producteur_bic TEXT;
ALTER TABLE contracts ADD COLUMN producteur_representant TEXT;
ALTER TABLE contracts ADD COLUMN producteur_fonction TEXT;
```
Toutes nullables.

**Impacts**
- Les contrats **déjà générés** ne sont jamais régénérés automatiquement : ils
  restent tels quels, avec le texte figé de leur DOCX déjà produit.
- Seuls les **nouveaux** contrats (et ceux explicitement régénérés) utiliseront
  les nouveaux placeholders `{{producteur_*}}`.
- C'est le sprint le plus sensible du plan : il touche directement au
  générateur DOCX (`ContractGenerator`) et au template lui-même.

**Risques**
Élevé pour ce sprint précis, à traiter avec la plus grande prudence :
- Modifier le template DOCX peut casser le formatage existant si mal fait —
  toujours utiliser python-docx pour éditer un paragraphe existant (remplacer
  le texte des runs), jamais reconstruire la mise en page à la main.
- Toujours valider la génération DOCX **avant et après** la modification du
  template, sur un contrat de test dédié, avant de toucher aux contrats réels.
- Cette étape ne doit être livrée qu'après validation complète du Sprint 8.5
  (Producteur) et 8.10 (Producteur dans les Prestations), jamais en même temps
  qu'un autre changement structurant.

**Tests à effectuer**
- Génération DOCX d'un nouveau contrat : section Producteur correcte, issue des
  données réelles (plus de texte figé).
- Comparaison visuelle du rendu avant/après pour un contrat identique en
  contenu : aucune différence de mise en page, seul le texte devient
  dynamique.
- Export PDF : toujours fidèle au DOCX.
- Régénération d'un contrat existant (créé avant ce sprint) : fonctionne sans
  erreur, adopte désormais les nouveaux placeholders.
- Contrats non régénérés : leurs fichiers déjà produits restent inchangés sur
  le disque (on ne touche jamais un fichier déjà livré à un tiers sans action
  explicite de l'utilisateur).
- Démarrage complet de l'application.

---

### Sprint 9 — Devis

**Objectif**
Premier module de la chaîne commerciale à s'appuyer sur toute l'architecture
posée par les sprints 8.5 à 8.11 : Producteur, Formation, Organisateur et
Prestation, sans aucune ressaisie.

**Fichiers concernés** *(à détailler dans un ticket dédié le moment venu)*
- `app/models/devis.py`, `app/repositories/devis_repository.py`,
  `app/services/devis_service.py`, `app/ui/devis.py`, `app/ui/devis_dialog.py`
- Nouveau template DOCX de devis

**Migrations SQLite**
```
CREATE TABLE IF NOT EXISTS devis(
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    reference       TEXT UNIQUE NOT NULL,   -- DEVIS-AAAA-XXXX
    prestation_id   INTEGER,
    producteur_id   INTEGER,
    statut          TEXT DEFAULT 'brouillon',
    montant         REAL DEFAULT 0,
    ...
    FOREIGN KEY(prestation_id) REFERENCES prestations(id) ON DELETE SET NULL
)
```

**Impacts**
Un devis accepté doit pouvoir générer un contrat pré-rempli, exactement selon
le mécanisme déjà en place entre Prestation et Contrat (Sprint 8.4,
`ContractDialog(initial_contract=...)`).

**Risques**
Comparable au Sprint 8.4 (liaison Prestations ↔ Contrats), déjà éprouvé : le
risque principal serait de casser le fonctionnement autonome des Contrats —
à re-tester systématiquement.

**Tests à effectuer**
Repris du standard déjà appliqué : création, modification, suppression,
recherche, génération DOCX, transformation devis → contrat, non-régression
complète, démarrage de l'application.

*(Les sprints Factures et Paiements suivront le même schéma de detailed
planning, à rédiger dans des tickets dédiés le moment venu — ils dépendent des
retours d'expérience des sprints Devis et Producteur-dans-les-Contrats.)*

---

## 3. Ordre conseillé (résumé)

```
Sprint 8.5   Producteur (fondations, multi-producteurs, un seul actif)
Sprint 8.6   Renommer Artistes -> Formations
Sprint 8.7   Retirer le cachet habituel de la Formation
Sprint 8.8   Champs internes et marketing de la Formation
Sprint 8.9   Module Membres
Sprint 8.10  Producteur dans les Prestations
Sprint 8.11  Producteur dans les Contrats (+ template DOCX)
Sprint 9     Devis
Sprint 9.x   Factures
Sprint 9.x   Paiements
v1.0         Stabilisation, non-regression complete, packaging
```

Logique de cet ordre :
- Les **fondations de données** (Producteur, section 8.5) précèdent toute
  connexion.
- Le **renommage** (8.6) est isolé en un sprint unique, sans mélange avec un
  changement de comportement.
- Le **retrait du cachet** (8.7) et les **champs internes** (8.8) sont
  volontairement séparés : deux changements de nature différente (retrait vs
  ajout) ne doivent pas être livrés ensemble.
- **Membres** (8.9) est placé après la stabilisation de Formations : il en
  dépend directement (`formation_id`), mais n'a aucune dépendance vers
  Producteur.
- **Producteur dans les Prestations** (8.10) précède **Producteur dans les
  Contrats** (8.11) : la Prestation est le point d'entrée naturel désormais
  (Sprint 8.4), il est plus sûr de valider la donnée à ce niveau avant de
  toucher au générateur DOCX.
- Le sprint le plus sensible techniquement (8.11, modification du template
  DOCX) arrive en dernier parmi les sprints structurants, une fois toutes les
  fondations de données validées.
- **Devis** (9) n'arrive qu'une fois Producteur et Formations pleinement
  intégrés aux Contrats, pour ne pas avoir à refaire ce travail deux fois.

---

## 4. Règles importantes (rappel contraignant pour tous les sprints ci-dessus)

- Le **Producteur** est l'entité juridique : il facture, signe, possède SIRET,
  licence, coordonnées bancaires.
- La **Formation** est l'entité artistique : jamais signataire d'un contrat.
- Les **Membres** servent uniquement la gestion interne.
- Les Membres ne doivent **jamais** apparaître automatiquement dans un devis,
  un contrat ou une facture — aucun champ `membre_id` sur ces tables, à aucun
  sprint.
- Le **nombre de musiciens** ne doit jamais être imprimé automatiquement sur
  un document commercial ou juridique.
- La **configuration** (solo, duo, trio, quartet, variable) ne doit jamais être
  imprimée automatiquement sur un document commercial ou juridique.
- Le **prix** n'appartient qu'à la Prestation, au Devis ou au Contrat — jamais
  à la Formation.

Tout sprint qui violerait une de ces règles doit être considéré en échec, quels
que soient les tests techniques par ailleurs validés.

---

## 5. Vision long terme (jusqu'à la v1.0)

```
v0.5.x  Prestations (fait), Producteur, Formations, Membres
v0.6    Producteur pleinement integre aux Prestations et aux Contrats
v0.7    Devis
v0.8    Factures
v0.9    Paiements, Agenda, Documents (Dossier deja pose par Prestations)
v0.9.x  Parametres (fiche Producteur active, template par defaut),
        Statistiques (CA par Formation/Organisateur/periode)
v1.0    Stabilisation complete :
        - non-regression sur tous les modules
        - coherence visuelle et ergonomique globale
        - Producteur, Formation, Membres, Organisateur, Prestation, Devis,
          Contrat, Facture, Paiement tous relies sans ressaisie
        - packaging pour installation sur un nouveau poste
```

À la v1.0, le logiciel représente fidèlement l'activité réelle d'un producteur
de spectacles : une structure juridique (Producteur) qui engage des formations
artistiques (Formations, avec leurs membres gérés en interne) pour des
organisateurs (Organisateurs), autour d'événements réels (Prestations), du
premier contact jusqu'au paiement final (Devis → Contrat → Facture →
Paiement) — sans qu'aucune information ne soit jamais ressaisie deux fois.
