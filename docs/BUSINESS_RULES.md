# YGNT Manager - Règles métier

Ce document décrit les règles de gestion réellement appliquées par le logiciel.
Il complète `PROJECT.md` (vision, architecture) et `CODING_RULES.md` (règles de développement).

---

## Principe général

Un contrat complet doit pouvoir être créé en moins de deux minutes.

Toute règle métier ci-dessous existe pour éliminer la ressaisie et éviter les erreurs
dans les documents légaux générés (DOCX / PDF), pas pour ajouter de la complexité.

---

## Artistes

- Un artiste est identifié par un nom légal et/ou un nom de scène : au moins l'un des
  deux est obligatoire.
- Le cachet (`fee`) saisi sur la fiche artiste est un **cachet habituel**, pas un
  montant figé : il sert uniquement de valeur par défaut lors de la création d'un
  contrat et reste toujours modifiable au cas par cas.
- Les informations légales et bancaires (adresse, SIREN, SIRET, code APE, licence,
  IBAN, BIC, numéro de sécurité sociale) sont conservées sur la fiche artiste et
  réutilisées automatiquement dans chaque nouveau contrat.
- La suppression d'un artiste ne supprime pas les contrats déjà générés : la fiche
  artiste est une source de pré-remplissage, pas une dépendance bloquante.

---

## Organisateurs

- Un organisateur est identifié par un nom (`name`) : obligatoire.
- La fiche organisateur porte les informations légales et de contact (forme
  juridique, adresse, SIRET, code APE, licence, TVA intracommunautaire, IBAN, BIC,
  représentant, fonction, site internet, notes) réutilisées automatiquement dans
  chaque nouveau contrat.
- L'adresse enregistrée sur la fiche organisateur est **le siège social** de
  l'organisateur. Elle sert aux mentions légales du contrat, jamais à décrire le
  lieu où se déroule la prestation (voir règle dédiée ci-dessous).

---

## Contrats

### Numérotation

- Chaque contrat reçoit un numéro unique au format `YGNT-{année}-{séquence sur 4
  chiffres}` (ex. `YGNT-2026-0001`).
- La séquence repart implicitement par année et se base sur le dernier numéro
  attribué pour l'année en cours : elle n'est jamais recalculée à partir du nombre
  total de contrats, pour rester correcte même après suppression d'un contrat.
- Le numéro est attribué automatiquement à la création et n'est plus modifiable
  ensuite.

### Champs obligatoires

- L'organisateur (structure) et le nom du spectacle sont les deux seules
  informations strictement obligatoires pour enregistrer un contrat.
- Toutes les autres informations (artiste, prestation, conditions financières)
  peuvent être complétées plus tard ; le contrat reste un brouillon modifiable.

### Artiste et organisateur liés au contrat

- Un contrat peut être rattaché à une fiche Artiste (`artist_id`) et à une fiche
  Organisateur (`organization_id`) réellement enregistrées comme clés étrangères.
- Sélectionner un artiste ou un organisateur dans le dialogue de contrat déclenche
  le pré-remplissage automatique de tous les champs correspondants. L'utilisateur
  garde la main : toute valeur pré-remplie reste modifiable avant enregistrement.
- Le contrat conserve une copie figée (« instantané ») des informations
  organisateur et artiste au moment de sa création/modification, même si la fiche
  d'origine change ensuite : un contrat déjà généré ne doit jamais changer de
  contenu rétroactivement parce qu'une fiche a été modifiée.

### Lieu de la prestation

- Le lieu de la prestation (nom de la salle, adresse, code postal, ville) est
  **strictement distinct** de l'adresse du siège social de l'organisateur.
- L'article « Objet » du contrat généré doit toujours utiliser les champs de
  prestation (`prestation_lieu`, `prestation_adresse`, `prestation_postal_code`,
  `prestation_city`), jamais l'adresse de l'organisateur.
- Si seule une partie de ces informations est renseignée, les parties vides sont
  simplement omises (pas de virgules ni d'espaces parasites dans le document
  généré).

### Statuts

- Un contrat a toujours l'un des trois statuts suivants : Brouillon (`draft`,
  valeur par défaut), Validé (`validated`), Signé (`signed`).
- Le statut est informatif : il ne bloque aucune action (génération, export,
  modification restent possibles quel que soit le statut).

### Conditions financières

- Le cachet (`cession_montant`) est initialisé avec le cachet habituel de
  l'artiste sélectionné, mais reste modifiable pour chaque contrat.
- Un acompte, un taux de TVA, un mode de paiement (Virement / Chèque) et une
  échéance de règlement peuvent être précisés par contrat ; aucun de ces champs
  n'est obligatoire.

### Duplication d'un contrat

- Dupliquer un contrat crée un nouveau contrat en Brouillon, avec un nouveau
  numéro, sans document DOCX/PDF déjà généré : la duplication sert à repartir
  d'un modèle, jamais à créer une copie conforme d'un document déjà émis.

### Historique

- Toute action significative sur un contrat (création, modification,
  duplication, génération DOCX, export PDF, ouverture d'un document) est tracée
  dans un historique daté, consultable depuis la fiche du contrat.

---

## Génération de documents

### DOCX

- Le DOCX est **toujours** généré à partir du template unique
  `templates/contrat_cession.docx` et des données du contrat.
- La génération DOCX ne doit jamais être cassée par une évolution ultérieure du
  logiciel : c'est la fonctionnalité la plus critique de l'application.
- Le fichier généré est nommé selon le format :
  `{numéro de contrat} - {date de prestation} - {organisateur} - {spectacle}.docx`
  et déposé dans `exports/`.

### PDF

- Le PDF n'est jamais reconstruit indépendamment du DOCX : il est **toujours**
  généré en convertissant le DOCX via Microsoft Word (automatisation COM), afin de
  garantir une mise en page strictement identique entre les deux formats.
- Si Microsoft Word n'est pas installé ou ne peut pas démarrer, l'export PDF
  échoue explicitement (message clair) plutôt que de produire un document dégradé.
- Le fichier PDF porte le même nom que le DOCX correspondant (extension différente).

### Ouverture des documents

- Les boutons « Ouvrir DOCX » et « Ouvrir PDF » ne sont actifs que si le fichier
  correspondant existe réellement sur le disque.

---

## Intégrité des données

- Toute la base utilise une connexion SQLite unique et partagée (singleton).
- Toute logique métier passe par un Service ; seuls les Repositories exécutent du
  SQL. Aucune fenêtre ne doit accéder directement à la base.
- Les évolutions de schéma sont toujours additives et rétrocompatibles (nouvelles
  colonnes nullables) : un contrat créé avant une évolution reste lisible et
  générable après.

---

## Interface

- Chaque module de gestion (Artistes, Organisateurs, Contrats) propose la même
  présentation : recherche, tableau, double-clic pour modifier, boutons Nouveau /
  Modifier / Supprimer / Actualiser.
- Le dialogue de création/modification d'un contrat mémorise sa taille de fenêtre
  d'une ouverture à l'autre et reste utilisable sur un écran Full HD.
