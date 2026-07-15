# YGNT Manager — Architecture du module Prestations (référence)

Document de conception final. Consolide la proposition du ticket #0009 avec les
décisions actées au ticket #0010. Ce document sert de référence unique pour le
développement du module Prestations ; il complète `PROJECT.md`,
`CODING_RULES.md`, `BUSINESS_RULES.md` et `ROADMAP.md` sans les remplacer.

Aucun code, aucun fichier applicatif, aucune base n'est modifié par ce document.

---

## 1. Principe directeur

**La Prestation est l'entité centrale du logiciel.**

Un événement réel (mariage, festival, mairie, comité d'entreprise, anniversaire,
soirée privée...) existe désormais en tant que fiche à part entière, indépendamment
du nombre de documents administratifs générés autour de lui. Devis, Contrat,
Facture et Paiement deviennent des documents **rattachés** à une Prestation, plutôt
que des entités isolées qui se ressaisissent mutuellement les mêmes informations.

Le Contrat reste pleinement fonctionnel seul (rétrocompatibilité totale avec
l'existant) ; la Prestation est une couche au-dessus, pas un remplacement.

---

## 2. Référence unique de la prestation

Chaque prestation reçoit une référence unique au format :

```
PREST-AAAA-XXXX
```

- `AAAA` : année de création de la prestation.
- `XXXX` : séquence sur 4 chiffres, propre à la Prestation (compteur indépendant
  de la numérotation des contrats `YGNT-AAAA-XXXX`).
- Même algorithme que la numérotation des contrats déjà en place (règle décrite
  dans `BUSINESS_RULES.md`) : la séquence se base sur la dernière référence
  attribuée pour l'année en cours, jamais sur un simple comptage total — elle
  reste donc correcte même après suppression/archivage d'une prestation.
- La référence est attribuée à la création et n'est plus modifiable ensuite.

---

## 3. Rattachement des documents à la prestation

Tous les documents métier se rattachent à la prestation par une clé étrangère
**portée par le document**, jamais l'inverse — car une prestation peut exister
avant qu'aucun document ne soit créé (phase de prospection), et peut accumuler
plusieurs documents du même type au fil du temps (devis revu, contrat dupliqué) :

```
contracts  .prestation_id   FK -> prestations(id)   NULL   (colonne ajoutee, existant)
devis      .prestation_id   FK -> prestations(id)   NULL   (futur module)
factures   .prestation_id   FK -> prestations(id)   NULL   (futur module)
paiements  .prestation_id   FK -> prestations(id)   NULL   (futur module)
```

Les contrats déjà existants conservent `prestation_id = NULL` : ils restent
lisibles et générables exactement comme aujourd'hui. Un contrat garde par
ailleurs ses propres `artist_id`/`organization_id` et son instantané figé
(`organisateur_*`/`artiste_*`) : quand il est créé depuis une prestation, ces
champs sont simplement pré-remplis à partir d'elle, selon le même mécanisme
d'auto-remplissage déjà en service entre fiches Artiste/Organisateur et Contrat.

---

## 4. Le Dossier (remplace « Documents »)

Le **Dossier** est la vue consolidée de tout ce qui se rapporte à une prestation.
Il regroupe deux natures d'éléments bien distinctes, pour éviter toute
duplication :

**a) Les documents transactionnels** — Devis, Contrats, Factures, Paiements —
existent déjà chacun dans leur propre table, avec leur propre cycle de vie. Le
Dossier ne duplique pas ces données : il les **interroge** via `prestation_id` et
les présente ensemble (nom, date, statut, montant, actions Ouvrir/Générer).

**b) Les pièces jointes libres** — photos, riders, plans de scène,
autorisations, pièces jointes diverses — n'ont pas d'autre table d'origine ; elles
sont stockées dans une nouvelle table dédiée :

```
prestation_dossier
├── id              INTEGER PK AUTOINCREMENT
├── prestation_id   INTEGER NOT NULL   FK -> prestations(id) ON DELETE CASCADE
├── categorie       TEXT    NOT NULL   (piece_jointe, photo, rider,
│                                       plan_de_scene, autorisation, autre)
├── nom_original    TEXT    NOT NULL
├── chemin_fichier  TEXT    NOT NULL
├── ajoute_le       TEXT    DEFAULT CURRENT_TIMESTAMP
```

Le Dossier affiché à l'écran = documents transactionnels (via requêtes croisées)
+ contenu de `prestation_dossier`, présentés ensemble, filtrables par catégorie.

---

## 5. La Timeline (remplace « Historique »)

L'historique technique façon `contract_history` (« Création », « Modification »,
« Génération DOCX »...) est remplacé, au niveau de la Prestation, par une
**Timeline** qui raconte la vie de l'événement en termes métier :

