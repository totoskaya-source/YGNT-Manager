# IDEAS V1.1

Backlog produit de YGNT Manager. Ce document liste des **idées**
d'amélioration, pas des tâches techniques : il ne contient aucun code, aucun
TODO d'implémentation, aucun détail de fichier ou de fonction.

Il est volontairement séparé de `ROADMAP.md` (engagements de version) et de
`BUGS.md` (défauts) : aucune idée listée ici n'est obligatoire pour une
version donnée. Une idée passe de ce backlog à la roadmap lorsqu'elle est
retenue pour un sprint.

Statuts possibles pour chaque idée : **À étudier**, **Validé**,
**Développé**, **Reporté**, **Abandonné**.

---

## P1 - Priorité haute

*(impact fort sur le travail quotidien)*

### Dashboard orienté actions

- **Description** : faire du Dashboard le point d'entrée qui montre
  immédiatement ce qui demande une action (factures en retard, devis à
  relancer, prestations sans facture, CDDU à préparer, documents non
  générés), plutôt qu'un simple récapitulatif de chiffres.
- **Valeur utilisateur** : le producteur sait en un coup d'œil ce qu'il doit
  traiter aujourd'hui, sans repasser module par module.
- **Impact technique estimé** : moyen — calculs ajoutés à
  `app/services/stats_helper.py`, Dashboard existant enrichi, aucun nouveau
  service, aucune autre page touchée.
- **Statut** : Développé (bloc "À traiter" + bloc "Documents" livrés,
  Situation financière recentrée sur CA du mois/annuel ; en recette
  utilisateur avant intégration définitive sur `v1.1-web`).

### Bouton Dupliquer

- **Description** : permettre de dupliquer un enregistrement existant
  (Prestation, Devis, Contrat, Facture) comme point de départ d'un nouveau,
  pour éviter de ressaisir des informations proches d'un cas déjà traité.
- **Valeur utilisateur** : gain de temps important sur les prestations
  récurrentes (même artiste, même type de cachet, organisateur différent).
- **Impact technique estimé** : faible à moyen — la couche Service des
  Contrats dispose déjà d'une duplication ; l'idée est de vérifier sa
  disposition dans l'interface et de généraliser le même principe aux
  autres modules.
- **Statut** : À étudier.

### Ouvrir le dossier des documents

- **Description** : un bouton qui ouvre directement, dans l'explorateur de
  fichiers, le dossier contenant les documents générés (DOCX/PDF) d'un
  dossier (prestation, devis, contrat, facture, CDDU).
- **Valeur utilisateur** : évite de chercher manuellement un fichier
  généré parmi tous les exports.
- **Impact technique estimé** : faible — chaque module sait déjà ouvrir un
  document précis ; il s'agit d'ouvrir son dossier parent plutôt qu'un
  fichier unique.
- **Statut** : À étudier.

### Générer puis ouvrir un document

- **Description** : enchaîner automatiquement la génération d'un document
  (DOCX ou PDF) et son ouverture, au lieu de deux actions manuelles
  séparées.
- **Valeur utilisateur** : un contrat complet généré et vérifié en un seul
  geste, cohérent avec l'objectif "moins de deux minutes" de
  `PROJECT.md`.
- **Impact technique estimé** : faible — les deux actions existent déjà
  séparément dans chaque Service ; il s'agit de les enchaîner côté
  interface.
- **Statut** : À étudier.

---

## P2 - Priorité moyenne

*(améliorations importantes mais non urgentes)*

### Préremplissage intelligent

- **Description** : pré-remplir davantage de champs à partir de l'historique
  (dernier cachet pratiqué avec un artiste, dernier lieu utilisé par un
  organisateur, conditions habituelles) plutôt que de ne pré-remplir que
  les coordonnées.
- **Valeur utilisateur** : moins de ressaisie sur les dossiers similaires à
  un précédent.
- **Impact technique estimé** : moyen — nécessite d'identifier une règle de
  sélection fiable (dernier enregistrement ? le plus fréquent ?) avant tout
  développement.
- **Statut** : À étudier.

### Amélioration des actions rapides

- **Description** : revoir les actions rapides du Dashboard (aujourd'hui
  un bouton de création par module) pour les rendre plus contextuelles,
  par exemple en fonction de ce qui ressort du bloc "À traiter".
- **Valeur utilisateur** : les actions proposées correspondent mieux à ce
  qu'il y a réellement à faire.
- **Impact technique estimé** : faible à moyen — dépend du degré de
  contextualisation souhaité.
- **Statut** : À étudier.

