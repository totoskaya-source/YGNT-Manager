import sys

from PySide6.QtWidgets import QApplication

from app.database.backup import backup_database
from app.database.migrations import MigrationManager
from app.ui.main_window import MainWindow
from app.ui.theme import apply_theme


def main():
    backup_database()
    MigrationManager().migrate()

    app = QApplication(sys.argv)
    apply_theme(app)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
