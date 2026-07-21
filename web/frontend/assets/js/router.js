// Routeur minimal par hash : suffisant pour deux écrans (connexion, accueil).
// Ajouter un futur module = un appel à `register()` de plus, sans toucher au
// reste du routeur.
//
// Réagit aussi aux changements de statut d'authentification (pas seulement
// au hash) : une déconnexion déclenchée depuis n'importe où (Header, session
// expirée...) doit renvoyer vers /login sans que ce code appelant ait à
// connaître le routeur.

import { getState, subscribe } from "./state.js";

const routes = new Map();
let mountPoint = null;
let notFoundRoute = "/";
let lastStatus = null;

/**
 * @param {string} path ex: "/login"
 * @param {{render: (el: HTMLElement) => void, requiresAuth: boolean}} definition
 */
export function register(path, definition) {
  routes.set(path, definition);
}

export function init(element, defaultPath) {
  mountPoint = element;
  notFoundRoute = defaultPath;
  window.addEventListener("hashchange", render);
  subscribe((state) => {
    if (state.status !== lastStatus) {
      lastStatus = state.status;
      render();
    }
  });
}

export function navigate(path) {
  if (currentPath() === path) {
    render();
  } else {
    window.location.hash = `#${path}`;
  }
}

function currentPath() {
  return window.location.hash.replace(/^#/, "") || "/";
}

export function render() {
  if (getState().status === "booting") {
    return; // rien à afficher tant que la session n'est pas résolue (main.js)
  }

  const path = currentPath();
  const route = routes.get(path) || routes.get(notFoundRoute);
  const isAuthenticated = getState().status === "authenticated";

  if (route.requiresAuth && !isAuthenticated) {
    navigate("/login");
    return;
  }
  if (!route.requiresAuth && isAuthenticated && path === "/login") {
    navigate("/");
    return;
  }

  mountPoint.innerHTML = "";
  route.render(mountPoint);
}
