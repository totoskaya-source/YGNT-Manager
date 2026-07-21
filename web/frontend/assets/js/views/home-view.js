import { getState } from "../state.js";

/** Écran d'accueil après connexion. Aucune donnée métier : le Cockpit
 * orienté actions (00_PRODUCT_VISION.md §7) est un chantier ultérieur. */
export function renderHomeView(root) {
  const { user } = getState();

  const card = document.createElement("div");
  card.className = "card";

  const title = document.createElement("h1");
  title.textContent = `Bienvenue, ${user.prenom} ${user.nom}`;

  const societe = document.createElement("p");
  societe.textContent = `Vous êtes connecté à : ${user.societeNom}`;

  const note = document.createElement("p");
  note.style.color = "var(--color-text-muted)";
  note.textContent =
    "Le Cockpit orienté actions (prestations à traiter, devis à relancer...) sera construit dans un prochain sprint.";

  card.append(title, societe, note);
  root.append(card);
}
