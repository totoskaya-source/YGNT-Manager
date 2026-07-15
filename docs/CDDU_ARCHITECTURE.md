# YGNT Manager — Architecture du module Contrat de travail (CDDU)

Document de conception — Sprint 14.2 (finalisation avant développement).
Il complète `PROJECT.md`, `CODING_RULES.md`, `BUSINESS_RULES.md`,
`ROADMAP.md`, `PRESTATIONS_ARCHITECTURE.md` et
`PRODUCTEUR_FORMATIONS_ARCHITECTURE.md`, sans les remplacer.

**Ce document est une évolution des Sprints 14.0 et 14.1, pas un nouveau
module.** Les décisions structurantes restent toutes valides : le salarié
est une fiche Artiste existante (14.0), la mensualisation repose sur
`contrat_cddu_dates` comme source de vérité (14.1). Le Sprint 14.2 tranche la
dernière question laissée ouverte : **quel est le workflow par défaut**, et
sépare clairement le cas courant (rapide, sans friction) du cas avancé
(mensualisation, avec assistant).

Aucun code, aucun modèle, aucune migration, aucun repository, aucun service,
aucune UI n'est produit par ce document. Aucun commit Git. Seul
`docs/CDDU_ARCHITECTURE.md` est modifié par cette révision.

---

## 1. Principe directeur

Le CDDU (Contrat à Durée Déterminée d'Usage) est le second type de contrat de
YGNT Manager, indépendant du **Contrat de cession** (Producteur ↔
Organisateur, inchangé). Le salarié d'un CDDU **est** une fiche Artiste
existante — aucune table « Salarié » séparée (décision Sprint 14.0).

**Priorité n°1 du Sprint 14.2 : le cas d'usage principal du logiciel est**

```
1 date  =  1 musicien  =  1 CDDU
```

C'est le chemin que le logiciel doit optimiser en premier — création en
quelques secondes, sans question, sans assistant. La mensualisation
(plusieurs dates, plusieurs prestations, un seul contrat — Sprint 14.1) reste
entièrement disponible, mais devient explicitement un **outil complémentaire
pour cas particuliers**, accessible par un chemin séparé, qui ne doit jamais
alourdir le chemin principal.

---

## 2. Enrichissement de la fiche Artiste (champs RH) — inchangé

```
artists (ajouts)
├── birth_place              TEXT   -- lieu de naissance
├── conges_spectacle_number  TEXT   -- N° de congés spectacle
```

```
producteurs (ajout)
├── convention_collective   TEXT
```

Voir Sprint 14.0 pour le détail complet des champs déjà disponibles.

---

## 3. La liste des artistes d'une prestation — `prestation_participants` (réalisé, Sprint 15.5)

Le workflow prioritaire (§6) exige que, depuis l'écran d'une Prestation,
**chaque artiste engagé sur elle apparaisse individuellement** avec sa propre
action « Créer le CDDU ». Or `prestations.artist_id` (schéma actuel) ne porte
qu'**un seul** artiste par prestation (la Formation vendue) — insuffisant dès
qu'un groupe de plusieurs musiciens (chacun étant sa propre fiche Artiste,
décision Sprint 14.0) est engagé sur le même événement.

**Ce prérequis, identifié au Sprint 14.2, a été livré au Sprint 15.5** sous le
nom d'**Équipe de prestation** — voir `PRESTATIONS_ARCHITECTURE.md`, section
11, pour la référence complète (table, règles, contraintes). Le nom réel de
la table diffère de la proposition initiale (`prestation_artistes`) :

```
prestation_participants
├── id              INTEGER PK AUTOINCREMENT
├── prestation_id   INTEGER NOT NULL   FK -> prestations(id) ON DELETE CASCADE
├── artiste_id      INTEGER NOT NULL   FK -> artists(id)     ON DELETE CASCADE
├── role            TEXT                -- optionnel
├── ordre           INTEGER             -- optionnel
├── created_at      TEXT DEFAULT CURRENT_TIMESTAMP
├── updated_at      TEXT

UNIQUE(prestation_id, artiste_id)
```

