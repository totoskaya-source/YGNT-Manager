# YGNT Manager — BUGS.md

## Version en préparation

**v1.0.3**

## Bugs ouverts

### 🔴 Critiques
Bugs empêchant l'utilisation du logiciel ou pouvant provoquer une perte de données.

Aucun.

### 🟠 Majeurs
Fonctionnalités importantes ne fonctionnant pas correctement.

Aucun.

### 🟡 Mineurs
Défauts d'affichage, ergonomie ou comportements non bloquants.

Aucun.

## Corrections intégrées dans la v1.0.3

- Correction du blocage d'enregistrement d'une facture créée depuis une prestation (contrainte de clé étrangère `factures.formation_id` incorrecte depuis l'introduction des Formations).
- Correction de la génération de Devis/Facture depuis une prestation liée à une Formation (champs producteur/formation restaient vides).
- Correction du bouton "+ Ajouter la formation de la prestation" du CDDU, incompatible avec les prestations liées à une Formation.
- Ajout du bouton "Créer un CDDU" sur l'écran Prestations.
- Correction de l'oubli de la qualification de l'artiste dans le document CDDU généré.
- Correction de l'oubli du prénom de l'artiste dans le document CDDU généré (le nom de famille seul apparaissait).
- Correction du point orphelin dans la clause "agissant en qualité de" du CDDU lorsque la fonction du représentant du producteur n'est pas renseignée.
- Finition rédactionnelle du document CDDU : reformulation de l'article OBJET, affichage de l'instrument principal, aération du bloc identité, espacement avant les articles.
- Rendu obligatoire le champ Qualification sur la fiche Artiste (plus de valeur par défaut).
- Ajout d'astérisques rouges sur les champs obligatoires dans les dialogues concernés.

## Tests de validation avant publication

### Général
- [ ] Lancement du logiciel
- [ ] Création de la base de données
- [ ] Ouverture d'une base existante
- [ ] Sauvegarde
- [ ] Restauration

### Producteurs
- [ ] Création
- [ ] Modification
- [ ] Suppression
- [ ] Recherche

### Organisateurs
- [ ] Création
- [ ] Modification
- [ ] Suppression
- [ ] Recherche

### Artistes
- [ ] Création
- [ ] Modification
- [ ] Suppression
- [ ] Recherche

### Formations
- [ ] Création
- [ ] Modification
- [ ] Suppression

### Prestations
- [ ] Création
- [ ] Modification
- [ ] Suppression

### Devis
- [ ] Génération DOCX
- [ ] Génération PDF

### Contrats
- [ ] Génération DOCX
- [ ] Génération PDF

### CDDU
- [ ] Génération DOCX
- [ ] Génération PDF

### Factures
- [ ] Création
- [ ] PDF

### Paiements
- [ ] Création
- [ ] Modification

## Améliorations prévues (v1.1)

- Ergonomie
- Optimisations de performances
- Nouvelles fonctionnalités mineures

## Préparation de la version Web (v2.0)

- Séparation Interface / Métier
- API
- Authentification
- Base de données multi-utilisateur
- Synchronisation
- Hébergement
