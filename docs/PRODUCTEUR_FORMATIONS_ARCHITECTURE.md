# YGNT Manager — Évolution de l'architecture métier (Producteur / Formations / Membres)

Document de conception. Aucune ligne de code, aucune migration, aucun commit ne
sont réalisés par ce document. Il complète `PROJECT.md`, `CODING_RULES.md`,
`BUSINESS_RULES.md`, `ROADMAP.md` et `PRESTATIONS_ARCHITECTURE.md`.

---

## 1. Principe directeur

Le logiciel confondait jusqu'ici deux notions :

- **L'entité juridique qui produit et facture** (aujourd'hui : du texte figé en
  dur dans le template DOCX, jamais issu d'une donnée réelle).
- **L'entité artistique engagée** (aujourd'hui : le module Artistes, avec un
  cachet habituel qui n'a pas sa place sur la fiche elle-même).

Cette évolution introduit une distinction claire, conforme au fonctionnement
réel d'un producteur de spectacles :

```
Producteur      -> qui facture, signe, possede le SIRET/la licence/la banque
Formation       -> l'entite artistique engagee (ex. SANFUEGO)
Membres         -> les personnes qui composent une Formation (gestion interne)
Organisateur    -> inchange
```

Le Contrat reste strictement l'accord juridique entre le **Producteur** et
l'**Organisateur** ; la **Formation** en est l'objet (ce qui est engagé), jamais
une partie contractante.

---

## 2. Producteur (nouvelle entité)

Le Producteur est l'entité qui facture, signe les contrats, possède le SIRET, la
licence, les coordonnées bancaires et le logo. Aujourd'hui, ces informations
(« YGNT Production », SIRET, licence, représentant) sont **écrites en dur dans
le template DOCX** — elles n'existent dans aucune table. C'est une dette
directe : si le SIRET ou le représentant légal change, il faut éditer le
template à la main.

### Structure de table proposée

```
producteurs
├── id                INTEGER PK AUTOINCREMENT
├── nom               TEXT NOT NULL        -- "YGNT Production"
├── forme_juridique   TEXT                 -- "Association loi 1901"
├── adresse           TEXT
├── postal_code       TEXT
├── city              TEXT
├── siret             TEXT
├── ape                TEXT
├── licence           TEXT                 -- licence d'entrepreneur de spectacles
├── tva               TEXT
├── iban              TEXT
├── bic               TEXT
├── representant      TEXT                 -- "Tanguy ZAHN"
├── fonction          TEXT                 -- "President"
├── logo_path         TEXT                 -- chemin du fichier logo
├── site_internet     TEXT
├── email             TEXT
├── phone             TEXT
├── notes             TEXT
├── actif             INTEGER DEFAULT 1    -- producteur utilise par defaut
├── created_at        TEXT DEFAULT CURRENT_TIMESTAMP
├── updated_at        TEXT
```

### Particularité d'usage

Contrairement aux Organisateurs, il n'y a normalement **qu'un seul Producteur
actif** : YGNT Manager reste un outil pour une structure de production donnée.
Le modèle reste une vraie table (pas une simple ligne de `settings`) pour rester
cohérent avec le reste de l'architecture et pour ne pas fermer la porte à une
structure secondaire si le besoin apparaît un jour — mais l'interface future
(module **Paramètres**, déjà prévu dans `ROADMAP.md`) présentera une **fiche
unique**, pas une liste avec recherche.

---

## 3. Formations (évolution du module Artistes)

Le module Artistes devient **Formations**. Une Formation représente un artiste
solo, un groupe, une compagnie, un DJ ou un orchestre (ex. SANFUEGO).

### Ce qui disparaît de la fiche

- **Le cachet habituel** (`fee`). Le prix n'est plus une propriété de la
  Formation : il se définit uniquement au niveau de la Prestation ou du
  Contrat, au cas par cas.

### Ce qui reste (informations utiles à la prestation artistique)

Nom de scène, nom légal, adresse, coordonnées, informations légales et
bancaires (SIREN, SIRET, code APE, licence, IBAN, BIC, numéro de sécurité
sociale), notes — reprise à l'identique du modèle Artiste actuel, moins `fee`.

### Champs internes complémentaires (facultatifs, jamais imprimés)

Pour servir la logistique (mais jamais un document juridique) :

- `type_formation` (solo, duo, trio, quartet, groupe, orchestre, compagnie...)
- `nombre_musiciens`

Ces deux champs sont **strictement internes** : voir règle dédiée en section 8.

---

## 4. Membres (futur module)

Chaque Membre appartient à une Formation (ex. SANFUEGO → Anthony, Miguel,
Carlos). Gestion interne uniquement.

### Structure de table proposée