- Représente le **roster** des artistes engagés sur une Prestation
  (typiquement : les membres d'un groupe, chacun ayant sa propre fiche), avec
  un rôle et un ordre d'affichage optionnels — utile pour trier la liste des
  actions « Créer le CDDU » du workflow prioritaire (§6).
- `prestations.artist_id` reste inchangé, conservé comme Formation vendue
  pour tout ce qui concerne le contrat de cession — aucun impact.
- **Le futur générateur CDDU utilisera exclusivement
  `prestation_participants`** pour déterminer quels contrats créer et pour
  quels artistes — jamais `prestations.artist_id` seul, qui ne représente
  que le spectacle vendu, pas l'équipe réelle.
- C'est cette table qui alimentera la colonne d'action « Créer le CDDU » (§6)
  et la recherche « toutes les prestations du mois concernant cet artiste »
  de l'assistant de mensualisation (§7), lors du sprint qui construira l'UI
  correspondante.
- Livré ce sprint : migration, modèle, repository, service, tests. Aucune UI,
  aucun écran, aucun bouton — la connexion effective entre cette table et les
  écrans CDDU décrits aux §6/§7 reste à construire dans un sprint UI dédié.

---

## 4. Structure de la table `contrats_cddu` — inchangée depuis le Sprint 14.1

```
contrats_cddu
├── id, numero (CDDU-AAAA-XXXX)
├── prestation_id      FK -> prestations(id)   -- prestation de départ, informatif
├── artist_id          FK -> artists(id)        -- le salarié
├── producteur_id       FK -> producteurs(id)
├── producteur_* (instantané employeur)
├── artiste_* (instantané salarié)
├── prestation_reference, prestation_objet, prestation_lieu, prestation_ville
│     (instantané de la prestation de départ, contexte de l'article Objet)
├── numero_objet         TEXT DEFAULT ''         -- toujours vide, voir §9
├── remuneration_brute     REAL DEFAULT 0.0       -- saisie manuelle uniquement
├── defraiement_*            (tous optionnels, voir §10)
├── observations, docx_path, pdf_path
├── status                    TEXT DEFAULT 'draft' -- cycle de vie étendu, voir §12
├── created_at, updated_at, generated_at
```

`date_debut`/`date_fin`, si affichées, restent dérivées (min/max des lignes
`contrat_cddu_dates`), jamais stockées séparément. Détail complet inchangé
depuis le Sprint 14.1.

---

## 5. `contrat_cddu_dates` — inchangée depuis le Sprint 14.1

```
contrat_cddu_dates
├── id                 INTEGER PK AUTOINCREMENT
├── contrat_cddu_id    INTEGER NOT NULL   FK -> contrats_cddu(id) ON DELETE CASCADE
├── prestation_id      INTEGER            FK -> prestations(id)  ON DELETE SET NULL
├── date_travaillee    TEXT NOT NULL
├── nombre_cachets     INTEGER DEFAULT 1
```

Chaque ligne : une date travaillée, la prestation d'origine, le nombre de
cachets. Le contrat regroupe toutes ses lignes. Un CDDU « simple » (cas
prioritaire, §6) a exactement une ligne ; un CDDU « mensualisé » (§7) en a
plusieurs, potentiellement sur des prestations différentes. Nombre total de
cachets toujours calculé (`SUM`), jamais stocké.

Précision utile au Sprint 14.2 : c'est également sur cette table que repose
l'exclusion des dates déjà contractualisées dans l'assistant de
mensualisation (§7) — une date est considérée comme « déjà couverte » dès
qu'une ligne `contrat_cddu_dates` existe pour cet artiste sur cette date,
rattachée à un CDDU dont le statut n'est pas `archived` (voir §12 pour le
cycle de vie complet).

---

## 6. Workflow prioritaire — CDDU simple en un clic

C'est le chemin que 90 % des usages doivent emprunter. Aucune question,
aucun assistant, aucun choix de type de contrat.

```
Fiche Prestation
        │
        ▼
Liste des artistes engagés (prestation_participants, §3 — réalisé)
        │
        ▼
Chaque artiste porte une action directe :  [ Créer le CDDU ]
        │
        ▼  (un clic)
Le logiciel exécute automatiquement, sans aucune interruption :
  1. Création du CDDU (statut Brouillon), numéro CDDU-AAAA-XXXX attribué
  2. Instantané figé producteur_*/artiste_* (Producteur actif + fiche Artiste)
  3. Une ligne contrat_cddu_dates : date = date de la prestation,
     prestation_id = cette prestation, nombre_cachets = 1
  4. Génération DOCX (contrat_cddu.docx + PlaceholderEngine, inchangé)
  5. Export PDF (PdfConverter, inchangé)
        │
        ▼
Statut du CDDU : Brouillon → PDF généré, positionné automatiquement dès que
l'export PDF réussit (règle d'avancement automatique déjà définie au §12 —
« Validé » reste un statut manuel, volontairement non déclenché par cette
action rapide, l'utilisateur le positionne s'il relit et valide le contenu)
```

