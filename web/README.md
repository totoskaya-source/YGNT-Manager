# YGNT Manager Web

Nouveau produit SaaS multi-tenant pour les producteurs de spectacles.
Cohabite dans ce dépôt avec le Desktop existant (`app/`), sans en dépendre.

Documentation de conception (Sprint 0) : voir [`docs/`](docs/).
Planification du sprint en cours : voir [`SPRINT_001.md`](SPRINT_001.md).

## Structure du projet

```
web/
├── backend/        Couches API, Services métier, Accès aux données, Stockage
│   ├── ygnt_web/
│   │   ├── api/            Couche API (routes, aucune règle métier)
│   │   ├── services/       Couche Services métier
│   │   ├── repositories/   Couche Accès aux données
│   │   ├── storage/        Couche Stockage
│   │   ├── core/           Configuration
│   │   └── main.py         Point d'entrée de l'application
│   └── tests/
│       ├── unit/
│       └── integration/
├── frontend/       Couche Frontend (statique pour l'instant, aucune règle métier)
│   ├── index.html
│   ├── assets/
│   └── tests/
└── docs/           Documents de conception (Sprint 0)
```

## Prérequis

- Python 3.11+ (le `.venv` existant à la racine du dépôt convient : il
  contient déjà `fastapi` et `uvicorn` aux versions utilisées ici).

## Lancer le projet en local

```bash
cd web/backend
pip install -r requirements-dev.txt   # une seule fois, ou après une venv dédiée
uvicorn ygnt_web.main:app --reload
```

Ouvrir http://127.0.0.1:8000/ dans un navigateur : la page affiche l'état du
backend (`Backend : ok`), obtenu via l'appel à `GET /health`.

## Lancer les tests

```bash
cd web/backend
pytest
```
