> ⚠️ **BROUILLON DE TRAVAIL — NON VALIDÉ**
> Ce document n'a pas de valeur normative. Aucun contenu ci-dessous
> (périmètre, décisions, entités) ne doit être considéré comme validé tant
> qu'il n'a pas été repris explicitement dans un document SDS numéroté
> (`00_PRODUCT_VISION.md`, `01_PRODUCT_PRINCIPLES.md`,
> `02_DOMAIN_MODEL.md`...). **En cas de contradiction, les documents SDS
> prévalent toujours sur ce brouillon.**

---

# PROJECT CHARTER
## YGNT Manager Web

**Version :** 1.0 (Draft)  
**Statut :** En cours de conception  
**Sprint :** Sprint 0

---

# 1. Présentation

YGNT Manager Web est un nouveau produit développé à partir de l'expérience acquise avec YGNT Manager Desktop.

Il ne s'agit pas d'un portage du Desktop mais d'une plateforme Web moderne, collaborative et évolutive destinée aux producteurs de spectacles.

---

# 2. Objectifs

Le projet a pour objectifs de :

- Centraliser toute la gestion d'une production de spectacles.
- Réduire les doubles saisies.
- Automatiser les tâches répétitives.
- Garantir la cohérence des données.
- Permettre le travail collaboratif.
- Préparer les évolutions futures du logiciel.

---

# 3. Périmètre

Version 1.0 :

- Dashboard
- Utilisateurs
- Producteurs
- Organisateurs
- Artistes
- Formations
- Prestations
- Contrats
- CDDU
- Devis
- Factures
- Paiements
- Documents
- Paramètres

Hors périmètre initial :

- Comptabilité complète
- Billetterie
- CRM
- Application mobile
- API publique
- Intelligence artificielle
- Signature électronique

Ces fonctionnalités pourront être ajoutées ultérieurement.

---

# 4. Principes fondamentaux

## Desktop

Le Desktop reste un produit indépendant.

Son développement continue.

Le Web ne doit jamais remettre en cause le fonctionnement du Desktop.

---

## Architecture

Le Web est développé comme un nouveau produit.

Aucune interface Desktop n'est copiée.

Les règles métier sont réutilisées lorsqu'elles restent pertinentes.

---

## Documentation

Toute décision importante doit être documentée.

Aucune règle métier ne doit exister uniquement dans les conversations.

---

## Développement

Aucune fonctionnalité ne sera développée sans validation préalable de son architecture.

Chaque sprint devra être validé avant le suivant.

---

# 5. Philosophie

YGNT Manager Web doit respecter les principes suivants :

- simplicité
- cohérence
- rapidité
- automatisation
- sécurité
- évolutivité
- maintenabilité

---

# 6. Méthode de développement

Le projet suit une méthode itérative par sprints.

Chaque sprint comprend :

1. Analyse
2. Conception
3. Validation
4. Développement
5. Tests
6. Documentation
7. Livraison

---

# 7. Règles de développement

Le code doit respecter les principes suivants :

- Architecture claire
- Responsabilités séparées
- Documentation obligatoire
- Tests lorsque nécessaire
- Nommage cohérent
- Aucun code dupliqué
- Évolutivité prioritaire

---

# 8. Décisions déjà validées

Les décisions suivantes sont considérées comme validées :

- Le Desktop reste indépendant.
- Le Web est un nouveau produit.
- Les règles métier sont réutilisées lorsque cela est pertinent.
- Une prestation sera rattachée à une Formation.
- Une Formation pourra contenir un seul artiste ou plusieurs.
- Les améliorations identifiées sur le Desktop devront être intégrées au Web lorsqu'elles améliorent l'architecture.
- Un CDDU devra pouvoir regrouper plusieurs prestations.

---

# 9. Définition de "Terminé"

Une fonctionnalité est considérée comme terminée lorsque :

- son architecture est validée ;
- son développement est terminé ;
- les tests sont validés ;
- la documentation est à jour ;
- elle est intégrée sans régression.

---

# 10. Vision long terme

YGNT Manager Web a vocation à devenir une plateforme complète de gestion des producteurs de spectacles.

L'architecture devra permettre d'ajouter de nouveaux modules sans remise en cause des modules existants.