Tous les champs pré-remplis (§8) restent modifiables **après coup**, en
rouvrant le CDDU créé — mais la création elle-même ne pose aucune question et
ne bloque sur rien : c'est le point central de ce sprint. L'utilisateur peut
enchaîner « Créer le CDDU » sur chaque artiste de la liste en quelques
secondes, un contrat DOCX+PDF prêt par artiste.

---

## 7. Workflow avancé — Assistant de mensualisation

Chemin **séparé**, jamais mélangé au précédent. Accessible via une action
distincte, par exemple un second bouton visible à côté de la liste des
artistes d'une Prestation : « Créer un CDDU mensualisé », ou depuis le module
Contrats de travail lui-même.

```
Créer un CDDU mensualisé  (action séparée, avec assistant)
        │
        ▼
Choisir l'artiste concerné
        │
        ▼
Le logiciel recherche automatiquement toutes les Prestations du mois
concerné où cet artiste est engagé (via prestation_participants, §3, en plus de
prestations.artist_id pour compatibilité)
        │
        ▼
Filtrage automatique : seules les dates NON déjà rattachées à un CDDU actif
sont proposées (voir règle d'exclusion ci-dessous)
        │
        ▼
☑ Tout sélectionner  /  ☑ sélection individuelle par date
        │
        ▼
Nombre total de cachets affiché en temps réel (somme des lignes cochées)
        │
        ▼
Validation → un seul CDDU créé, une ligne contrat_cddu_dates par date cochée
        │
        ▼
Génération DOCX / Export PDF (même mécanique que le workflow prioritaire)
```

### Règle d'exclusion des dates déjà contractualisées

- Une date où l'artiste a déjà une ligne `contrat_cddu_dates` rattachée à un
  CDDU dont le statut **n'est pas** `Archivé` est considérée comme déjà
  couverte et **n'est jamais proposée** par défaut dans l'assistant — elle ne
  doit pas être recréée par erreur dans un second contrat.
