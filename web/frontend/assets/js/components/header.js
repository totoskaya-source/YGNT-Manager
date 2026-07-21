import * as api from "../api.js";
import { getState, setUser } from "../state.js";

export function createHeader({ onToggleSidebar }) {
  const header = document.createElement("header");
  header.className = "app-header";

  const menuToggle = document.createElement("button");
  menuToggle.type = "button";
  menuToggle.className = "app-header__menu-toggle";
  menuToggle.setAttribute("aria-label", "Afficher/masquer le menu");
  menuToggle.textContent = "☰";
  menuToggle.addEventListener("click", onToggleSidebar);

  const brand = document.createElement("div");
  brand.className = "app-header__brand";
  brand.textContent = "YGNT Manager";

  const societe = document.createElement("div");
  societe.className = "app-header__societe";

  const user = document.createElement("div");
  user.className = "app-header__user";

  const userName = document.createElement("span");

  const logoutButton = document.createElement("button");
  logoutButton.type = "button";
  logoutButton.className = "app-header__logout";
  logoutButton.textContent = "Déconnexion";
  logoutButton.addEventListener("click", async () => {
    await api.logout();
    setUser(null);
  });

  const refresh = (state) => {
    societe.textContent = state.user ? state.user.societeNom : "";
    userName.textContent = state.user ? `${state.user.prenom} ${state.user.nom}` : "";
  };

  user.append(userName, logoutButton);
  header.append(menuToggle, brand, societe, user);

  refresh(getState());
  return { element: header, refresh };
}