```
membres
├── id            INTEGER PK AUTOINCREMENT
├── formation_id  INTEGER NOT NULL   FK -> formations(id) ON DELETE CASCADE
├── nom           TEXT NOT NULL
├── prenom        TEXT
├── telephone     TEXT
├── email         TEXT
├── instrument    TEXT
├── fonction      TEXT               -- ex. "Chanteur", "Batteur", "Régisseur"
├── notes         TEXT
├── created_at    TEXT DEFAULT CURRENT_TIMESTAMP
```

`ON DELETE CASCADE` (et non `SET NULL`) : un Membre n'a pas d'existence en
dehors de sa Formation — contrairement à une Prestation, qui doit survivre à la
suppression de l'artiste ou de l'organisateur qui lui est lié.

### Règle stricte

Les membres ne doivent **jamais** apparaître automatiquement dans un devis, un
contrat ou une facture. Aucun champ `membre_id` n'existe ni n'existera sur ces
tables. Le module Membres est un carnet d'adresses interne à la Formation, pas
une source de données pour les documents commerciaux.

---

## 5. Organisateurs

Aucun changement. Le module reste exactement tel qu'il est aujourd'hui.

---

## 6. Prestations

La Prestation devient la matérialisation de la chaîne :

```
Producteur -> Formation -> Organisateur -> Lieu -> Date -> Dossier
```

Impact sur le modèle `prestations` (`PRESTATIONS_ARCHITECTURE.md`) :

- `artist_id` devient conceptuellement `formation_id` (la table cible se
  renomme `artists` → `formations`, cf. section 9 — le nom de la colonne peut
  rester `artist_id` ou être renommé selon la profondeur de la migration
  choisie, voir plan de transition).
- Nouvelle colonne `producteur_id` (nullable, FK -> `producteurs(id)`), remplie
  automatiquement avec le Producteur actif à la création d'une prestation.
- Le reste (`organization_id`, `lieu_*`, `date_debut`/`date_fin`, `statut`,
  Dossier, Timeline) est inchangé.

---

## 7. Contrats — clarification du rôle juridique

Le contrat continue de représenter **uniquement** l'accord entre le Producteur
et l'Organisateur. La Formation est l'entité artistique engagée par cet
accord — jamais une partie contractante.

Concrètement, cela implique à terme :

- Ajout de `producteur_id` (FK nullable) + un instantané figé
  `producteur_structure`, `producteur_forme`, `producteur_adresse`,
  `producteur_postal_code`, `producteur_city`, `producteur_siret`,
  `producteur_licence`, `producteur_tva`, `producteur_iban`, `producteur_bic`,
  `producteur_representant`, `producteur_fonction` — exactement le même
  principe que l'instantané déjà en place pour `organisateur_*` et
  `artiste_*` (cf. `BUSINESS_RULES.md`).
- Les champs `artiste_*` existants gardent leur rôle (informations de la
  Formation engagée), simplement rebaptisés `formation_*` dans une migration
  ultérieure si l'on va au bout du renommage (voir section 9).
- Le template DOCX (`contrat_cession.docx`) devra remplacer le texte figé
  actuel de la section Producteur par de vrais placeholders
  `{{producteur_structure}}`, `{{producteur_siret}}`, `{{producteur_licence}}`,
  `{{producteur_representant}}`, `{{producteur_fonction}}`, etc. — ce qui
  rendra enfin cette section modifiable sans toucher au fichier Word.

Aucune de ces informations n'est retirée du contrat : elles ne sont plus
codées en dur, elles deviennent des données réelles.

---

## 8. Règles métier

- Le **nombre de musiciens** de la Formation ne doit jamais être imprimé
  automatiquement sur un contrat, un devis ou une facture.
- Le **type de formation** (duo, trio, quartet...) ne doit jamais être imprimé
  automatiquement sur un contrat, un devis ou une facture.
- Ces deux informations existent uniquement pour l'usage interne (logistique,
  fiche technique, dossier) — jamais comme placeholder de génération de
  document juridique ou commercial.
- Le contrat représente uniquement l'accord Producteur ↔ Organisateur ; la
  Formation y figure comme objet de la prestation, jamais comme signataire.
- Les Membres ne sont jamais une source de donnée pour un document commercial.
- Un seul Producteur est actif à la fois (`actif = 1`) ; c'est lui qui alimente
  automatiquement toute nouvelle Prestation et tout nouveau Contrat créé sans
  prestation.

---

## 9. Impacts sur les modules existants