### Rester dans le dialogue après génération (Devis/Contrat/Facture)

- **Description** : après la création d'un enregistrement, rester dans le
  dialogue pour générer immédiatement le DOCX/PDF sans avoir à rouvrir la
  fiche.
- **Valeur utilisateur** : un flux de création continu, sans étape
  intermédiaire.
- **Impact technique estimé** : faible — déjà en place pour les Devis
  (Sprint 12.0) ; à confirmer/généraliser pour les Contrats et les
  Factures.
- **Statut** : À étudier (partiellement développé pour les Devis).

### Refonte graphique des modèles de documents

- **Description** : refonte graphique complète des modèles Devis, Contrats
  et Factures, avec une charte graphique uniforme sur tous les documents,
  inspirée d'une facture professionnelle moderne (mise en page élégante,
  tableaux, totaux, blocs d'informations). Le logo actuel YGNT Production
  est conservé.
- **Valeur utilisateur** : une image plus professionnelle auprès des
  organisateurs et artistes.
- **Impact technique estimé** : élevé — travail de conception graphique et
  reprise des templates DOCX existants (`templates/*.docx`), sans changer
  le moteur de génération.
- **Statut** : À étudier.

### Prévisualisation DOCX/PDF

- **Description** : afficher un véritable aperçu visuel du document avant
  génération, au-delà du résumé texte déjà proposé dans chaque module.
- **Valeur utilisateur** : vérifier le rendu avant de produire le fichier
  final.
- **Impact technique estimé** : moyen à élevé — nécessite un rendu visuel
  du DOCX, absent aujourd'hui (seul un résumé texte existe).
- **Statut** : À étudier.

### Suivi des contrats en cours

- **Description** : une vue dédiée distinguant les contrats encore en
  brouillon/validation de ceux réellement signés.
- **Valeur utilisateur** : mieux piloter les dossiers en attente de
  signature.
- **Impact technique estimé** : faible — répartition par statut déjà
  disponible pour les Factures et les Devis sur la page Statistiques, à
  étendre aux Contrats.
- **Statut** : À étudier.

### Statistiques mensuelles et annuelles détaillées

- **Description** : au-delà du chiffre d'affaires du mois/de l'année déjà
  disponible sur le Dashboard, une vue détaillée par période (nombre de
  prestations, taux de transformation devis → contrat, etc.).
- **Valeur utilisateur** : suivre l'activité dans le temps, pas seulement
  en cumul global.
- **Impact technique estimé** : moyen — calculs supplémentaires sur les
  listes déjà chargées par le Dashboard/la page Statistiques.
- **Statut** : À étudier.

### Répartition des clients

- **Description** : vue de la répartition de l'activité par organisateur
  (au-delà du classement par nombre de prestations déjà disponible),
  notamment en chiffre d'affaires.
- **Valeur utilisateur** : identifier les clients les plus importants.
- **Impact technique estimé** : faible — extension du classement
  "Top organisateurs" déjà existant.
- **Statut** : À étudier.

### Prestations par période

- **Description** : filtrer et consulter les prestations sur une période
  personnalisée (mois, année, plage de dates au choix).
- **Valeur utilisateur** : retrouver rapidement l'activité d'une période
  donnée, notamment en fin d'année ou lors d'un bilan.
- **Impact technique estimé** : moyen — nécessite un filtrage par date en
  plus des listes complètes actuellement chargées.
- **Statut** : À étudier.

### Menu Outils (calculs métier)

- **Description** : un menu "Outils" regroupant des calculs utiles à la
  production de spectacles : ouverture directe du simulateur IntermiPaie,
  préparation des cachets avant son utilisation, répartition des cachets,
  calcul HT ↔ TTC, calcul des frais kilométriques. Le moteur de calcul
  d'IntermiPaie ne doit jamais être reproduit sans source officielle ; si
  une API officielle existe un jour, son intégration sera à prévoir.
- **Valeur utilisateur** : centraliser des calculs aujourd'hui faits en
  dehors du logiciel.
- **Impact technique estimé** : moyen — plusieurs petits outils
  indépendants, sans impact sur les modules existants.
- **Statut** : À étudier.

---

## P3 - Confort

*(idées intéressantes mais pouvant attendre)*

### Personnalisation du Dashboard

- **Description** : permettre de réordonner ou masquer les blocs du
  Dashboard selon les préférences de l'utilisateur.
- **Valeur utilisateur** : un Dashboard adapté à la façon de travailler de
  chacun.
- **Impact technique estimé** : moyen — nécessite de mémoriser une
  configuration utilisateur, aujourd'hui inexistante.