```
Demande reçue
Devis créé
Devis envoyé
Devis accepté
Contrat signé
Concert réalisé
Facture envoyée
Paiement reçu
Dossier archivé
```

Structure de table :

```
prestation_timeline
├── id              INTEGER PK AUTOINCREMENT
├── prestation_id   INTEGER NOT NULL   FK -> prestations(id) ON DELETE CASCADE
├── evenement       TEXT    NOT NULL   (libellé métier, ex. "Devis envoyé")
├── details         TEXT
├── source          TEXT    NOT NULL   ('auto' ou 'manuel')
├── survenu_le      TEXT    DEFAULT CURRENT_TIMESTAMP
```

- **Entrées automatiques** (`source = 'auto'`) : générées par le logiciel quand un
  document change d'état sous la prestation (un devis est créé, un contrat passe
  à « signé », un paiement est enregistré). Chaque module (Devis, Contrat,
  Facture, Paiement) ajoute sa propre ligne à la Timeline de sa prestation au
  moment de l'action, en plus de son propre historique technique existant
  (`contract_history` n'est pas supprimé : il continue d'exister pour le détail
  fin du contrat, la Timeline en offre la lecture métier consolidée).
- **Entrées manuelles** (`source = 'manuel'`) : l'utilisateur peut ajouter un jalon
  libre (« Demande reçue par téléphone », « Relancer le client avant le 15/07 »).
- La Timeline est un journal **append-only** : on n'y modifie ni n'y supprime une
  entrée, on en ajoute une nouvelle — elle doit rester une trace fidèle du
  déroulé réel.

---

## 6. Structure exacte de la table `prestations`

```
prestations
├── id                    INTEGER PK AUTOINCREMENT
├── reference             TEXT    UNIQUE NOT NULL   -- PREST-AAAA-XXXX
├── type_evenement        TEXT    NOT NULL          -- mariage, festival, mairie,
│                                                       comite_entreprise,
│                                                       anniversaire,
│                                                       soiree_privee, autre
├── nom                   TEXT    NOT NULL          -- libelle lisible
├── statut                TEXT    NOT NULL DEFAULT 'prospection'
│                                                    -- prospection, devis_envoye,
│                                                       confirmee, realisee,
│                                                       facturee, soldee,
│                                                       archivee, annulee
├── date_debut            TEXT    NOT NULL
├── date_fin              TEXT                      -- optionnel (festival multi-jours)
│
├── artist_id             INTEGER                    FK -> artists(id)
├── organization_id       INTEGER                    FK -> organizations(id)
│
├── lieu_nom              TEXT                       -- nom de la salle / du site
├── lieu_adresse          TEXT
├── lieu_postal_code      TEXT
├── lieu_city             TEXT
│
├── notes                 TEXT
├── created_at            TEXT    DEFAULT CURRENT_TIMESTAMP
├── updated_at            TEXT
```

Notes de conception :

- `artist_id` et `organization_id` sont **nullables** : une prestation existe dès
  la demande initiale, avant même de savoir qui jouera ou pour quel organisateur.
- Aucun montant n'est stocké sur `prestations` : le montant affiché dans les
  listes est **dérivé** du devis/contrat le plus pertinent qui lui est rattaché
  (pas de vérité financière dupliquée — elle vit sur le document qui l'engage
  réellement).
- `statut` reflète l'état courant (utilisé pour filtrer/trier le tableau) ; la
  Timeline reste la source détaillée et chronologique — les deux sont liés mais
  ne sont pas la même donnée : `statut` peut être mis à jour automatiquement
  quand un jalon majeur de la Timeline survient.
- Toute évolution ultérieure de ce schéma suit la règle déjà en vigueur pour
  `contracts`/`organizations` : colonnes ajoutées de façon additive et
  rétrocompatible, jamais de renommage ni de suppression de colonne existante.

---

## 7. Relations avec l'existant et les futurs modules

| Table | Relation | Nature |
|---|---|---|
| `artists` | `prestations.artist_id` | optionnelle, inchangée dans `artists` |
| `organizations` | `prestations.organization_id` | optionnelle, inchangée dans `organizations` |
| `contracts` | `contracts.prestation_id` (nouvelle colonne, nullable) | un contrat peut exister sans prestation (rétrocompatibilité) |
| `devis` *(futur)* | `devis.prestation_id` | un devis peut précéder tout contrat |
| `factures` *(futur)* | `factures.prestation_id` | rattachée à l'événement, pas seulement au contrat |
| `paiements` *(futur)* | `paiements.prestation_id` + `paiements.facture_id` | rattachement à l'événement et rapprochement précis avec la facture réglée |

