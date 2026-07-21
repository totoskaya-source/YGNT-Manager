/** Modal générique : overlay + panneau, fermeture au clic hors panneau ou
 * Échap. `buildContent(panel, close)` construit le contenu (titre déjà posé
 * par l'appelant via `title`). */
export function openModal({ title, buildContent }) {
  const overlay = document.createElement("div");
  overlay.className = "modal-overlay";

  const panel = document.createElement("div");
  panel.className = "modal-panel";
  panel.setAttribute("role", "dialog");
  panel.setAttribute("aria-modal", "true");

  const heading = document.createElement("h2");
  heading.textContent = title;
  panel.append(heading);
  overlay.append(panel);

  function close() {
    document.removeEventListener("keydown", onKeydown);
    overlay.remove();
  }

  function onKeydown(event) {
    if (event.key === "Escape") {
      close();
    }
  }

  overlay.addEventListener("click", (event) => {
    if (event.target === overlay) {
      close();
    }
  });
  document.addEventListener("keydown", onKeydown);

  document.body.append(overlay);
  buildContent(panel, close);

  return { close };
}
