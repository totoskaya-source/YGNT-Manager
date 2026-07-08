# YGNT Manager - Roadmap officielle vers la v1.0

Cette roadmap reflète l'état réel du logiciel et complète `PROJECT.md` (vision) et
`BUSINESS_RULES.md` (règles métier). Chaque étape doit se terminer par une
application qui démarre sans erreur et des tests manuels validés.

---

## État actuel : v0.4.7

### Modules livrés

- **Artistes** — CRUD complet (fiche complète : coordonnées, informations légales
  et bancaires, cachet habituel), recherche, tableau.
- **Organisateurs** — CRUD complet (fiche complète : coordonnées, informations
  légales, bancaires, TVA, représentant/fonction, site internet), recherche,
  tableau.
- **Contrats** — module prioritaire, le plus avancé :
  - Numérotation automatique (`YGNT-{année}-{séquence}`).
  - Dialogue en onglets (Artiste / Organisateur / Prestation / Conditions
    financières / Aperçu), redimensionnable, taille mémorisée.
  - Sélection d'un Artiste et d'un Organisateur avec pré-remplissage automatique
    de tous les champs correspondants (fini la ressaisie manuelle).
  - Séparation correcte entre l'adresse du siège de l'organisateur et le lieu réel
    de la prestation.
  - Génération DOCX à partir du template `contrat_cession.docx`.
  - Export PDF fidèle au DOCX (conversion via Microsoft Word / COM).
  - Historique des actions par contrat.

### Non livré à ce stade

- **Dashboard** — annoncé dans `PROJECT.md` mais pas encore implémenté (page vide
  aujourd'hui).

---

## v0.5 — Tableau de bord

Objectif : donner une vue d'ensemble immédiate en ouvrant l'application.

- Indicateurs clés : nombre de contrats par statut, prochaines prestations,
  chiffre d'affaires du mois/de l'année en cours.
- Raccourcis vers les actions les plus fréquentes (nouveau contrat, nouvel
  artiste, nouvel organisateur).

---

## v0.6 — Devis

Objectif : pouvoir chiffrer une prestation avant de s'engager, sans ressaisie.

- Nouveau module Devis, sur le même modèle que Contrats (Artiste / Organisateur /
  Prestation / Conditions financières / Aperçu, pré-remplissage automatique).
- Génération d'un document DOCX de devis à partir d'un template dédié.
- Transformation d'un devis accepté en contrat, sans ressaisie des informations
  déjà validées.

---

## v0.7 — Factures

Objectif : clôturer administrativement un contrat honoré.

- Génération d'une facture à partir d'un contrat (cachet, acompte, TVA déjà
  saisis sur le contrat).
- Suivi du statut de facturation (émise, envoyée, payée).

---

## v0.8 — Paiements

Objectif : savoir en un coup d'œil ce qui reste dû.

- Suivi des règlements (acompte / solde) liés à un contrat ou une facture.
- Alerte sur les échéances dépassées.

---

## v0.9 — Agenda et Documents

Objectif : centraliser le calendrier et les pièces jointes d'un dossier.

- Agenda : vue calendrier des prestations à venir, à partir des contrats/devis
  existants (pas de double saisie de dates).
- Documents : espace de stockage des pièces jointes par artiste, organisateur ou
  contrat (fiches techniques, riders, autorisations...).

---

## v0.9.x — Paramètres et Statistiques

Objectif : finaliser les modules prévus avant la stabilisation v1.0.

- Paramètres : coordonnées de la structure émettrice (YGNT Production), template
  DOCX par défaut, préférences d'export.
- Statistiques : chiffre d'affaires par artiste/organisateur/période, nombre de
  prestations, taux de transformation devis → contrat.

---

## v1.0 — Stabilisation et distribution

Objectif : version destinée à un usage réel élargi, au-delà du poste actuel.

- Revue complète de non-régression sur tous les modules (Artistes, Organisateurs,
  Contrats, Devis, Factures, Paiements, Agenda, Documents, Paramètres,
  Statistiques).
- Cohérence visuelle et ergonomique sur l'ensemble du logiciel.
- Fiabilisation des exports (DOCX, PDF) et de la base de données pour un usage
  quotidien sans supervision technique.
- Packaging de l'application pour une installation simple sur un nouveau poste.

---

## Principe directeur

Chaque étape de cette roadmap ne sera considérée terminée que si :

- l'application démarre sans exception ;
- la génération DOCX et l'export PDF existants ne sont pas cassés ;
- les contrats déjà créés restent lisibles et générables ;
- un contrat complet reste réalisable en moins de deux minutes.
