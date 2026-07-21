export function renderPagination(container, { page, taillePage, total, onPageChange }) {
  container.innerHTML = "";
  const totalPages = Math.max(1, Math.ceil(total / taillePage));

  const wrapper = document.createElement("div");
  wrapper.className = "pagination";

  const precedent = document.createElement("button");
  precedent.type = "button";
  precedent.className = "button button--secondary button--small";
  precedent.textContent = "Précédent";
  precedent.disabled = page <= 1;
  precedent.addEventListener("click", () => onPageChange(page - 1));

  const info = document.createElement("span");
  info.textContent = `Page ${page} sur ${totalPages} (${total} résultat${total > 1 ? "s" : ""})`;

  const suivant = document.createElement("button");
  suivant.type = "button";
  suivant.className = "button button--secondary button--small";
  suivant.textContent = "Suivant";
  suivant.disabled = page >= totalPages;
  suivant.addEventListener("click", () => onPageChange(page + 1));

  wrapper.append(precedent, info, suivant);
  container.append(wrapper);
}
