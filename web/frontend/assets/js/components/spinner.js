export function createSpinner({ standalone = false } = {}) {
  const span = document.createElement("span");
  span.className = standalone ? "spinner spinner--standalone" : "spinner";
  span.setAttribute("role", "status");
  span.setAttribute("aria-label", "Chargement en cours");
  return span;
}