| Module | Impact |
|---|---|
| **Artistes → Formations** | Renommage du module (table, modèle, service, repository, UI). Retrait de l'usage du champ `fee` dans le service/l'UI (la colonne peut rester en base, simplement plus lue/écrite — cohérent avec le principe déjà appliqué de ne jamais supprimer une colonne). Ajout facultatif de `type_formation`/`nombre_musiciens`. |
| **Organisateurs** | Aucun impact. |
| **Contrats** | Ajout de `producteur_id` + instantané `producteur_*`. Le template DOCX doit évoluer pour utiliser ces nouveaux placeholders à la place du texte figé. Aucune régression sur les contrats déjà générés (nouvelles colonnes nullables). |
| **Prestations** | Ajout de `producteur_id`. Renommage conceptuel de la relation vers Formation. |
| **Nouveau module Producteur** | Fiche unique (pas de liste), rattachée au futur module Paramètres déjà prévu dans `ROADMAP.md`. |
| **Nouveau module Membres** | CRUD complet rattaché à une Formation, sur le même standard que les autres modules (recherche, tableau, Nouveau/Modifier/Supprimer/Actualiser). |
| **Dashboard, Devis, Factures, Paiements** (prévus) | Devront utiliser le Producteur (facturation) et la Formation (objet de la prestation) selon les mêmes principes dès leur conception, pour ne pas reproduire l'ambiguïté actuelle. |

---

## 10. Migrations nécessaires plus tard (non réalisées ici)

Toutes additives et rétrocompatibles, dans l'esprit déjà appliqué depuis le
Sprint 1 (`_ensure_columns`, jamais de suppression de colonne) :

1. `CREATE TABLE producteurs(...)` (section 2).
2. `CREATE TABLE membres(...)` avec FK `formation_id -> formations(id) ON DELETE CASCADE` (section 4).
3. `ALTER TABLE artists RENAME TO formations` — SQLite met à jour automatiquement
   les clauses `FOREIGN KEY ... REFERENCES artists(id)` des autres tables
   (`contracts`, `prestations`) pour qu'elles pointent vers `formations` ; aucune
   perte de données, aucune casse des identifiants existants.
4. Ne **pas** supprimer la colonne `formations.fee` (ex-`artists.fee`) : cesser
   simplement de la lire/l'écrire côté service et interface.
5. `ALTER TABLE contracts ADD COLUMN producteur_id INTEGER` + colonnes
   `producteur_*` (instantané), toutes nullables.
6. `ALTER TABLE prestations ADD COLUMN producteur_id INTEGER`, nullable.
7. Mise à jour du template `contrat_cession.docx` : remplacement du texte figé
   de la section Producteur par les placeholders `{{producteur_*}}`.
8. (Facultatif, plus tard) Renommage des colonnes `artist_id` → `formation_id`
   et `artiste_*` → `formation_*` sur `contracts`/`prestations`, une fois le
   renommage du module stabilisé et testé — pas indispensable au fonctionnement,
   uniquement pour la clarté du code.

---

## 11. Plan de transition progressif

Chaque étape doit se terminer par une application qui démarre sans erreur, sans
aucune régression sur les contrats/DOCX/PDF existants — même discipline que
tous les sprints précédents.

**Étape 1 — Producteur (fondations)**
Créer table + modèle + repository + service (aucune UI), saisir manuellement le
Producteur actuel (YGNT Production) en base. Aucun impact visible.

**Étape 2 — Producteur dans les contrats**
Ajouter `producteur_id` + instantané `producteur_*` sur `contracts`. Le
`ContractService` associe automatiquement le Producteur actif à tout nouveau
contrat. Le template DOCX n'est pas encore modifié (texte figé conservé le
temps de valider la donnée en parallèle).

**Étape 3 — Template DOCX**
Remplacer le texte figé de la section Producteur par les placeholders
`{{producteur_*}}`, une fois les données validées à l'étape 2. Tester
intensivement la génération DOCX/PDF (règle n°1 : ne jamais casser le
générateur).

**Étape 4 — Renommage Artistes → Formations**
Renommer table/modèle/service/UI, retirer `fee` de l'usage (sans supprimer la
colonne). Mettre à jour `prestations`/`contracts` pour référencer les
Formations. Non-régression complète sur Contrats et Prestations.

**Étape 5 — Champs internes Formation**
Ajouter `type_formation`/`nombre_musiciens` sur `formations`, uniquement
visibles dans l'interface Formations — jamais dans un template de document.

**Étape 6 — Module Membres**
CRUD complet rattaché à une Formation, sur le standard habituel de
l'interface. Aucune connexion aux Contrats/Devis/Factures.

**Étape 7 — Producteur dans Prestations**
Ajouter `producteur_id` sur `prestations`, alimenté automatiquement.

Chaque étape est indépendante et livrable seule ; l'ordre proposé minimise le
risque (les fondations de données avant l'UI, le renommage sensible en dernier
parmi les changements structurants, Membres — sans aucune dépendance externe —
en position la plus sûre).
