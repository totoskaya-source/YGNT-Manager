# Journal des versions — YGNT Manager

Toutes les évolutions notables du logiciel sont consignées ici, par version.

---

## v1.0.0 — Packaging et finalisation

- Empaquetage de l'application pour distribution : script PyInstaller (`ygnt_manager.spec`, build onedir) et installateur Windows via Inno Setup (`ygnt_manager_setup.iss`), installation par utilisateur sans élévation UAC.
- Résolution des chemins compatible exécutable packagé (`app/paths.py`) : base de données, exports et sauvegardes toujours créés à côté de l'exécutable.
- Tâches longues (génération de documents, conversion PDF) exécutées en arrière-plan avec indicateur de progression (`app/ui/background_task.py`), interface non bloquante.
- Nouveau module Intermittent / Paie (`app/ui/intermipaie_dialog.py`).
- Conversion PDF via Microsoft Word fiabilisée : détection d'indisponibilité de Word, délai maximal configurable, nettoyage systématique des instances orphelines.
- Moteur de placeholders (`PlaceholderEngine`) enrichi : suppression automatique des lignes dont tous les placeholders sont vides, pour des documents toujours propres quelles que soient les informations renseignées.
- Corrections de recette finale :
  - Calendrier des champs Date (`QDateEdit`) : le popup s'affichait tronqué (numéros et abréviations de jours coupés) à cause du thème de l'application ; il affiche désormais toujours le mois complet, sur tous les dialogues concernés.
  - Contrat, organisateur particulier : le libellé « Structure » s'affichait à tort pour une personne physique ; distinction automatique Structure / Nom et prénom selon la présence d'un SIRET, d'une TVA intracommunautaire, d'une licence ou d'une forme juridique.
  - Contrat, bloc Organisateur : suppression des espaces verticaux résiduels quand plusieurs champs sont absents (SIRET, Représentée par, Fonction...) ; ajout des lignes Téléphone et Email (déjà saisies mais jamais affichées) ; l'Adresse reste toujours affichée si renseignée, y compris pour un particulier.
  - Devis et Facture : mêmes corrections de lignes conditionnelles pour le bloc Organisateur (plus de ligne « Représenté par ,  » orpheline lorsqu'un seul des deux champs est renseigné).

## v0.9.3 — Identité graphique unifiée des documents

- Refonte graphique des gabarits DOCX (Contrat, Devis, Facture) : mise en page et identité visuelle unifiées entre les trois documents.

## v0.9.2 — Dashboard et statistiques

- Nouveau module Statistiques (`app/services/stats_helper.py`, `app/ui/statistiques.py`) : indicateurs d'activité consultables depuis l'application.
- Intégration des statistiques au tableau de bord.

## v0.9.1 — Dashboard et expérience utilisateur

- Nouveau tableau de bord (`app/ui/dashboard.py`) : écran d'accueil avec message de bienvenue et indicateurs clés.

## v0.9.0 — Workflow documentaire finalisé

- Génération de documents (Contrats, Devis, Factures) directement depuis les listes, via un dialogue de confirmation partagé (`app/ui/dialogs.py`), sans repasser par la fiche complète.
- Simplification et harmonisation des actions de génération sur les écrans Contrats, Devis, Factures et Prestations.

## v0.8.0 — Workflow métier complet

- Nouveau module Paiements (modèle, migration, repository, service, dialogue, liste) rattaché aux Factures : suivi des règlements reçus.
- Mise à jour du modèle Facture pour refléter l'état des paiements associés.

## v0.7.0 — Module Factures terminé

- Nouveau module Factures complet (modèle, migration, repository, service, dialogue à onglets, liste) sur le même socle que Contrats et Devis.
- Génération de Facture depuis un Contrat ou une Prestation, génération DOCX et export PDF.
- Correction : remplacement de la date de paiement statique du Contrat par les modalités de paiement réellement saisies.

## v0.6.6 — Refonte graphique et thème centralisé

- Nouveau theme Qt centralisé (`app/ui/theme.py`) : palette, typographie et styles communs appliqués à toute l'application, plus aucun style codé en dur dans les fenêtres.
- Harmonisation visuelle des dialogues Artiste, Organisation et Producteur, et de la fenêtre principale.

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
