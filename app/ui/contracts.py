from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.models.contract import Contract
from app.services.contract_service import ContractService
from app.services.facture_service import FactureService
from app.ui.contract_dialog import ContractDialog
from app.ui.dialogs import confirm_delete, notify_success
from app.ui.facture_dialog import FactureDialog
from app.ui.theme import mark_destructive, style_page_title, style_table


class ContractsPage(QWidget):
    HEADERS = (
        "ID",
        "Numero",
        "Date",
        "Organisateur",
        "Spectacle",
        "Montant",
        "Statut",
        "DOCX",
        "PDF",
        "Generation",
    )

    def __init__(
        self,
        service: ContractService | None = None,
        facture_service: FactureService | None = None,
    ) -> None:
        super().__init__()

        self.service = service or ContractService()
        self.facture_service = facture_service or FactureService()
        self._contracts: list[Contract] = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        title = QLabel("Contrats")
        style_page_title(title)
        layout.addWidget(title)

        layout.addLayout(self._build_toolbar())

        self.table = QTableWidget()
        self.table.setColumnCount(len(self.HEADERS))
        self.table.setHorizontalHeaderLabels(self.HEADERS)
        self.table.setAlternatingRowColors(True)
        self.table.setSortingEnabled(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setColumnHidden(0, True)
        self.table.itemDoubleClicked.connect(self.edit_selected_contract)
        self.table.itemSelectionChanged.connect(self._sync_buttons)
        style_table(self.table)

        header = self.table.horizontalHeader()
        header.setSortIndicatorShown(True)
        header.setSectionsClickable(True)
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        header.setStretchLastSection(True)

        layout.addWidget(self.table)

        self.refresh_table()
        self._sync_buttons()

    def _build_toolbar(self) -> QHBoxLayout:
        toolbar = QHBoxLayout()
        toolbar.setSpacing(8)

        self.btn_new = QPushButton("Nouveau")
        self.btn_edit = QPushButton("Modifier")
        self.btn_duplicate = QPushButton("Dupliquer")
        self.btn_delete = QPushButton("Supprimer")
        mark_destructive(self.btn_delete)
        self.btn_generate = QPushButton("Generer DOCX")
        self.btn_export_pdf = QPushButton("Export PDF")
        self.btn_open = QPushButton("Ouvrir DOCX")
        self.btn_open_pdf = QPushButton("Ouvrir PDF")
        self.btn_create_facture = QPushButton("🧾 Creer une facture")
        self.btn_refresh = QPushButton("Actualiser")
        self.btn_history = QPushButton("Historique")

        self.search = QLineEdit()
        self.search.setPlaceholderText("Rechercher un contrat...")
        self.search.setClearButtonEnabled(True)
        self.search.textChanged.connect(self.refresh_table)

        self.status_filter = QComboBox()
        self.status_filter.addItem("Tous les statuts", "all")
        self.status_filter.addItem("Brouillon", "draft")
        self.status_filter.addItem("Valide", "validated")
        self.status_filter.addItem("Signe", "signed")
        self.status_filter.currentIndexChanged.connect(self.refresh_table)

        self.btn_new.clicked.connect(self.new_contract)
        self.btn_edit.clicked.connect(self.edit_selected_contract)
        self.btn_duplicate.clicked.connect(self.duplicate_selected_contract)
        self.btn_delete.clicked.connect(self.delete_selected_contract)
        self.btn_generate.clicked.connect(self.generate_selected_docx)
        self.btn_export_pdf.clicked.connect(self.export_selected_pdf)
        self.btn_open.clicked.connect(self.open_selected_document)
        self.btn_open_pdf.clicked.connect(self.open_selected_pdf)
        self.btn_create_facture.clicked.connect(self.create_facture_from_selected_contract)
        self.btn_refresh.clicked.connect(self.refresh_table)
        self.btn_history.clicked.connect(self.show_selected_history)

        for button in (
            self.btn_new,
            self.btn_edit,
            self.btn_duplicate,
            self.btn_delete,
            self.btn_generate,
            self.btn_export_pdf,
            self.btn_open,
            self.btn_open_pdf,
            self.btn_create_facture,
            self.btn_history,
            self.btn_refresh,
        ):
            toolbar.addWidget(button)

        toolbar.addStretch()
        toolbar.addWidget(self.status_filter)
        toolbar.addWidget(self.search, 1)
        return toolbar

    def new_contract(self) -> None:
        # Le dialogue s'enregistre desormais lui-meme (Sprint 12.0) : il reste
        # ouvert apres la creation pour generer immediatement DOCX/PDF, sans
        # repasser par cette liste. On se contente de rafraichir au retour.
        dialog = ContractDialog(self, service=self.service)
        dialog.exec()
        self.refresh_table()

    def edit_selected_contract(self, *_args: Any) -> None:
        contract = self._selected_contract()

        if contract is None:
            QMessageBox.information(self, "Modification", "Selectionnez un contrat.")
            return

        dialog = ContractDialog(self, contract=contract, service=self.service)
        dialog.exec()
        self.refresh_table()

    def duplicate_selected_contract(self) -> None:
        contract_id = self._selected_contract_id()
        if contract_id is None:
            QMessageBox.information(self, "Duplication", "Selectionnez un contrat.")
            return

        self._run_action(
            lambda: self.service.duplicate_contract(contract_id),
            "Contrat duplique.",
        )
        self.refresh_table()

    def delete_selected_contract(self) -> None:
        contract = self._selected_contract()

        if contract is None or contract.id is None:
            QMessageBox.information(self, "Suppression", "Selectionnez un contrat.")
            return

        label = f"le contrat {contract.contract_number or contract.id}"

        if confirm_delete(self, label):
            self._run_action(
                lambda: self.service.delete_contract(int(contract.id)),
                "Contrat supprime.",
            )
            self.refresh_table()

    def generate_selected_docx(self) -> None:
        contract_id = self._selected_contract_id()
        if contract_id is None:
            QMessageBox.information(self, "Generation", "Selectionnez un contrat.")
            return

        contract = self.service.get_contract(contract_id)
        if contract is None:
            self.refresh_table()
            return

        preview = self.service.preview(contract)
        response = QMessageBox.question(
            self,
            "Apercu avant generation",
            f"{preview}\n\nGenerer le document DOCX ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes,
        )

        if response != QMessageBox.StandardButton.Yes:
            return

        path = self._run_action(
            lambda: self.service.generate_docx(contract_id),
            "Document DOCX genere.",
        )
        self.refresh_table()
        if path is not None:
            QMessageBox.information(self, "DOCX", f"Document cree :\n{path}")

    def export_selected_pdf(self) -> None:
        contract_id = self._selected_contract_id()
        if contract_id is None:
            QMessageBox.information(self, "Export PDF", "Selectionnez un contrat.")
            return

        path = self._run_action(
            lambda: self.service.export_pdf(contract_id),
            "PDF exporte.",
        )
        self.refresh_table()
        if path is not None:
            QMessageBox.information(self, "PDF", f"PDF cree :\n{path}")

    def open_selected_document(self) -> None:
        contract_id = self._selected_contract_id()
        if contract_id is None:
            QMessageBox.information(self, "Document", "Selectionnez un contrat.")
            return

        self._run_action(
            lambda: self.service.open_document(contract_id),
            "Document ouvert.",
        )

    def open_selected_pdf(self) -> None:
        contract_id = self._selected_contract_id()
        if contract_id is None:
            QMessageBox.information(self, "PDF", "Selectionnez un contrat.")
            return

        self._run_action(
            lambda: self.service.open_pdf(contract_id),
            "PDF ouvert.",
        )

    def create_facture_from_selected_contract(self) -> None:
        contract = self._selected_contract()

        if contract is None:
            QMessageBox.information(self, "Creer une facture", "Selectionnez un contrat.")
            return

        # Le contrat n'est jamais modifie : la facture est un nouveau document
        # independant, pre-rempli puis toujours modifiable avant enregistrement
        # (meme principe que Devis/Contrat depuis Prestation).
        seed = self.facture_service.build_from_contract(contract)

        dialog = FactureDialog(
            self,
            initial_facture=seed,
            service=self.facture_service,
        )
        dialog.exec()

    def show_selected_history(self) -> None:
        contract_id = self._selected_contract_id()
        if contract_id is None:
            QMessageBox.information(self, "Historique", "Selectionnez un contrat.")
            return

        entries = self.service.history(contract_id)
        if not entries:
            QMessageBox.information(self, "Historique", "Aucun historique.")
            return

        message = "\n".join(
            f"{entry['created_at']} - {entry['action']} - {entry['details'] or ''}"
            for entry in entries
        )
        QMessageBox.information(self, "Historique", message)

    def refresh_table(self) -> None:
        status = str(self.status_filter.currentData())
        self._contracts = self.service.search_contracts(self.search.text(), status)
        self._fill_table(self._contracts)
        self._sync_buttons()

    def _fill_table(self, contracts: list[Contract]) -> None:
        self.table.setSortingEnabled(False)
        self.table.setRowCount(len(contracts))

        for row, contract in enumerate(contracts):
            values = (
                contract.id,
                contract.contract_number,
                contract.prestation_date or contract.event_date,
                contract.organisateur_structure,
                contract.spectacle_nom or contract.event_name,
                float(contract.cession_montant or contract.gross_salary or 0),
                contract.status_label,
                self._path_state(contract.docx_path),
                self._path_state(contract.pdf_path),
                contract.generated_at or "",
            )

            for column, value in enumerate(values):
                item = self._make_item(value)
                if column == 5:
                    item.setText(f"{float(value):.2f} EUR")
                    item.setData(Qt.ItemDataRole.EditRole, float(value))
                self.table.setItem(row, column, item)

        self.table.setSortingEnabled(True)
        self.table.resizeColumnsToContents()
        self.table.horizontalHeader().setStretchLastSection(True)

    def _make_item(self, value: Any) -> QTableWidgetItem:
        item = QTableWidgetItem("" if value is None else str(value))
        item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        return item

    def _selected_contract_id(self) -> int | None:
        row = self.table.currentRow()
        if row < 0:
            return None

        item = self.table.item(row, 0)
        if item is None:
            return None

        try:
            return int(item.text())
        except ValueError:
            return None

    def _selected_contract(self) -> Contract | None:
        contract_id = self._selected_contract_id()
        return self.service.get_contract(contract_id) if contract_id is not None else None

    def _sync_buttons(self) -> None:
        contract = self._selected_contract()
        has_selection = contract is not None
        has_docx = bool(contract and contract.docx_path and Path(contract.docx_path).exists())
        has_pdf = bool(contract and contract.pdf_path and Path(contract.pdf_path).exists())

        for button in (
            self.btn_edit,
            self.btn_duplicate,
            self.btn_delete,
            self.btn_generate,
            self.btn_export_pdf,
            self.btn_history,
            self.btn_create_facture,
        ):
            button.setEnabled(has_selection)

        self.btn_open.setEnabled(has_docx)
        self.btn_open_pdf.setEnabled(has_pdf)

    def _path_state(self, path: str) -> str:
        return "Oui" if path and Path(path).exists() else "Non"

    def _run_action(self, action: Callable[[], Any], success_message: str) -> Any:
        try:
            result = action()
        except Exception as exc:
            QMessageBox.warning(self, "Erreur", str(exc))
            return None

        if success_message:
            notify_success(self, success_message)
        return result
