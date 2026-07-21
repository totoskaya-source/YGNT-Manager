let container = null;

function getContainer() {
  if (!container) {
    container = document.createElement("div");
    container.className = "toast-container";
    document.body.append(container);
  }
  return container;
}

/** Notification transitoire (succès/erreur), distincte de la bannière
 * d'erreur globale qui reste affichée jusqu'à fermeture explicite. */
export function showToast(message, type = "success", duree = 4000) {
  const toast = document.createElement("div");
  toast.className = `toast toast--${type}`;
  toast.setAttribute("role", "status");
  toast.textContent = message;

  getContainer().append(toast);
  setTimeout(() => toast.remove(), duree);
}