Une prestation peut donc porter, au fil du temps, plusieurs contrats (version
révisée, duplication), plusieurs devis, plusieurs factures et plusieurs
paiements : la relation est toujours 1 (prestation) → N (documents), jamais
l'inverse.

---

## 8. Règles métier

- Une prestation = un événement réel, unique et daté. Pas de sous-prestations,
  pas d'imbrication (principe de simplicité de `CODING_RULES.md`).
- Artiste et organisateur ne sont pas obligatoires à la création ; ils deviennent
  nécessaires avant de générer un devis ou un contrat (reprise de la règle
  contrat déjà en vigueur : « organisateur obligatoire, spectacle obligatoire »).
- Le lieu (nom, adresse, code postal, ville) est saisi **une seule fois**, sur la
  prestation ; devis, contrat et facture l'héritent automatiquement — suite
  logique de la correction apportée au ticket #0007.1 (séparation lieu de
  prestation / siège de l'organisateur), désormais structurelle.
- Suppression : jamais de suppression physique d'une prestation portant déjà un
  contrat signé ou une facture — passage au statut `annulee` (suppression
  logique), conformément à la Règle n°1 de `CODING_RULES.md`.
- Le Dossier ne duplique jamais les documents transactionnels : il les affiche
  par requête croisée sur `prestation_id` ; seules les pièces jointes libres sont
  stockées dans `prestation_dossier`.
- La Timeline est append-only et reflète des jalons métier, pas des actions
  techniques CRUD ; `contract_history` (et les historiques équivalents à venir
  pour Devis/Facture/Paiement) continuent d'exister pour le détail technique fin
  et alimentent la Timeline en plus de leur propre journal.

---

## 9. Structure de l'interface utilisateur

### Module Prestations (liste)

Présentation homogène avec les autres modules (`PROJECT.md`) : recherche,
tableau, double-clic pour modifier, boutons Nouveau / Modifier / Supprimer /
Actualiser.

Colonnes du tableau : Référence, Date, Type d'événement, Nom, Artiste,
Organisateur, Lieu, Statut, Montant *(dérivé du devis/contrat)*, Devis (oui/non),
Contrat (oui/non), Facture (oui/non), Paiement (soldé/non).

### Fiche Prestation

Dialogue à onglets (même socle ergonomique que le Contrat depuis le ticket
#0007 : redimensionnable, taille mémorisée, boutons Enregistrer/Annuler toujours
visibles) :

1. **Général** — Référence *(lecture seule)*, type d'événement, nom, statut,
   date(s)
2. **Artiste** — sélection + pré-remplissage automatique (mécanisme existant)
3. **Organisateur** — sélection + pré-remplissage automatique (mécanisme existant)
4. **Lieu** — nom de salle, adresse, code postal, ville (source unique pour tous
   les documents rattachés)
5. **Dossier** — vue filtrable par catégorie (Tous / Devis / Contrats / Factures
   / Paiements / Pièces jointes / Photos / Riders / Plans de scène /
   Autorisations / Autres), avec actions contextuelles : Générer un nouveau
   document (pré-rempli depuis la prestation), Ouvrir, Importer un fichier
