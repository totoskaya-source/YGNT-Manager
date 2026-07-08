# YGNT Manager

Version : 0.4
Projet : Logiciel de gestion pour une association/producteur de spectacles.

---

# Vision

YGNT Manager doit devenir un logiciel professionnel permettant de gérer toute l'activité d'un producteur de spectacles.

L'objectif principal est de gagner un maximum de temps sur la création des contrats, devis, factures et la gestion des artistes.

Chaque fonctionnalité doit privilégier :

- la rapidité
- la simplicité
- la fiabilité

Le logiciel est développé d'abord pour un usage réel, puis pourra être distribué.

---

# Stack technique

- Python 3.14
- PySide6
- SQLite
- python-docx
- ReportLab (PDF)
- Git
- GitHub

---

# Architecture

Le projet suit une architecture en couches.

UI
↓

Services

↓

Repositories

↓

Database SQLite

Les fenêtres PySide6 ne doivent jamais exécuter directement de SQL.

Toute logique métier passe par les Services.

Les Repositories sont les seuls autorisés à accéder à SQLite.

---

# Principes

Toujours conserver un code simple.

Toujours privilégier la lisibilité.

Éviter les duplications.

Une seule responsabilité par classe.

Une seule connexion SQLite.

Typage Python obligatoire.

---

# Interface

Toutes les fenêtres doivent avoir une présentation homogène.

Lorsque c'est pertinent :

- barre de recherche
- tableau
- double clic pour modifier
- bouton Nouveau
- bouton Modifier
- bouton Supprimer
- bouton Actualiser

Le style graphique doit rester cohérent dans tout le logiciel.

---

# Modules

Le logiciel est organisé en modules.

Modules actuels :

- Dashboard
- Artistes
- Contrats

Modules prévus :

- Organisateurs
- Devis
- Factures
- Paiements
- Agenda
- Documents
- Paramètres
- Statistiques

---

# Priorité actuelle

La priorité absolue est le module Contrats.

Les contrats doivent être générés rapidement et sans erreur.

La génération DOCX existante doit toujours rester compatible.

Le PDF doit être généré correctement.

---

# Tests

À la fin de chaque sprint :

- lancer l'application
- vérifier que le logiciel démarre
- tester les fonctionnalités développées
- corriger les erreurs avant de terminer

Un sprint n'est jamais terminé tant que les tests ne sont pas validés.

---

# Git

À la fin de chaque sprint :

git status

git add .

git commit

git push

Le dépôt GitHub doit toujours refléter une version fonctionnelle.

---

# Philosophie

Chaque amélioration doit apporter un vrai gain de temps.

La simplicité est plus importante que le nombre de fonctionnalités.

Un utilisateur doit pouvoir créer un contrat complet en moins de deux minutes.

Chaque décision technique doit servir cet objectif.
