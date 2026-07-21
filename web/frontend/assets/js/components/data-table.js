/** Tableau générique, réutilisable par de futurs modules : `columns` décrit
 * les colonnes ({key, label, sortable, render(row)}), `rows` les données
 * déjà chargées (pas de logique de tri/pagination ici, uniquement du
 * rendu). */
export function renderDataTable(container, { columns, rows, sort, onSortChange, emptyMessage = "Aucun résultat." }) {
  container.innerHTML = "";

  const scroll = document.createElement("div");
  scroll.className = "table-scroll";

  const table = document.createElement("table");
  table.className = "data-table";

  const thead = document.createElement("thead");
  const headRow = document.createElement("tr");
  for (const column of columns) {
    const th = document.createElement("th");
    if (column.sortable) {
      const button = document.createElement("button");
      button.type = "button";
      const actif = sort && sort.colonne === column.key;
      const fleche = actif ? (sort.ordre === "asc" ? " ▲" : " ▼") : "";
      button.textContent = column.label + fleche;
      button.addEventListener("click", () => onSortChange(column.key));
      th.append(button);
    } else {
      th.textContent = column.label;
    }
    headRow.append(th);
  }
  thead.append(headRow);

  const tbody = document.createElement("tbody");
  if (rows.length === 0) {
    const tr = document.createElement("tr");
    const td = document.createElement("td");
    td.colSpan = columns.length;
    td.className = "data-table__empty";
    td.textContent = emptyMessage;
    tr.append(td);
    tbody.append(tr);
  } else {
    for (const row of rows) {
      const tr = document.createElement("tr");
      for (const column of columns) {
        const td = document.createElement("td");
        const valeur = column.render ? column.render(row) : row[column.key];
        if (valeur instanceof HTMLElement) {
          td.append(valeur);
        } else {
          td.textContent = valeur ?? "";
        }
        tr.append(td);
      }
      tbody.append(tr);
    }
  }

  table.append(thead, tbody);
  scroll.append(table);
  container.append(scroll);
}