- **Option d'affichage des dates archivées** : un interrupteur, désactivé par
  défaut (« Afficher aussi les dates de contrats archivés »), permet de faire
  réapparaître ces dates dans la liste, visuellement distinguées (par
  exemple grisées, avec la mention du numéro de CDDU archivé d'origine), pour
  le cas rare où une reprise est nécessaire (contrat archivé par erreur,
  correction a posteriori). Activer cette option n'empêche jamais de créer un
  nouveau CDDU sur ces dates si l'utilisateur le décide explicitement — le
  logiciel avertit, il ne bloque jamais.

Cette page reste la **seule** du module où l'utilisateur manipule
explicitement plusieurs dates et plusieurs prestations à la fois — le
workflow prioritaire (§6) n'expose jamais cette complexité.

---

## 8. Préremplissage automatique (commun aux deux workflows)

**Depuis Paramètres YGNT (Producteur actif)** → `producteur_*`, inchangé
depuis le Sprint 14.0.

**Depuis la fiche Artiste** → `artiste_*` (nom, adresse, téléphone, email,
date/lieu de naissance, numéro de sécurité sociale, numéro de congés
spectacle, fonction ← `instrument`), inchangé depuis le Sprint 14.0.

**Depuis la ou les Prestations concernées** → `prestation_objet`,
`prestation_lieu`, `prestation_ville`, `prestation_reference` (prestation de
départ pour le contexte de l'article Objet), dates et cachets alimentant
`contrat_cddu_dates`. Dans le workflow prioritaire, une seule prestation ;
dans l'assistant de mensualisation, potentiellement plusieurs (voir §11 pour
le comportement de l'article Objet dans ce cas).

Dans les deux workflows, tout champ pré-rempli reste modifiable après
création — rien n'est jamais verrouillé.

---

## 9. Le numéro d'objet — inchangé

Champ `numero_objet` et placeholder `{{numero_objet}}`, toujours vide,
aucune logique de calcul ou de génération. Décision reportée à un sprint
ultérieur.

---

## 10. Défraiements — inchangé

Article Déplacement / Hébergement / Repas / Autres / Montant libre, tous
optionnels, préremplis uniquement si une information exploitable existe déjà
(recherche transverse façon `IntermiPaieDialog`), sinon laissés vides,
disparaît entièrement du DOCX si rien n'est renseigné (suppression
automatique des paragraphes vides de `PlaceholderEngine`). Inchangé par la
distinction workflow simple/mensualisé.

---

## 11. Placeholders du futur template DOCX (`templates/contrat_cddu.docx`)

Inchangé depuis le Sprint 14.1 :

```
{{numero}}
{{producteur_nom}} {{producteur_adresse}} {{producteur_postal_code}}
{{producteur_city}} {{producteur_siret}} {{producteur_representant}}
{{producteur_fonction}} {{producteur_convention_collective}}

{{artiste_nom}} {{artiste_date_naissance}} {{artiste_lieu_naissance}}
{{artiste_adresse}} {{artiste_postal_code}} {{artiste_city}}
{{artiste_numero_secu}} {{artiste_numero_conges_spectacle}}
{{artiste_fonction}}

{{prestation_objet}} {{prestation_lieu}} {{prestation_ville}}
{{numero_objet}}                      -- toujours vide, §9

{{date_debut}} {{date_fin}}           -- dérivées, min/max de contrat_cddu_dates
{{dates_travaillees}}                 -- une ligne par entrée de contrat_cddu_dates,
                                          triées par date
{{nombre_total_cachets}}              -- somme des cachets, affichée explicitement

{{remuneration_brute|currency}}

{{defraiement_deplacement|currency}} {{defraiement_hebergement|currency}}
{{defraiement_repas|currency}} {{defraiement_autres_libelle}}
{{defraiement_autres_montant|currency}} {{defraiement_montant_libre_libelle}}
{{defraiement_montant_libre_montant|currency}}

{{ville_signature}} {{date_signature}}
```

Comportement de l'article **Objet** confirmé : pour un CDDU simple (workflow
prioritaire), `prestation_objet`/`prestation_lieu`/`prestation_ville`
décrivent fidèlement l'unique prestation concernée. Pour un CDDU mensualisé,
ces champs restent ceux de la prestation choisie comme contexte général ;
le détail exhaustif (dates, prestations d'origine, cachets) reste porté par
`{{dates_travaillees}}`, jamais résumé ni fusionné.

Clauses fixes (Rupture anticipée, Retraite et congés payés, Absence-maladie,
Médecine du travail, Assurances, Litiges) : texte légal figé, inchangé.

---

## 12. Cycle de vie et statuts — inchangé depuis le Sprint 14.1

```
Brouillon → Validé → PDF généré → Envoyé → Signé → Archivé
```

Le statut reste librement modifiable manuellement à tout moment et ne
bloque aucune action. Seule précision apportée par ce sprint : le workflow
prioritaire (§6) déclenche automatiquement le passage à **PDF généré** dès
que l'export PDF réussit (sans jamais faire reculer un statut déjà plus
avancé), mais ne positionne jamais automatiquement **Validé** — ce statut
reste une décision humaine explicite. « Envoyé » et « Signé » restent des
statuts manuels pour ce sprint, réservés pour une future intégration de
signature électronique. « Archivé » reste l'état terminal manuel utilisé par
la règle d'exclusion de l'assistant de mensualisation (§7).

Aucune régression sur le contrat de cession (toujours trois statuts,
inchangé).

---

## 13. Règles métier

Règles conservées des Sprints 14.0/14.1 : une seule entité personne
(Artiste), numérotation `CDDU-{année}-{séquence}`, instantané figé, aucun
calcul de paie, défraiements optionnels, aucun lien direct à un
Organisateur, génération DOCX toujours depuis le template unique, PDF
toujours dérivé du DOCX, contrat de cession inchangé, `contrat_cddu_dates`
comme seule source de vérité des dates/cachets, type de contrat jamais
stocké (dérivé), numéro d'objet toujours vide.

Règles ajoutées ou précisées au Sprint 14.2 :

- **Le CDDU simple (1 date = 1 musicien = 1 CDDU) est le workflow de
  référence** : il doit rester accessible en un clic, sans question ni
  écran intermédiaire, depuis la liste des artistes d'une Prestation.
- **La mensualisation ne doit jamais interférer avec le workflow simple** :
  elle vit exclusivement dans un point d'entrée séparé (« Créer un CDDU
  mensualisé »), jamais comme une étape ou une question posée dans le
  workflow prioritaire.
- **Une date déjà couverte par un CDDU actif (non archivé) n'est jamais
  proposée par défaut** dans l'assistant de mensualisation, pour éviter la
  double-contractualisation involontaire d'une même date.
- **Les dates couvertes par un CDDU archivé restent accessibles** via une
  option d'affichage explicite, désactivée par défaut, pour permettre une
  reprise exceptionnelle sans jamais bloquer l'utilisateur.
- **La liste des artistes d'une Prestation** (`prestation_participants`, §3,
  livrée au Sprint 15.5) est une table additive, sans impact sur
  `prestations.artist_id` ni sur le contrat de cession.

