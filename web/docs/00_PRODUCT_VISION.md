# Product Vision — YGNT Manager Web

Software Design Specification — Document fondateur
Statut : **Sprint 0 — décisions structurantes validées (voir §12)**
Périmètre : vision produit uniquement (aucune décision technique, aucun code)

**Révision** : les décisions des §4.1, §5, §6.2 et §7 ont été validées et sont
reflétées dans ce document. Voir `01_PRODUCT_PRINCIPLES.md` pour leur
déclinaison en principes opérationnels.

---

## Table des matières

1. [Résumé](#1-résumé)
2. [Contexte et origine du projet](#2-contexte-et-origine-du-projet)
3. [Énoncé de vision](#3-énoncé-de-vision)
4. [Principes fondateurs](#4-principes-fondateurs)
5. [Positionnement Web vis-à-vis du Desktop](#5-positionnement-web-vis-à-vis-du-desktop)
6. [Utilisateurs cibles et personas](#6-utilisateurs-cibles-et-personas)
7. [Le Cockpit : philosophie d'action](#7-le-cockpit--philosophie-daction)
8. [Proposition de valeur](#8-proposition-de-valeur)
9. [Hors périmètre](#9-hors-périmètre)
10. [Cas particuliers](#10-cas-particuliers)
11. [Cas limites](#11-cas-limites)
12. [Décisions ouvertes — synthèse](#12-décisions-ouvertes--synthèse)
13. [Évolutions futures envisageables](#13-évolutions-futures-envisageables)
14. [Checklist de validation](#14-checklist-de-validation)

---

## 1. Résumé

YGNT Manager Web est un nouveau produit destiné aux producteurs de spectacles.
Il ne remplace pas YGNT Manager Desktop (v1.0.3, stable, en maintenance) et
n'en est pas un portage : c'est une nouvelle conception, pensée pour le Web
dès le départ, qui reprend le métier déjà validé côté Desktop sans en hériter
l'architecture technique.

Ce document fixe le **pourquoi** du produit avant tout **comment**. Il sert de
référence pour tous les documents suivants (`01_PRODUCT_PRINCIPLES.md`,
`02_DOMAIN_MODEL.md`, `04_USE_CASES.md`, `05_DATABASE.md`,
`06_ARCHITECTURE.md`, `07_API.md`, `08_ROADMAP.md`).

---

## 2. Contexte et origine du projet

- **YGNT Manager Desktop v1.0.3** est stable et continue d'évoluer, mais entre
  en phase de maintenance : il reste la référence métier éprouvée (voir
  `docs/PROJECT.md`, `docs/BUSINESS_RULES.md`,
  `docs/PRESTATIONS_ARCHITECTURE.md` à la racine du dépôt), mais n'est plus le
  terrain des évolutions ambitieuses.
- **YGNT Manager Web** est un nouveau produit, pas une migration du code
  existant. Il peut être repensé en profondeur dans sa conception technique,
  mais il sert le **même métier** : la production de spectacles.
- Les deux produits cohabitent dans le **même dépôt Git**, sous `web/` pour la
  partie Web et `app/` (Desktop existant) pour la partie historique.
- **Le Desktop ne doit jamais être cassé** par les travaux menés sur le Web.
  Aucune modification du Web ne doit toucher au code, aux données ou aux
  documents générés par le Desktop.
- Nous sommes en **Sprint 0** : aucune ligne de code applicative n'est
  autorisée tant que l'architecture n'est pas validée. Ce document est le
  premier livrable de ce sprint.
- Nous travaillons **comme un éditeur logiciel** : chaque décision produit est
  documentée, proposée, et validée avant d'être considérée comme acquise.

---

## 3. Énoncé de vision

> YGNT Manager Web n'est pas seulement un logiciel de gestion. C'est un
> assistant de production qui accompagne le producteur tout au long du cycle
> de vie d'une prestation.

Cet énoncé est la boussole du produit. Toute fonctionnalité proposée dans les
prochains documents doit pouvoir s'y rattacher : soit elle simplifie le
travail du producteur, soit elle l'accompagne à une étape du cycle de vie
d'une prestation. À défaut, elle n'a pas sa place dans le produit — ou doit
être requalifiée explicitement.

---

## 4. Principes fondateurs

Ces principes sont donnés comme cadre de travail non négociable pour la
conception du produit. Ils sont repris ici pour être déclinés, pas
réinterprétés.

### 4.1 La Prestation est l'entité centrale

Un événement réel (concert, mariage, festival, soirée privée...) existe en
tant que fiche à part entière. Ce principe est déjà validé et documenté côté
Desktop dans `docs/PRESTATIONS_ARCHITECTURE.md` : la Prestation y est définie
comme le pivot autour duquel gravitent Devis, Contrat, Facture et Paiement.

> ✅ **Décision validée** — Le modèle conceptuel Prestation déjà éprouvé côté
> Desktop (référence unique `PREST-AAAA-XXXX`, notion de Dossier consolidé,
> de Timeline métier, d'équipe de prestation distincte du contrat de cession)
> sert de **référence métier de départ** pour le Web. Il sera raffiné —
> jamais recopié tel quel — dans `02_DOMAIN_MODEL.md`, notamment pour
> intégrer la dimension multi-tenant/multi-utilisateur actée en §5.

### 4.2 Toutes les données gravitent autour de la prestation

Artiste, organisateur, lieu, documents commerciaux : tout se rattache à une
prestation plutôt que d'exister en silos indépendants.

### 4.3 Aucune ressaisie inutile

Une information saisie une fois (coordonnées d'un artiste, adresse d'un
organisateur, lieu d'un événement) doit être réutilisée automatiquement
partout où elle est pertinente, sans jamais obliger l'utilisateur à la
retaper.

### 4.4 Organisation

Le produit aide le producteur à s'organiser : il doit toujours pouvoir
répondre à « où en est ce dossier ? » sans recherche manuelle.

### 4.5 Automatisation

Ce qui peut être déduit, calculé ou déclenché automatiquement par le logiciel
ne doit jamais être une action manuelle supplémentaire pour l'utilisateur.

### 4.6 Simplicité

La simplicité prime sur le nombre de fonctionnalités. Un principe déjà énoncé
côté Desktop (`docs/PROJECT.md`) et repris ici comme socle commun aux deux
produits.

### 4.7 Le Cockpit est orienté Actions, non Statistiques

Détaillé en [section 7](#7-le-cockpit--philosophie-daction).

### 4.8 Chaque fonctionnalité doit faire gagner du temps

Une fonctionnalité qui n'apporte pas de gain de temps mesurable ou perceptible
au producteur n'a pas de justification suffisante pour exister.

---

## 5. Positionnement Web vis-à-vis du Desktop

| | Desktop | Web |
|---|---|---|
| Statut | Stable, maintenance | Nouveau produit, en conception |
| Utilisateur | Mono-poste, un seul utilisateur | Multi-tenant dès l'architecture (voir décision ci-dessous) |
| Données | SQLite locale, un seul fichier | À définir dans `05_DATABASE.md`, avec isolation par tenant |
| Accès | Poste local uniquement | Accessible à distance (navigateur) |
| Génération de documents | DOCX/PDF via Word (COM), dépendance Windows | À redéfinir sans dépendance Word (voir `06_ARCHITECTURE.md`) |
| Évolution | Corrections et améliorations ponctuelles | Chantier actif |

Le Web n'hérite d'aucune contrainte technique du Desktop (ni SQLite, ni
dépendance Word, ni PySide6). Il hérite en revanche du métier validé : les
règles de gestion déjà éprouvées (`docs/BUSINESS_RULES.md`) restent la
référence tant qu'elles ne sont pas explicitement remises en question.

> ✅ **Décision validée — Portée utilisateur du Web (Option C retenue).**
> C'est la décision la plus structurante de ce document : elle conditionne
> `02_DOMAIN_MODEL.md`, `05_DATABASE.md` et `06_ARCHITECTURE.md`.
>
> Le produit est conçu **dès le départ comme un SaaS multi-tenant**. La V1
> pourra n'être exploitée qu'avec un seul tenant (une seule société de
> production), mais **toute l'architecture doit être compatible, dès sa
> première version, avec plusieurs sociétés, plusieurs utilisateurs et
> plusieurs rôles**. Il ne s'agit pas d'ajouter le multi-tenant plus tard :
> c'est une contrainte de conception qui s'applique à `02_DOMAIN_MODEL.md`
> (entité Société/Tenant, Utilisateur, Rôle dès le modèle de domaine) et à
> `05_DATABASE.md` (isolation des données par tenant sur chaque table
> métier), même si l'usage réel démarre avec un seul client.
>
> Conséquence directe : le persona « Collaborateur interne » (§6.2) et le
> filtrage du Cockpit par utilisateur (§7) ne sont plus des options — ils
> découlent de cette décision.

---

## 6. Utilisateurs cibles et personas

### 6.1 Persona principal — Le Producteur / Gérant

Utilisateur déjà identifié et servi par le Desktop. Gère l'ensemble du cycle
de vie d'une prestation : prospection, devis, contrat, facturation,
règlement. Attend du Web au minimum ce que le Desktop lui apporte déjà,
augmenté de l'accessibilité à distance.

### 6.2 Persona secondaire — Collaborateur interne

> ✅ **Décision validée** — Conséquence de l'Option C retenue en §5. Un
> collaborateur (assistant de production, comptable) peut intervenir avec un
> périmètre de droits réduit (ex. : accès aux prestations mais pas à la
> facturation, ou l'inverse). Ce persona est confirmé dès la V1, même dans un
> usage à tenant unique. Le détail des rôles et permissions est spécifié dans
> `02_DOMAIN_MODEL.md`, pas ici.

### 6.3 Acteurs externes (hors utilisateurs directs pour l'instant)

L'artiste et l'organisateur sont des **entités du domaine** (déjà présentes
côté Desktop), pas des utilisateurs du logiciel : ils ne se connectent pas au
produit. Un accès externe (portail de consultation, signature électronique)
est envisageable mais **hors périmètre de la vision actuelle** — voir
[section 13](#13-évolutions-futures-envisageables).

---

## 7. Le Cockpit : philosophie d'action

Le Cockpit est l'écran d'entrée du produit. Il ne doit **jamais** se limiter
à un tableau de chiffres : son rôle est de répondre à la question « qu'est-ce
que je dois traiter aujourd'hui ? ».

Ce principe est déjà validé et mis en œuvre côté Desktop (Dashboard « orienté
actions », `docs/IDEAS_V1_1.md`) : factures en retard, devis à relancer,
prestations sans facture, documents non générés, prochaines prestations. Le
Cockpit du Web part de cette même philosophie.

Ce qui distingue un Cockpit d'un tableau de bord statistique :

| Tableau de bord statistique | Cockpit orienté action |
|---|---|
| « Vous avez généré 12 contrats ce mois-ci » | « 3 devis n'ont pas eu de réponse depuis 10 jours : relancer » |
| Informe | Déclenche une action |
| Se consulte | Se traite |
| Regarde en arrière | Regarde ce qu'il reste à faire |

> ✅ **Décision validée** — Par défaut, le Cockpit affiche **« Mes actions »**
> : les actions assignées à l'utilisateur connecté. L'utilisateur peut ensuite
> basculer vers deux autres vues via un filtre :
> - **« Toute l'équipe »** — les actions de l'ensemble des collaborateurs du
>   tenant ;
> - **« Non attribuées »** — les actions qui n'ont encore été assignées à
>   personne.
>
> Cette règle sera détaillée en cas d'usage dans `04_USE_CASES.md`.

---

## 8. Proposition de valeur

| Pour le producteur | Grâce à |
|---|---|
| Ne plus ressaisir deux fois la même information | Prestation comme source unique de vérité (§4.2, §4.3) |
| Savoir en un coup d'œil ce qui doit être traité | Cockpit orienté actions (§7) |
| Travailler depuis n'importe où | Accès Web, sans dépendance à un poste unique |
| Collaborer sans se marcher dessus | Modèle multi-tenant/multi-utilisateur (§5) |
| Gagner du temps sur chaque tâche répétitive | Automatisation (§4.5) |

---

## 9. Hors périmètre

Pour éviter toute dérive de scope dès le Sprint 0, YGNT Manager Web **n'est
pas** :

- un portage visuel ou fonctionnel à l'identique du Desktop ;
- un outil de comptabilité générale (au-delà de la facturation déjà couverte
  par le métier existant) ;
- un CRM généraliste ;
- à ce stade, un portail accessible aux artistes ou aux organisateurs
  (voir §6.3 et §13) ;
- un remplacement immédiat du Desktop : les deux produits cohabitent.

---

## 10. Cas particuliers

- **Cohabitation Desktop / Web pendant la transition** : un producteur peut
  utiliser le Desktop et le Web en parallèle. Aucune synchronisation
  bidirectionnelle automatique n'est présupposée par ce document — le sujet
  est renvoyé à `06_ARCHITECTURE.md`/`05_DATABASE.md` si un besoin de
  migration ou d'import ponctuel est confirmé.
- **Tenant à un seul utilisateur** : même si l'architecture est multi-tenant
  et multi-utilisateur dès la conception (§5), un tenant ne comptant qu'un
  seul utilisateur (cas de la V1) doit rester aussi simple à utiliser que le
  Desktop actuel — la gestion des rôles ne doit jamais ajouter de friction
  perceptible pour un producteur qui travaille seul.
- **Collaborateur aux droits restreints consultant un dossier incomplet** :
  le Cockpit et le Dossier doivent rester cohérents même quand certaines
  informations (ex. montants) sont masquées selon le rôle — traité en détail
  dans `02_DOMAIN_MODEL.md`.

---

## 11. Cas limites

- **Migration d'un historique Desktop existant** (des années de contrats,
  factures, artistes) vers le Web : hors périmètre de ce document ; à traiter
  comme un chantier de migration de données dédié, une fois `05_DATABASE.md`
  stabilisé.
- **Deux utilisateurs modifiant la même prestation simultanément** : la
  gestion de la concurrence d'accès est un sujet d'architecture, pas de
  vision produit — renvoyé à `06_ARCHITECTURE.md`.
- **Un tenant tente d'accéder aux données d'un autre tenant** (erreur
  applicative, faille) : l'isolation multi-tenant est un invariant de
  sécurité non négociable, quelle que soit l'implémentation technique
  retenue — détaillé dans `06_ARCHITECTURE.md`.
- **Perte de connexion réseau en cours de saisie** : un produit Web suppose
  une connexion ; un mode dégradé/hors-ligne n'est pas présupposé nécessaire
  pour la V1, à confirmer si des cas d'usage terrain (ex. saisie en festival
  sans réseau) l'exigent.

---

## 12. Décisions ouvertes — synthèse

### 12.1 Décisions validées

1. **§4.1** — ✅ Le modèle conceptuel Prestation du Desktop (référence,
   Dossier, Timeline, équipe de prestation) sert de référence métier de
   départ pour le Web.
2. **§5** — ✅ Portée utilisateur : **Option C**, multi-tenant SaaS dès la
   conception de l'architecture ; usage V1 limité à un seul tenant.
3. **§6.2** — ✅ Le persona « Collaborateur interne » est retenu dès la V1.
4. **§7** — ✅ Le Cockpit affiche « Mes actions » par défaut (filtré par
   utilisateur connecté), avec bascule possible vers « Toute l'équipe » ou
   « Non attribuées ».

### 12.2 Décision restant ouverte

5. **§9** — Le périmètre « hors scope » listé n'a pas encore reçu de
   confirmation explicite. Il reste la version de travail tant qu'il n'est
   pas contredit.

Les points 1 à 4 étant tranchés, `02_DOMAIN_MODEL.md` et
`01_PRODUCT_PRINCIPLES.md` peuvent être rédigés sur cette base stable.

---

## 13. Évolutions futures envisageables

*(idées, non engageantes, à ne pas confondre avec une roadmap)*

- Portail externe pour les organisateurs (consultation d'un devis, signature
  électronique d'un contrat).
- Application mobile compagnon.
- **Ouverture commerciale à des sociétés clientes externes** : l'architecture
  multi-tenant est actée dès la conception (§5), mais la décision de vendre
  effectivement le produit à d'autres producteurs de spectacles (site public,
  inscription libre, facturation SaaS, onboarding autonome) reste une
  décision commerciale distincte, non prise à ce stade.
- Intégrations agenda externes (Google Agenda, Outlook) — idée déjà notée côté
  Desktop (`docs/IDEAS_V1_1.md`), transposable au Web.
- Import/synchronisation depuis le Desktop pour les producteurs en transition.

---

## 14. Checklist de validation

- [x] L'énoncé de vision (§3) reflète fidèlement l'intention du commanditaire.
- [x] Les principes fondateurs (§4) sont validés sans réserve.
- [x] La décision §4.1 (reprise du modèle conceptuel Prestation du Desktop)
      est tranchée.
- [x] La décision §5 (portée utilisateur — Option C) est tranchée.
- [x] Le persona « Collaborateur interne » (§6.2) est confirmé.
- [x] Le mode d'affichage du Cockpit (§7 — « Mes actions » par défaut) est
      tranché.
- [ ] Le périmètre « hors scope » (§9) est validé tel quel ou amendé.
- [x] Les cas particuliers (§10) et cas limites (§11) sont jugés complets à
      ce stade.
- [ ] La décision restante listée en §12.2 a reçu une réponse explicite.
- [x] Ce document peut servir de référence stable pour rédiger
      `01_PRODUCT_PRINCIPLES.md` et `02_DOMAIN_MODEL.md`.
