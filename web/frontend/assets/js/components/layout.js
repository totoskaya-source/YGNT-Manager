import { subscribe } from "../state.js";
import { createHeader } from "./header.js";
import { createSidebar } from "./sidebar.js";

/** Construit la coquille de l'application (Header + Sidebar + Contenu) et
 * la monte dans `root`. Renvoie l'élément de contenu, où le routeur monte
 * chaque écran.
 *
 * La bannière d'erreur globale n'est pas montée ici : elle doit rester
 * visible même sur l'écran de connexion (avant que cette coquille n'existe),
 * voir main.js. */
export function mountAppShell(root) {
  root.innerHTML = "";

  const shell = document.createElement("div");
  shell.className = "app-shell";

  const body = document.createElement("div");
  body.className = "app-body";

  const content = document.createElement("main");
  content.className = "app-content";

  const contentInner = document.createElement("div");
  content.append(contentInner);

  const sidebar = createSidebar();

  const header = createHeader({
    onToggleSidebar: () => shell.classList.toggle("sidebar-open"),
  });

  body.append(sidebar, content);
  shell.append(header.element, body);
  root.append(shell);

  subscribe(header.refresh);

  return contentInner;
}
