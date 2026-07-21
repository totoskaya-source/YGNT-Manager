# Product Principles — YGNT Manager Web

Software Design Specification — Document de cadrage n°2
Statut : **Brouillon Sprint 0 — en attente de validation**
Périmètre : déclinaison opérationnelle des principes produit. Ne redéfinit
pas la vision (`00_PRODUCT_VISION.md`), ne prend aucune décision de modèle de
données (`02_DOMAIN_MODEL.md`) ni d'architecture technique
(`06_ARCHITECTURE.md`).

---

## Table des matières

1. [Objet du document](#1-objet-du-document)
2. [Rappel des principes fondateurs validés](#2-rappel-des-principes-fondateurs-validés)
3. [Déclinaison opérationnelle de chaque principe](#3-déclinaison-opérationnelle-de-chaque-principe)
4. [Principes complémentaires proposés](#4-principes-complémentaires-proposés)
5. [Ordre de priorité en cas de conflit entre principes](#5-ordre-de-priorité-en-cas-de-conflit-entre-principes)
6. [Conséquences du choix multi-tenant sur les principes](#6-conséquences-du-choix-multi-tenant-sur-les-principes)
7. [Cas particuliers](#7-cas-particuliers)
8. [Cas limites](#8-cas-limites)
9. [Évolutions futures envisageables](#9-évolutions-futures-envisageables)
10. [Checklist de validation](#10-checklist-de-validation)

---

## 1. Objet du document

`00_PRODUCT_VISION.md` répond à la question « pourquoi ce produit existe-t-il
et pour qui ? ». Ce document répond à la question suivante : **comment
reconnaît-on, au moment d'une décision produit, qu'un choix respecte ou
trahit les principes fondateurs ?**

Il transforme chaque principe en un test concret, utilisable dès
`02_DOMAIN_MODEL.md` et surtout dans `04_USE_CASES.md`, où chaque cas d'usage
proposé devra pouvoir être confronté à ces principes avant d'être retenu.

Ce document ne redéfinit aucun principe : il les reprend tels que validés
dans la Vision et les rend actionnables.

---

## 2. Rappel des principes fondateurs validés

Repris de `00_PRODUCT_VISION.md` §4, sans modification :

1. La Prestation est l'entité centrale.
2. Toutes les données gravitent autour de la prestation.
3. Aucune ressaisie inutile.
4. Organisation.
5. Automatisation.
6. Simplicité.
7. Le Cockpit est orienté Actions, non Statistiques.
8. Chaque fonctionnalité doit faire gagner du temps.

---

## 3. Déclinaison opérationnelle de chaque principe

Pour chaque principe : une règle d'application et un test à se poser avant de
valider une fonctionnalité dans les documents suivants.

### 3.1 La Prestation est l'entité centrale

- **Règle** : toute nouvelle donnée ou fonctionnalité doit pouvoir répondre à
  la question « à quelle prestation cela se rattache-t-il ? », directement ou
  via un document qui lui est lui-même rattaché.
- **Test avant validation** : si une donnée ne peut pas être reliée à une
  Prestation, interroger sa place dans le modèle avant de l'ajouter — ce
  n'est pas nécessairement un refus, mais un signal d'alerte.

### 3.2 Toutes les données gravitent autour de la prestation

- **Règle** : une information (lieu, montant, statut) a une seule source de
  vérité, rattachée à la Prestation ou au document qui l'engage réellement —
  jamais dupliquée entre modules.
- **Test avant validation** : « cette information existe-t-elle déjà ailleurs
  dans le dossier de la prestation ? » Si oui, la référencer, jamais la
  recopier.

### 3.3 Aucune ressaisie inutile

- **Règle** : toute donnée déjà connue du système (fiche artiste, fiche
  organisateur, lieu déjà saisi) doit pré-remplir automatiquement les champs
  correspondants, tout en restant modifiable au cas par cas.
- **Test avant validation** : « l'utilisateur retape-t-il une information que
  le logiciel connaît déjà ? » Si oui, la fonctionnalité n'est pas terminée.

### 3.4 Organisation

- **Règle** : chaque écran de liste ou de suivi doit permettre de répondre à
  « où en est ce dossier ? » sans recherche manuelle ni navigation
  supplémentaire.
- **Test avant validation** : un statut, une échéance ou une action en
  attente doit être visible sans ouvrir la fiche.

### 3.5 Automatisation

- **Règle** : une tâche répétitive identifiée est candidate par défaut à
  l'automatisation ; elle n'est acceptée comme geste manuel permanent que si
  une raison explicite l'impose (ex. contrôle humain requis avant envoi
  d'un document légal).
- **Test avant validation** : « pourquoi cette étape reste-t-elle manuelle ? »
  doit avoir une réponse, sinon l'automatiser.

### 3.6 Simplicité

- **Règle** : en cas de doute entre deux implémentations, celle qui est la
  plus simple à comprendre pour l'utilisateur l'emporte, même si elle couvre
  moins de cas à la marge.
- **Test avant validation** : un nouvel utilisateur peut-il comprendre l'écran
  sans explication ? Si la réponse nécessite une formation, revoir la
  fonctionnalité avant de l'ajouter à la version cible.

### 3.7 Le Cockpit est orienté Actions, non Statistiques

- **Règle** : toute information affichée sur le Cockpit doit soit déclencher
  une action possible, soit être immédiatement actionnable en un clic. Un
  chiffre qui ne débouche sur rien n'a pas sa place sur le Cockpit.
- **Test avant validation** : « que fait l'utilisateur juste après avoir vu
  cette information ? » Si la réponse est « rien », elle relève d'une future
  page Statistiques, pas du Cockpit.

### 3.8 Chaque fonctionnalité doit faire gagner du temps

- **Règle** : toute fonctionnalité proposée doit énoncer, avant d'être
  retenue, le geste qu'elle supprime ou le temps qu'elle fait gagner.
- **Test avant validation** : si personne ne peut formuler ce gain en une
  phrase, la fonctionnalité est ajournée.

---

## 4. Principes complémentaires proposés

Les candidats ci-dessous proviennent du brouillon de travail
`drafts/PROJECT_CHARTER.md` (non validé). Ils sont présentés ici pour
arbitrage — **aucun n'est retenu à ce stade** tant qu'il n'a pas reçu de
validation explicite.

> 🔶 **Décision à valider — Cohérence.** Présentation homogène de tous les
> modules (recherche, tableau, actions), déjà en vigueur côté Desktop
> (`docs/PROJECT.md`). Proposition : l'élever en principe fondateur explicite
> du Web, au même titre que la Simplicité.

> 🔶 **Décision à valider — Sécurité.** Découle directement de la décision
> multi-tenant déjà validée (`00_PRODUCT_VISION.md` §5) : l'isolation des
> données entre tenants est non négociable. Proposition : l'élever en
> principe fondateur explicite plutôt que de le laisser implicite dans
> l'architecture, précisément parce qu'un principe fondateur engage aussi les
> choix produit (ex. : pas de fonctionnalité de « recherche globale »
> inter-tenants, même en interne).

> 🔶 **Décision à valider — Évolutivité.** Pouvoir ajouter un module sans
> remettre en cause les modules existants. Cohérent avec la règle déjà en
> vigueur côté Desktop (évolutions de schéma toujours additives,
> `docs/BUSINESS_RULES.md`). Proposition : le formaliser comme principe
> produit, pas seulement comme règle technique.

> 🔶 **Décision à valider — Maintenabilité.** Reprise du principe de code
> propre déjà en vigueur côté Desktop. Question ouverte : ce principe
> relève-t-il de ce document (engagement produit) ou seulement des règles de
> développement internes à définir plus tard ? Recommandation : le garder
> hors de ce document — la maintenabilité est un principe d'ingénierie, pas
> un principe produit visible par l'utilisateur.

**Non retenu en proposition distincte** : la « rapidité » évoquée dans le
brouillon de travail est déjà couverte par le principe validé « chaque
fonctionnalité doit faire gagner du temps » (§3.8) — pas de doublon proposé.

---

## 5. Ordre de priorité en cas de conflit entre principes

Certains principes peuvent entrer en tension (ex. : la Sécurité, si elle est
retenue, peut ajouter une friction — authentification, contrôle d'accès —
qui va à l'encontre de la Simplicité).

> 🔶 **Décision à valider — Ordre de priorité proposé** (à trancher, faute de
> quoi chaque conflit sera arbitré au cas par cas sans règle stable) :
>
> 1. **Sécurité** (si retenue en §4) et intégrité des données — jamais
>    sacrifiées, y compris pour la simplicité.
> 2. **Simplicité** pour l'utilisateur final — priorité sur la richesse
>    fonctionnelle.
> 3. **Aucune ressaisie / Automatisation** — priorité sur la couverture de
>    cas rares.
> 4. **Richesse fonctionnelle** — vient en dernier : une fonctionnalité
>    supplémentaire ne justifie jamais de complexifier l'expérience courante.
>
> Cet ordre s'applique en cas de conflit réel, pas comme grille systématique
> — il sert à trancher, pas à remplacer le jugement au cas par cas.

---

## 6. Conséquences du choix multi-tenant sur les principes

La décision Option C (`00_PRODUCT_VISION.md` §5) modifie la portée de
plusieurs principes déjà validés, sans les contredire :

- **§3.2 (gravitent autour de la prestation)** — la source unique de vérité
  s'entend **par tenant** : deux tenants ne partagent jamais de donnée, même
  si leurs prestations se ressemblent.
- **§3.3 (aucune ressaisie)** — le pré-remplissage automatique ne doit
  **jamais** puiser une information dans un autre tenant, même pour
  accélérer la saisie.
- **§3.7 (Cockpit orienté actions)** — déjà précisé dans la Vision (§7) :
  filtrage par défaut sur l'utilisateur connecté, avec bascule vers l'équipe
  du tenant. Le Cockpit ne montre jamais les actions d'un autre tenant.

---

## 7. Cas particuliers

- **Un nouveau principe candidat (§4) n'est que partiellement validé** (ex. :
  Cohérence validée, Sécurité encore en discussion) : ce document doit être
  mis à jour pour ne conserver que les principes explicitement tranchés — pas
  d'état intermédiaire flou dans un document SDS.
- **Un principe validé se heurte à une contrainte technique découverte plus
  tard** (dans `06_ARCHITECTURE.md` par exemple) : le principe n'est pas
  silencieusement contourné — la contradiction doit être remontée et
  documentée comme un point de révision de ce document, pas résolue par le
  code seul.
- **Une fonctionnalité demandée ne respecte aucun principe mais répond à un
  besoin métier ponctuel** : elle peut être acceptée à titre d'exception,
  mais l'exception doit être explicitement justifiée et tracée (pas
  silencieuse), pour éviter l'érosion progressive des principes.

---

## 8. Cas limites

- **Deux principes validés se contredisent sur un cas concret** non couvert
  par l'ordre de priorité (§5) : le cas doit être remonté pour arbitrage
  avant développement, pas tranché unilatéralement en cours
  d'implémentation.
- **Un principe devient obsolète** (ex. : un changement de décision sur le
  multi-tenant) : ce document doit être révisé explicitement, avec une
  mention de la révision — jamais laissé en contradiction silencieuse avec
  `00_PRODUCT_VISION.md`.

---

## 9. Évolutions futures envisageables

*(idées, non engageantes)*

- Ajout d'un principe d'**Accessibilité** si le produit s'ouvre à un public
  plus large.
- Formalisation d'un principe de **Conformité réglementaire** (RGPD en
  particulier, renforcé par la nature multi-tenant du produit) si ce sujet
  n'est pas déjà couvert ailleurs lors de la rédaction de
  `06_ARCHITECTURE.md`.
- Réouverture de l'arbitrage sur la Maintenabilité (§4) si un document dédié
  aux règles d'ingénierie du Web est créé par la suite.

---

## 10. Checklist de validation

- [ ] Les huit principes fondateurs (§2) sont correctement déclinés en règles
      opérationnelles (§3) — aucun n'est resté abstrait.
- [ ] Chaque principe complémentaire proposé (§4 — Cohérence, Sécurité,
      Évolutivité, Maintenabilité) a reçu une réponse explicite (retenu /
      écarté / reporté).
- [ ] L'ordre de priorité en cas de conflit (§5) est validé tel quel ou
      amendé.
- [ ] Les conséquences du multi-tenant sur les principes existants (§6) sont
      jugées complètes.
- [ ] Les cas particuliers (§7) et cas limites (§8) sont jugés complets à ce
      stade.
- [ ] Ce document peut servir de référence stable pour rédiger
      `02_DOMAIN_MODEL.md`.
