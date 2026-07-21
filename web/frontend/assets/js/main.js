import * as api from "./api.js";
import { createErrorBanner } from "./components/error-banner.js";
import { mountAppShell } from "./components/layout.js";
import { createSpinner } from "./components/spinner.js";
import * as router from "./router.js";
import { setUser } from "./state.js";
import { renderHomeView } from "./views/home-view.js";
import { renderLoginView } from "./views/login-view.js";

const appRoot = document.getElementById("app");

// La bannière d'erreur globale est montée une seule fois, en dehors du
// routeur : elle doit rester visible quel que soit l'écran (connexion,
// démarrage, ou coquille authentifiée) — voir components/layout.js.
const viewContainer = document.createElement("div");

router.register("/login", {
  requiresAuth: false,
  render(root) {
    renderLoginView(root);
  },
});

router.register("/", {
  requiresAuth: true,
  render(root) {
    const content = mountAppShell(root);
    renderHomeView(content);
  },
});

async function boot() {
  appRoot.append(createErrorBanner(), viewContainer);

  const bootScreen = document.createElement("div");
  bootScreen.className = "boot-screen";
  bootScreen.append(createSpinner({ standalone: true }));
  viewContainer.append(bootScreen);

  const restored = await api.restoreSession();
  if (restored) {
    try {
      setUser(api.toUserState(await api.fetchCurrentUser()));
    } catch {
      setUser(null);
    }
  } else {
    setUser(null);
  }

  // init() s'abonne à l'état : le premier rendu est déclenché par ce même
  // abonnement (voir router.js), pas besoin d'un appel explicite ici.
  router.init(viewContainer, "/login");
}

boot();
