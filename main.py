import sys

from PySide6.QtWidgets import QApplication

from app.database.migrations import MigrationManager
from app.ui.main_window import MainWindow


def main():
    MigrationManager().migrate()

    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