- **Statut** : À étudier.

### Raccourcis clavier

- **Description** : raccourcis clavier pour les actions les plus
  fréquentes (nouveau, enregistrer, rechercher...).
- **Valeur utilisateur** : plus rapide pour un usage intensif au clavier.
- **Impact technique estimé** : faible.
- **Statut** : À étudier.

### Amélioration des messages de confirmation

- **Description** : rendre les messages de confirmation (suppression,
  enregistrement, erreurs) plus clairs et plus homogènes dans toute
  l'application.
- **Valeur utilisateur** : moins d'ambiguïté sur ce qui vient de se passer.
- **Impact technique estimé** : faible.
- **Statut** : À étudier.

### Ouverture plus fluide des documents

- **Description** : améliorer la fiabilité et la rapidité d'ouverture des
  documents déjà générés (au-delà du cas "générer puis ouvrir").
- **Valeur utilisateur** : moins d'attente et moins d'erreurs à
  l'ouverture.
- **Impact technique estimé** : faible à moyen.
- **Statut** : À étudier.

### Historique des générations

- **Description** : une vue unifiée de l'historique de génération des
  documents, tous modules confondus (aujourd'hui, l'historique existe par
  module - Contrats, CDDU - mais pas de vue transversale).
- **Valeur utilisateur** : retracer facilement qui a généré quoi et quand.
- **Impact technique estimé** : moyen.
- **Statut** : À étudier.

### Export ZIP d'un dossier complet

- **Description** : exporter en une seule archive tous les documents liés à
  un dossier (devis, contrat, facture, CDDU d'une même prestation).
- **Valeur utilisateur** : partager facilement un dossier complet.
- **Impact technique estimé** : faible à moyen.
- **Statut** : À étudier.

### Icônes SVG

- **Description** : remplacer les éléments graphiques actuels par des
  icônes SVG dans l'interface.
- **Valeur utilisateur** : interface plus moderne.
- **Impact technique estimé** : faible.
- **Statut** : À étudier.

### Mode sombre

- **Description** : proposer un thème sombre en plus du thème actuel.
- **Valeur utilisateur** : confort visuel pour certains utilisateurs.
- **Impact technique estimé** : moyen — le thème est déjà centralisé dans
  `app/ui/theme.py`, ce qui facilite l'ajout d'une variante, à étudier plus
  précisément avant de s'engager.
- **Statut** : À étudier.

### Personnalisation du thème

- **Description** : au-delà du mode sombre, permettre d'ajuster certains
  éléments visuels (couleur d'accent, taille de police).
- **Valeur utilisateur** : adapter l'apparence aux préférences de chacun.
- **Impact technique estimé** : moyen.
- **Statut** : À étudier.

### Statistiques des paiements

- **Description** : statistiques dédiées aux paiements (délai moyen de
  règlement, répartition par mode de paiement).
- **Valeur utilisateur** : mieux anticiper la trésorerie.
- **Impact technique estimé** : faible à moyen.
- **Statut** : À étudier.

### Rubrique Ressources (liens utiles)

- **Description** : une rubrique regroupant des liens utiles au métier :
  IntermiPaie, GUSO, Audiens, SACEM, SACD, CNM, France Travail Spectacle,
  URSSAF, impots.gouv.
- **Valeur utilisateur** : un accès rapide aux services externes utilisés
  régulièrement.
- **Impact technique estimé** : faible.
- **Statut** : À étudier.

### Version Web / SaaS (réflexion globale)

- **Description** : réflexion d'ensemble sur une évolution vers une version
  Web/SaaS : synchronisation cloud, application Web, application mobile,
  API. Chantier distinct de la v1.1 desktop, avec ses propres prérequis
  techniques (authentification, base de données serveur, remplacement du
  pipeline PDF actuel dépendant de Microsoft Word).
- **Valeur utilisateur** : accès à distance et multi-utilisateur, hors
  portée d'un usage mono-poste actuel.
- **Impact technique estimé** : élevé — chantier à part entière, non
  compatible avec un développement en parallèle de la v1.1.
- **Statut** : Reporté.

### Intégration agendas externes (Google Agenda / Outlook)

- **Description** : synchroniser les prestations planifiées avec un agenda
  externe (Google Agenda, Outlook).
- **Valeur utilisateur** : retrouver les dates de prestations dans l'agenda
  personnel déjà utilisé au quotidien.
- **Impact technique estimé** : élevé — nécessite une intégration à une API
  tierce et une gestion d'authentification externe.
- **Statut** : Reporté.