---

## 14. Impacts sur les modules et services existants

Impacts déjà listés aux Sprints 14.0/14.1 (`artists`, `producteurs`,
`PdfConverter`, `PlaceholderEngine`, `IntermiPaieDialog`, sidebar,
templates, Dossier de Prestation via `contrat_cddu_dates`, `app/api`/
`app/web`) restent valables sans changement.

Impacts précisés ou ajoutés au Sprint 14.2 :

| Élément existant | Impact |
|---|---|
| `prestations` / `PrestationService` | **Additif, réalisé au Sprint 15.5** — table de liaison `prestation_participants` (§3), nécessaire à l'affichage de la liste des artistes engagés sur une Prestation. `prestations.artist_id` reste inchangé et continue de servir tel quel au contrat de cession. |
| Écran Prestation (UI) | **Additif** — chaque artiste de la liste porte désormais une action directe « Créer le CDDU » (workflow prioritaire, §6), et un point d'entrée séparé « Créer un CDDU mensualisé » (§7) est ajouté à proximité, sans jamais se substituer au premier. |
| `MigrationManager` | **Additif** — la table `prestation_participants` (Sprint 15.5) s'ajoute à `contrats_cddu`, `contrat_cddu_dates`, `contrat_cddu_history` (Sprint 15.0). |

---

## 15. Évolution UI prévue (roadmap, non développée à ce stade) — statut visuel du CDDU par artiste

Documentée ici pour mémoire, **non implémentée dans ce sprint**, à inscrire
comme évolution future dans `ROADMAP.md` lors d'un prochain sprint dédié à
l'interface :

Dans la liste des artistes d'une Prestation, une colonne **CDDU** afficherait
un indicateur visuel synthétique par artiste, dérivé du statut du CDDU le
plus avancé existant pour cet artiste sur cette prestation (jamais une
donnée stockée séparément — même principe de dérivation que le reste de ce
document) :

```
Anthony      🟢 Créé
José         🔴 À créer
Nicolas      🟡 Signé
```

- 🔴 À créer — aucun CDDU n'existe encore pour cet artiste sur cette
  prestation.
- 🟢 Créé — un CDDU existe (Brouillon à Envoyé), pas encore signé.
- 🟡 Signé — le CDDU de cet artiste est au statut Signé (ou au-delà,
  Archivé).

Cette colonne donnerait, en un coup d'œil depuis la fiche Prestation, l'état
de couverture RH complet d'un événement (« qui a déjà son contrat, qui n'en a
pas encore »), en cohérence directe avec le workflow prioritaire du §6.
Aucune action n'est requise pour ce sprint au-delà de cette mention : elle
ne modifie ni le schéma, ni aucun service, ni aucun écran existant.

---

## 16. Pourquoi cette architecture ne nécessite pas de refonte future

- **Le workflow prioritaire et l'assistant de mensualisation partagent
  exactement le même schéma** (`contrats_cddu` + `contrat_cddu_dates`) : le
  premier ne fait qu'y écrire une seule ligne automatiquement, le second en
  écrit plusieurs après sélection — aucune divergence de modèle entre les
  deux chemins.
- **`prestation_participants` comble un prérequis réel sans toucher à
  l'existant** : `prestations.artist_id` continue de fonctionner à
  l'identique pour tout ce qui concerne déjà le contrat de cession.
- **La règle d'exclusion des dates déjà contractualisées repose sur des
  colonnes déjà prévues** (`contrat_cddu_dates.prestation_id` +
  `contrats_cddu.status`) — aucune nouvelle colonne nécessaire pour la
  livrer.
- **Le statut visuel par artiste (§15) est purement dérivé** : il pourra être
  ajouté à l'interface plus tard sans aucune migration, exactement comme les
  colonnes « DOCX (oui/non) » déjà affichées ailleurs dans l'application.
- **Zéro régression** : contrat de cession, CDDU simple du Sprint 14.0 et
  mensualisation du Sprint 14.1 continuent de fonctionner à l'identique ; ce
  sprint réordonne l'expérience utilisateur, il ne change aucune donnée déjà
  actée.

---

Ce document constitue la référence à jour pour le développement futur du
module Contrat de travail (CDDU) : Sprint 14.0 (Artiste comme salarié),
Sprint 14.1 (mensualisation via `contrat_cddu_dates`), Sprint 14.2 (workflow
prioritaire en un clic, assistant de mensualisation séparé, exclusion des
dates déjà contractualisées, statut visuel documenté pour plus tard). Aucune
implémentation n'a été réalisée à ce stade.
