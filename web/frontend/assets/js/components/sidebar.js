import { navigate } from "../router.js";

// Structure reprise de 03_UX_ARCHITECTURE.md §1.1. Seul "Cockpit" est
// implémenté à ce stade (T5) : les autres entrées sont des emplacements
// réservés, visibles mais non cliquables, pour qu'ajouter un futur module
// n'exige qu'un changement de configuration ici, pas une refonte du menu.
const NAV_ITEMS = [
  { label: "Cockpit", path: "/", enabled: true },
  { label: "Prestations", enabled: false },
  { label: "Organisateurs", enabled: false },
  { label: "Artistes", enabled: false },
  { label: "Formations", enabled: false },
  { label: "Contrats", enabled: false },
  { label: "CDDU", enabled: false },
  { label: "Devis", enabled: false },
  { label: "Factures", enabled: false },
  { label: "Paiements", enabled: false },
  { label: "Documents", enabled: false },
  { label: "Paramètres", enabled: false },
];

export function createSidebar() {
  const nav = document.createElement("nav");
  nav.className = "app-sidebar";
  nav.setAttribute("aria-label", "Navigation principale");

  const list = document.createElement("ul");
  list.className = "nav-list";

  for (const item of NAV_ITEMS) {
    const li = document.createElement("li");
    li.className = "nav-list__item";

    const link = document.createElement("a");
    link.className = `nav-link${item.enabled ? "" : " is-disabled"}`;
    link.textContent = item.label;

    if (item.enabled) {
      link.href = `#${item.path}`;
      link.addEventListener("click", (event) => {
        event.preventDefault();
        navigate(item.path);
      });
    } else {
      link.href = "#";
      link.setAttribute("aria-disabled", "true");
      link.tabIndex = -1;
      const hint = document.createElement("span");
      hint.className = "nav-list__hint";
      hint.textContent = "(bientôt)";
      link.append(hint);
    }

    li.append(link);
    list.append(li);
  }

  nav.append(list);
  return nav;
}