6. **Timeline** — liste chronologique des jalons (icône selon la nature de
   l'événement, date, détail), avec un champ pour ajouter un jalon manuel

### Point d'entrée depuis Contrats

Le module Contrats existant continue de fonctionner de façon autonome
(création indépendante inchangée). Il gagne un point d'entrée supplémentaire :
« Créer le contrat » directement depuis l'onglet Dossier d'une fiche Prestation,
avec pré-remplissage complet (artiste, organisateur, lieu déjà connus).

---

## 10. Pourquoi cette architecture est préférable à l'architecture actuelle

- **Une seule saisie** de l'artiste, de l'organisateur et du lieu sert à tous les
  documents d'un même événement, au lieu de la répéter à chaque module futur.
- **Le logiciel colle à la façon dont un producteur pense réellement** : des
  événements, pas des paperasses isolées — conforme à la vision `PROJECT.md`.
- **Zéro régression** : Contrats reste 100 % autonome et rétrocompatible
  (`prestation_id` nullable), rien de l'existant n'est modifié.
- **Un dossier et une histoire par événement** : le Dossier centralise tous les
  documents et pièces jointes, la Timeline en raconte le déroulé complet — fini
  les historiques isolés et les fichiers dispersés.
- **Base saine pour le Dashboard et les Statistiques** déjà prévus dans
  `ROADMAP.md` : prochaines prestations, chiffre d'affaires par événement, taux
  de transformation devis → contrat deviennent des requêtes simples sur une
  table pivot unique.

---

## 11. Équipe de prestation (`prestation_participants`) — Sprint 15.5

**Réalisé** (contrairement au reste de ce document, qui restait au stade de
la conception : cette section documente une implémentation livrée).

### Principe

Le contrat de cession, le devis et la facture continuent de fonctionner
**uniquement** avec Organisateur / Formation / Prestation — la Formation
(`prestations.artist_id`) représente exclusivement **le spectacle vendu**,
jamais les personnes qui le jouent. Cette règle est intangible et n'est pas
remise en cause par ce qui suit.

Il manquait cependant un moyen de savoir **qui participe réellement** à une
prestation (les musiciens d'une Formation, un technicien, un road manager...)
sans jamais mélanger cette information avec ce qui alimente un document
commercial. C'est le rôle de l'**Équipe de prestation** : une donnée
strictement interne, indépendante du contrat de cession.

### Structure de table

```
prestation_participants
├── id              INTEGER PK AUTOINCREMENT
├── prestation_id   INTEGER NOT NULL   FK -> prestations(id) ON DELETE CASCADE
├── artiste_id      INTEGER NOT NULL   FK -> artists(id)     ON DELETE CASCADE
├── role            TEXT                -- optionnel
├── ordre           INTEGER             -- optionnel
├── created_at      TEXT DEFAULT CURRENT_TIMESTAMP
├── updated_at      TEXT

UNIQUE(prestation_id, artiste_id)
```

- Relation many-to-many : une Prestation possède 0..N participants ; un
  Artiste participe à 0..N prestations.
- Aucune duplication de donnée Artiste — seule la relation (qui, quel rôle,
  quel ordre d'affichage) est stockée ici.
- `role` et `ordre` sont facultatifs : une ligne sans rôle ni ordre est
  parfaitement valide.
- Contrainte `UNIQUE(prestation_id, artiste_id)` : un même artiste ne peut
  apparaître qu'une seule fois dans l'équipe d'une même prestation.
- `ON DELETE CASCADE` des deux côtés : supprimer une Prestation ou un Artiste
  retire simplement les lignes de participation correspondantes, sans jamais
  supprimer l'autre entité — cohérent avec la nature de simple table de
  liaison (à la différence de `contracts.artist_id`, qui cascade sur un
  document commercial complet, l'équipe de prestation ne porte aucune donnée
  propre à perdre au-delà de la relation elle-même).

### Règle métier intangible

Les participants sont des données **internes**. Ils ne doivent **jamais**
être injectés automatiquement dans un contrat de cession, un devis ou une
facture — ces trois documents ne lisent ni n'écrivent jamais
`prestation_participants`. Vérifié par test (`test_prestation_participants_migration.py`)
au niveau du schéma (aucune colonne liée sur `contracts`/`devis`/`factures`)
et au niveau fonctionnel (créer un contrat de cession n'ajoute aucune ligne
dans `prestation_participants`, et réciproquement).

### Consommateurs

Cette donnée sert, dès maintenant ou à terme :

- au **module CDDU** (`docs/CDDU_ARCHITECTURE.md`) — le futur générateur de
  contrats de travail utilisera exclusivement `prestation_participants` pour
  déterminer quels contrats créer et pour quels artistes ;
- aux futures **feuilles de présence** ;
- aux futures **feuilles de route** ;
- aux futures **statistiques** (nombre de dates par musicien, etc.) ;
- aux futurs **calculs de coûts** ;
- à une future **intégration de signature électronique**.

### Évolution future sans changement d'architecture

Le champ `role` est un texte libre, volontairement non contraint par une
énumération figée : l'équipe pourra, à terme, accueillir aussi bien des
musiciens que des danseurs, des techniciens, un road manager ou des invités,
sans qu'aucune migration de schéma ne soit nécessaire — il s'agit toujours de
la même ligne (prestation, artiste, rôle, ordre).

### Ce qui ne change pas

- `prestations.artist_id` (Formation vendue) reste inchangé, dans son rôle
  exact.
- Aucun impact sur `contracts`, `devis`, `factures` — ni colonne ajoutée, ni
  lecture, ni écriture automatique.
- Aucune UI, aucun écran, aucun bouton, aucun formulaire n'accompagne cette
  livraison : migration, modèle (`app/models/prestation_participant.py`),
  repository (`app/repositories/prestation_participant_repository.py`) et
  service (`app/services/prestation_participant_service.py`) uniquement.

---

Ce document constitue la référence à utiliser pour le développement futur du
module Prestations. La section 11 (Équipe de prestation) est la seule partie
de ce document effectivement implémentée à ce stade ; le reste demeure au
stade de la conception.
