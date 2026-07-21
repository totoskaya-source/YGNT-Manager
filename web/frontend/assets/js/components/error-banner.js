import { clearGlobalError, subscribe } from "../state.js";

/** Bannière d'erreur globale, montée une fois dans la coquille de l'app. */
export function createErrorBanner() {
  const container = document.createElement("div");

  subscribe((state) => {
    container.innerHTML = "";
    if (!state.globalError) {
      return;
    }
    const banner = document.createElement("div");
    banner.className = "error-banner";
    banner.setAttribute("role", "alert");

    const message = document.createElement("span");
    message.textContent = state.globalError;

    const dismiss = document.createElement("button");
    dismiss.type = "button";
    dismiss.className = "error-banner__dismiss";
    dismiss.setAttribute("aria-label", "Fermer");
    dismiss.textContent = "×";
    dismiss.addEventListener("click", clearGlobalError);

    banner.append(message, dismiss);
    container.append(banner);
  });

  return container;
}
