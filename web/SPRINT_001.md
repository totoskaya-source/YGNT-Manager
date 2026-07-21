# Sprint 001 — Préparer la base du projet YGNT Manager Web

Statut : **Proposition — en attente de validation**
Rédigé par : Lead Developer
Périmètre : ce document ne couvre que le Sprint 1. Aucune ligne de code n'a
été écrite au moment de sa rédaction. Aucun Sprint 2 n'est anticipé, même
partiellement : tout ce qui ne relève pas strictement de la base technique du
projet est renvoyé en fonctionnalité exclue (§3) sans autre précision sur son
contenu futur.

Base normative : l'ensemble des documents de cadrage Sprint 0
(`docs/00_PRODUCT_VISION.md` à `docs/06_ARCHITECTURE.md`), considérés comme
validés. Aucune règle métier, aucune entité et aucun principe n'est réinventé
ici : ce document découpe en tâches techniques ce qui a déjà été décidé,
il ne décide rien de nouveau sur le métier.

---

## Table des matières

1. [Objectif du sprint](#1-objectif-du-sprint)
2. [Fonctionnalités incluses](#2-fonctionnalités-incluses)
3. [Fonctionnalités explicitement exclues](#3-fonctionnalités-explicitement-exclues)
4. [Découpage en tâches techniques](#4-découpage-en-tâches-techniques)
5. [Ordre de développement](#5-ordre-de-développement)
6. [Critères de validation](#6-critères-de-validation)
7. [Définition du « Terminé »](#7-définition-du-terminé)
8. [Risques éventuels](#8-risques-éventuels)

---

## 1. Objectif du sprint

Poser les fondations techniques du projet Web, sans encore livrer de
fonctionnalité métier visible pour un producteur de spectacles.

À l'issue de ce sprint, le projet doit disposer :
- d'une structure de projet respectant les cinq couches déjà validées
  (`docs/06_ARCHITECTURE.md` §2 : Frontend, API, Services métier, Accès aux
  données, Stockage) ;
- d'un mécanisme de connexion et de session minimal, portant le contexte
  multi-tenant déjà validé (Société active, Utilisateur, Rôles —
  `docs/06_ARCHITECTURE.md` §4) ;
- d'une première preuve concrète que l'isolation multi-tenant fonctionne
  réellement, pas seulement sur le papier.

Ce sprint ne cherche à démontrer aucune valeur métier : il démontre que
l'architecture validée en Sprint 0 est réellement construisable telle que
décrite, et que les sprints suivants pourront s'appuyer dessus sans reprendre
les fondations.

---

## 2. Fonctionnalités incluses

Seules les trois entités « Plateforme » du modèle de données
(`docs/05_DATABASE.md` §2.1 à §2.3) sont concernées par ce sprint : Société,
Utilisateur, Rôle. Aucune autre entité n'est créée, même partiellement.

- **Structure de projet** — arborescence respectant la séparation des cinq
  couches (`docs/06_ARCHITECTURE.md` §2), sans mélange de responsabilités
  entre elles.
- **Gestion de la Société** — création d'une Société (espace de travail),
  strictement selon les attributs déjà définis (`docs/05_DATABASE.md` §2.1).
- **Gestion des Utilisateurs** — création d'un Utilisateur rattaché à une
  Société (`docs/05_DATABASE.md` §2.2), sans processus d'invitation avancé.
- **Gestion des Rôles** — existence d'au moins un Rôle par Société et
  affectation d'un Rôle à un Utilisateur (`docs/05_DATABASE.md` §2.3), sans
  éditeur de permissions fin.
- **Authentification et session** — connexion d'un Utilisateur, établissement
  du contexte courant (Utilisateur, Société active, Rôles), tel que décrit en
  `docs/06_ARCHITECTURE.md` §4.2 et §5.
- **Vérification d'autorisation minimale** — l'interface « vérifier une
  permission » du module Rôles (`docs/06_ARCHITECTURE.md` §3.4) existe et est
  appelable, même avec un contenu de permissions volontairement simple à ce
  stade.
- **Isolation multi-tenant démontrée** — la propagation du contexte à travers
  les cinq couches (`docs/06_ARCHITECTURE.md` §4.3) est effective et
  vérifiable, pas seulement déclarée.
- **Écran minimal** — un écran de connexion et un écran affichant le contexte
  de l'Utilisateur connecté (nom, Société active, Rôle), sans recherche de
  mise en forme graphique définitive (`docs/03_UX_ARCHITECTURE.md` reste hors
  périmètre de ce sprint pour tout le reste).
- **Socle de tests** — mise en place de la stratégie de tests déjà validée
  (`docs/06_ARCHITECTURE.md` §11), appliquée aux seuls Services développés
  dans ce sprint.
- **Documentation de démarrage** — un mode d'emploi permettant à un
  développeur de lancer le projet en local.

---

## 3. Fonctionnalités explicitement exclues

Tout ce qui suit reste dans le périmètre des sprints ultérieurs, sans que
leur contenu, leur ordre ou leur découpage soit préjugé ici :

- Prestation et Dossier de prestation.
- Organisateur, Contact.
- Artiste, Formation.
- Contrat, CDDU, Devis, Facture, Paiement.
- Document (généré ou déposé) et toute gestion documentaire.
- Cockpit et Tâches.
- Notifications.
- Recherche globale ou locale.
- Invitation d'Utilisateur avec envoi d'email, cycle de vie complet du compte
  (suspendu, désactivé...).
- Éditeur de Rôles et de permissions personnalisables par Société.
- Toute mise en forme graphique définitive, charte visuelle, ou travail
  d'ergonomie au-delà du strict nécessaire pour vérifier qu'une connexion
  fonctionne.
- Tout traitement asynchrone (`docs/06_ARCHITECTURE.md` §8) : aucune
  génération de document n'existe encore à ce stade.
- Déploiement en environnement de production ou mise en ligne publique.

---

## 4. Découpage en tâches techniques

| # | Tâche | Description |
|---|---|---|
| T1 | Initialiser la structure du projet | Créer l'arborescence du dossier `web/` reflétant les cinq couches déjà validées, sans qu'aucune couche n'en contienne une autre. |
| T2 | Mettre en place la configuration de base | Gestion des paramètres d'environnement (connexion au Stockage, secrets de session), sans valeur sensible en dur dans le projet. |
| T3 | Construire le Stockage initial | Traduire les trois entités Plateforme (`docs/05_DATABASE.md` §2.1-2.3) et leur relation N↔N Utilisateur↔Rôle en structure de persistance, conforme aux règles d'intégrité déjà validées (`docs/05_DATABASE.md` §5, notamment l'isolation multi-tenant). |
| T4 | Construire la couche Accès aux données | Un point d'accès par entité (Société, Utilisateur, Rôle), qui n'exécute jamais d'opération sans un contexte de Société explicite (`docs/06_ARCHITECTURE.md` §4.1). |
| T5 | Construire les Services métier Société / Utilisateurs / Rôles | Créer une Société, créer un Utilisateur rattaché, créer un Rôle, affecter un Rôle à un Utilisateur — en s'appuyant uniquement sur la couche Accès aux données (jamais directement sur le Stockage). |
| T6 | Construire le module Authentification | Connexion d'un Utilisateur, établissement du contexte courant (Utilisateur, Société active, Rôles) calculé côté serveur, jamais reçu du Frontend tel quel (`docs/06_ARCHITECTURE.md` §4.2, §4.4). |
| T7 | Construire l'interface de vérification de permission | Rendre appelable, depuis les autres Services, une vérification d'autorisation minimale associée au Rôle courant (`docs/06_ARCHITECTURE.md` §3.4, §5). |
| T8 | Construire la couche API minimale | Exposer uniquement : connexion, obtention du contexte courant, déconnexion — sans aucune règle métier propre à cette couche (`docs/06_ARCHITECTURE.md` §2). |
| T9 | Construire le Frontend minimal | Écran de connexion et écran affichant le contexte courant (Utilisateur, Société, Rôle), consommant uniquement l'API construite en T8. |
| T10 | Écrire les tests unitaires | Couvrir les Services construits en T5, T6 et T7, indépendamment du Frontend et du Stockage réel (`docs/06_ARCHITECTURE.md` §11). |
| T11 | Écrire un test d'intégration d'isolation multi-tenant | Démontrer explicitement qu'aucune donnée d'une Société n'est accessible depuis le contexte d'une autre Société, à travers les couches réellement construites (`docs/06_ARCHITECTURE.md` §11, §4.4). |
| T12 | Rédiger la documentation de démarrage | Mode d'emploi permettant à un développeur de lancer le projet en local à partir d'un dépôt propre, sans connaissance implicite non écrite. |

---

## 5. Ordre de développement

1. **T1** — Initialiser la structure du projet.
2. **T2** — Mettre en place la configuration de base.
3. **T3** — Construire le Stockage initial.
4. **T4** — Construire la couche Accès aux données.
5. **T5** — Construire les Services métier Société / Utilisateurs / Rôles
   *(T10, en partie, avance en parallèle dès que chaque Service est
   disponible)*.
6. **T6** — Construire le module Authentification.
7. **T7** — Construire l'interface de vérification de permission.
8. **T8** — Construire la couche API minimale.
9. **T9** — Construire le Frontend minimal.
10. **T11** — Écrire le test d'intégration d'isolation multi-tenant, dès que
    T4 à T8 sont en place.
11. **T10** (finalisation) — Compléter la couverture de tests unitaires
    manquante sur l'ensemble des Services du sprint.
12. **T12** — Rédiger la documentation de démarrage, une fois le projet
    réellement lançable de bout en bout.

Chaque tâche suppose la précédente terminée : aucune couche n'est construite
avant celle dont elle dépend (§1.1 de `docs/06_ARCHITECTURE.md`).

---

## 6. Critères de validation

Le sprint est considéré comme atteint si, et seulement si :

1. Un développeur n'ayant pas participé au sprint peut cloner le projet et le
   faire fonctionner en local en suivant uniquement la documentation produite
   en T12 — sans information orale complémentaire.
2. Une Société peut être créée, un Utilisateur peut y être rattaché, un Rôle
   peut lui être affecté, et cet Utilisateur peut se connecter.
3. Après connexion, le contexte courant (Utilisateur, Société active, Rôles)
   est visible et correct, aussi bien du point de vue du Frontend que du
   point de vue du serveur.
4. Le test d'intégration d'isolation multi-tenant (T11) échoue si l'isolation
   est contournée, et réussit dans l'implémentation livrée.
5. Aucune des cinq couches ne contourne celle qui la précède : en particulier,
   ni l'API ni le Frontend n'accèdent au Stockage autrement qu'en passant par
   les Services métier et l'Accès aux données.
6. Aucune fonctionnalité listée en §3 n'est présente, même de façon
   embryonnaire.
7. Aucun fichier du Desktop existant (`app/`, `app_old/`, et tout ce qui est
   hors `web/`) n'a été modifié par ce sprint.

---

## 7. Définition du « Terminé »

Une tâche du §4, ou le sprint dans son ensemble, n'est considérée comme
**Terminée** que si toutes les conditions suivantes sont réunies :

- Le code correspondant est écrit, relu (a minima par le Lead Developer) et
  intégré au projet.
- Les tests unitaires prévus (T10) pour la tâche concernée passent.
- Le test d'intégration d'isolation multi-tenant (T11) passe sur l'ensemble
  du périmètre déjà construit à ce stade du sprint.
- La tâche ne laisse aucune implémentation partielle silencieuse : une
  fonctionnalité incluse (§2) est soit complètement construite, soit non
  commencée — jamais à moitié.
- Aucune règle métier n'a été inventée pour combler un point non tranché en
  Sprint 0 : si un point bloquant apparaît, il est documenté comme décision
  ad hoc de ce sprint (§8) plutôt que résolu silencieusement.
- La documentation de démarrage (T12) reflète l'état réel du projet au
  moment de la clôture du sprint, pas un état intermédiaire.
- Le Desktop existant n'a subi aucune régression, aucune modification.

Le sprint complet n'est clôturé que lorsque les sept critères de validation
du §6 sont vérifiés simultanément, pas seulement individuellement tâche par
tâche.

---

## 8. Risques éventuels

- **Sur-ingénierie précoce** — le risque le plus probable dans un sprint de
  fondations est d'anticiper des besoins des sprints suivants (ex. :
  commencer à modéliser la Prestation « pendant qu'on y est »). À écarter
  strictement : toute tentation de ce type doit être renvoyée en dehors du
  sprint, conformément à §3.
- **Décisions ouvertes du Sprint 0 non bloquantes mais présentes** — certains
  points listés comme non tranchés (`docs/02_DOMAIN_MODEL.md` §9 points 1 à
  3 : statuts de la Société, cycle de vie précis de l'Utilisateur, liste
  définitive des Rôles) ne bloquent pas ce sprint, qui n'a besoin que d'un
  état minimal fonctionnel. Le risque est de les trancher implicitement dans
  le code au lieu de les traiter comme des choix d'implémentation
  volontairement simplifiés, à documenter comme tels et à ne pas confondre
  avec une décision métier définitive.
- **Isolation multi-tenant mal posée dès le départ** — c'est l'invariant de
  sécurité le plus coûteux à corriger rétroactivement
  (`docs/06_ARCHITECTURE.md` §4.4) : une erreur de conception à ce stade se
  propage à tous les sprints suivants. C'est pour cette raison que le test
  d'intégration dédié (T11) est un critère de validation du sprint, pas une
  simple tâche optionnelle.
- **Absence de choix technologique explicite** — ce document n'impose aucune
  technologie, mais un développeur doit malgré tout choisir des outils
  concrets pour écrire du code. Le risque est un flottement en tout début de
  sprint si ce choix n'est pas acté rapidement, en dehors de ce document, par
  la personne qui commence effectivement l'implémentation.
- **Confusion entre écran minimal et travail définitif d'interface** — le
  Frontend prévu (T9) sert uniquement à prouver que l'authentification et le
  contexte fonctionnent. Le risque est d'y investir un temps disproportionné
  en anticipant l'organisation UX déjà décrite (`docs/03_UX_ARCHITECTURE.md`)
  mais hors périmètre de ce sprint.
- **Dépôt partagé avec le Desktop** — toute erreur de manipulation (chemin,
  script, configuration) pourrait affecter par mégarde `app/` ou `app_old/`.
  Le critère de validation §6 point 7 doit être vérifié explicitement avant
  toute clôture de tâche touchant à la structure du dépôt.
