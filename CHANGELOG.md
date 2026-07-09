# Journal des versions — YGNT Manager

Toutes les évolutions notables du logiciel sont consignées ici, par version.

---

## v0.6.5 — Professionnalisation de l'application

- Affichage de la version dans le titre de la fenêtre et la barre de statut.
- Boîte de dialogue « À propos... » (nom du logiciel, version, auteur, copyright), accessible depuis Paramètres.
- Uniformisation des boîtes de confirmation de suppression (Formations, Organisateurs, Prestations, Devis, Contrats) via un composant partagé unique.
- Sauvegarde automatique de la base SQLite au démarrage (`backup/`), conservation des 10 sauvegardes les plus récentes.

## v0.6 — Module Devis et Dossier de prestation

- Fondations du module Devis (modèle, migration, repository, service) sur le même socle que Contrats.
- Interface Devis : liste, dialogue à onglets (Général, Formation, Organisateur, Prestation, Conditions financières, Aperçu).
- Génération DOCX puis export PDF des Devis, réutilisant le même moteur de placeholders et le même convertisseur PDF que les Contrats.
- Création d'un Devis pré-rempli depuis une Prestation.
- Transformation d'un Devis accepté en Contrat (nouveau document indépendant, le Devis n'est jamais modifié).
- Onglet « Dossier » sur la fiche Prestation : consultation des Devis et Contrats rattachés (référence, statut, date), navigation directe vers les documents.

## v0.5 — Producteur, Formations et architecture métier

- Nouvelle entité Producteur (informations légales, bancaires, logo) avec instantané figé sur chaque Contrat, comme pour l'Organisateur.
- Template DOCX du Contrat entièrement dynamique : plus aucune information Producteur codée en dur.
- Renommage du module Artistes en Formations dans toute l'interface.
- Suppression définitive du cachet habituel de la Formation : le montant se saisit désormais uniquement sur la Prestation ou le Contrat.
- Ajout de champs marketing/informatifs sur la Formation (style musical, description, logo, réseaux sociaux).

## v0.4 et antérieures

- Module Contrats : numérotation automatique, dialogue à onglets, génération DOCX, export PDF fidèle (conversion via Microsoft Word), historique par contrat.
- Modules Artistes et Organisateurs (CRUD complet).
- Module Prestations : pivot central reliant Formation, Organisateur, lieu et dates ; création de contrat pré-rempli depuis une prestation.
