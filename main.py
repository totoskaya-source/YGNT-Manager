import sys

from PySide6.QtCore import QLibraryInfo, QLocale, QTranslator
from PySide6.QtWidgets import QApplication

from app.database.backup import backup_database
from app.database.migrations import MigrationManager
from app.ui.main_window import MainWindow
from app.ui.theme import apply_theme


def install_french_translations(app: QApplication) -> None:
    """Traduit les elements standard de Qt (menus contextuels Couper/Copier/
    Coller/Supprimer/Annuler/Retablir/Tout selectionner, boutons standard des
    QMessageBox/QDialogButtonBox, etc.) sans devoir les recoder a la main."""
    translations_path = QLibraryInfo.path(QLibraryInfo.LibraryPath.TranslationsPath)
    translator = QTranslator(app)
    if translator.load(QLocale("fr_FR"), "qtbase", "_", translations_path):
        app.installTranslator(translator)


def main():
    backup_database()
    MigrationManager().migrate()

    app = QApplication(sys.argv)
    install_french_translations(app)
    apply_theme(app)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
