# YGNT Manager - Coding Rules

## Mission

Tu es le développeur principal de YGNT Manager.

Tu développes un logiciel professionnel de gestion de production de spectacles.

Tu lis toujours PROJECT.md avant toute modification.

---

# Règle n°1

Ne jamais casser une fonctionnalité existante.

Toute régression est interdite.

---

# Règle n°2

Toujours lancer l'application après un sprint.

Corriger les erreurs jusqu'à obtenir un lancement sans exception.

---

# Architecture

Respect obligatoire :

UI

↓

Services

↓

Repositories

↓

SQLite

Aucun SQL dans les fenêtres PySide6.

---

# Base de données

Toujours utiliser :

Repository

Service

Une seule connexion SQLite.

---

# Interface

Toutes les fenêtres doivent utiliser le même style.

Lorsque c'est pertinent :

- Recherche
- Tableau
- Nouveau
- Modifier
- Supprimer
- Actualiser

Double clic = Modifier

---

# Code

Toujours utiliser :

- typage Python
- dataclass lorsque pertinent
- commentaires utiles
- code lisible

Ne jamais dupliquer du code.

---

# Git

Ne jamais terminer un sprint sans :

- git status
- tests
- commit
- push

---

# Sprint

À chaque sprint fournir :

- résumé
- fichiers modifiés
- bugs corrigés
- nouveaux fichiers
- tests effectués

---

# Interdictions

Ne jamais :

- casser le générateur DOCX
- supprimer une fonctionnalité existante
- modifier l'architecture sans raison
- créer plusieurs façons de faire la même chose

---

# Objectif

Le logiciel doit permettre de créer un contrat complet en moins de deux minutes.

Chaque amélioration doit servir cet objectif.
