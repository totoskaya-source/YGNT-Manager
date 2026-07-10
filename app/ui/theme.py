"""Theme centralise de YGNT Manager.

Toute couleur, police, taille ou marge utilisee dans l'interface doit venir
de ce module. Aucune fenetre ne doit coder un style Qt (QSS) en dur : elle
appelle `apply_theme()` une fois au demarrage puis utilise les helpers
`style_page_title`, `style_section_label` et `mark_destructive` pour
signaler son intention (titre de page, en-tete de section, action
destructive) au theme, qui se charge du rendu.
"""

from __future__ import annotations

from PySide6.QtWidgets import QApplication, QLabel, QPushButton, QTableWidget, QWidget

# ===== Palette =====

BACKGROUND = "#F2F3F5"        # fond principal : gris tres clair
SURFACE = "#FFFFFF"           # cartes / champs / tableaux : blanc
BORDER = "#E1E3E8"
ROW_ALT = "#F7F7F9"

TEXT_PRIMARY = "#2B2B31"      # texte : gris fonce
TEXT_SECONDARY = "#6B7280"    # gris secondaire
TEXT_MUTED = "#9AA0AA"

PRIMARY = "#7A1428"           # bordeaux YGNT
PRIMARY_HOVER = "#8C1B32"
PRIMARY_PRESSED = "#5E0F20"

SECONDARY = "#6B7280"         # gris

DANGER = "#DC2626"            # rouge vif : reserve aux actions destructives
DANGER_HOVER = "#B91C1C"
DANGER_DISABLED = "#F3C9C9"

SIDEBAR_BG = "#3A121F"
SIDEBAR_HOVER = "#4C1B29"
SIDEBAR_TEXT = "#F1E4E7"
SIDEBAR_TEXT_MUTED = "#CBA6AF"

# ===== Typographie =====

FONT_FAMILY = "Segoe UI"
FONT_SIZE_BASE = 10
FONT_SIZE_TITLE = 20
FONT_SIZE_SECTION = 11

# ===== Espacements =====

SPACING_SM = 6
SPACING_MD = 12
SPACING_LG = 18
RADIUS = 6
RADIUS_CARD = 8

SIDEBAR_WIDTH = 230
TABLE_ROW_HEIGHT = 34

# ===== Noms d'objets (cibles des selecteurs QSS) =====

PAGE_TITLE = "pageTitle"
DIALOG_TITLE = "dialogTitle"
SECTION_LABEL = "sectionLabel"
SIDEBAR_LIST = "sidebar"
DESTRUCTIVE_PROPERTY = "destructive"


def _stylesheet() -> str:
    return f"""
    QWidget {{
        background-color: {BACKGROUND};
        color: {TEXT_PRIMARY};
        font-family: "{FONT_FAMILY}";
        font-size: {FONT_SIZE_BASE}pt;
    }}

    QMainWindow, QDialog {{
        background-color: {BACKGROUND};
    }}

    /* QLabel ne doit jamais peindre son propre fond : il doit toujours
       laisser apparaitre la couleur de son conteneur (carte blanche,
       onglet, fond de page...). Sans cela, chaque etiquette de formulaire
       affiche un rectangle gris disgracieux sur les cartes blanches. */
    QLabel {{
        background-color: transparent;
    }}

    QToolTip {{
        background-color: {TEXT_PRIMARY};
        color: {SURFACE};
        border: none;
        padding: 4px 8px;
        border-radius: 4px;
    }}

    /* ===== Titres ===== */

    QLabel#{PAGE_TITLE} {{
        font-size: {FONT_SIZE_TITLE}pt;
        font-weight: 600;
        color: {TEXT_PRIMARY};
        padding-bottom: 4px;
    }}

    QLabel#{DIALOG_TITLE} {{
        font-size: {FONT_SIZE_SECTION + 4}pt;
        font-weight: 600;
        color: {TEXT_PRIMARY};
        padding-bottom: 2px;
    }}

    QLabel#{SECTION_LABEL} {{
        font-size: {FONT_SIZE_SECTION}pt;
        font-weight: 600;
        color: {PRIMARY};
        margin-top: 10px;
        padding-bottom: 3px;
        border-bottom: 1px solid {BORDER};
    }}

    /* ===== Sidebar ===== */

    QListWidget#{SIDEBAR_LIST} {{
        background-color: {SIDEBAR_BG};
        border: none;
        outline: none;
        padding: 14px 0px;
        font-size: {FONT_SIZE_BASE + 1}pt;
    }}

    QListWidget#{SIDEBAR_LIST}::item {{
        color: {SIDEBAR_TEXT};
        padding: 11px 16px;
        margin: 2px 10px;
        border-radius: {RADIUS}px;
        border: none;
    }}

    QListWidget#{SIDEBAR_LIST}::item:hover {{
        background-color: {SIDEBAR_HOVER};
    }}

    QListWidget#{SIDEBAR_LIST}::item:selected {{
        background-color: {PRIMARY};
        color: #FFFFFF;
        font-weight: 600;
    }}

    /* ===== Boutons ===== */

    QPushButton {{
        background-color: {SURFACE};
        color: {TEXT_PRIMARY};
        border: 1px solid {BORDER};
        border-radius: {RADIUS}px;
        padding: 7px 16px;
        min-height: 20px;
    }}

    QPushButton:hover {{
        background-color: #F1EDEE;
        border-color: {PRIMARY};
    }}

    QPushButton:pressed {{
        background-color: #E7E1E3;
    }}

    QPushButton:focus {{
        border: 1px solid {PRIMARY};
        outline: none;
    }}

    QPushButton:disabled {{
        color: {TEXT_MUTED};
        background-color: #F5F5F6;
        border-color: #ECEDEF;
    }}

    QPushButton:default {{
        background-color: {PRIMARY};
        color: #FFFFFF;
        border: 1px solid {PRIMARY};
    }}

    QPushButton:default:hover {{
        background-color: {PRIMARY_HOVER};
    }}

    QPushButton:default:pressed {{
        background-color: {PRIMARY_PRESSED};
    }}

    QPushButton[{DESTRUCTIVE_PROPERTY}="true"] {{
        background-color: {DANGER};
        color: #FFFFFF;
        border: 1px solid {DANGER};
    }}

    QPushButton[{DESTRUCTIVE_PROPERTY}="true"]:hover {{
        background-color: {DANGER_HOVER};
    }}

    QPushButton[{DESTRUCTIVE_PROPERTY}="true"]:pressed {{
        background-color: #9B1414;
    }}

    QPushButton[{DESTRUCTIVE_PROPERTY}="true"]:disabled {{
        background-color: {DANGER_DISABLED};
        border-color: {DANGER_DISABLED};
        color: #FFFFFF;
    }}

    /* ===== Champs de saisie ===== */

    QLineEdit, QTextEdit, QPlainTextEdit, QComboBox, QDateEdit, QDoubleSpinBox, QSpinBox {{
        background-color: {SURFACE};
        border: 1px solid {BORDER};
        border-radius: {RADIUS}px;
        padding: 5px 8px;
        selection-background-color: {PRIMARY};
        selection-color: #FFFFFF;
    }}

    QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus, QComboBox:focus,
    QDateEdit:focus, QDoubleSpinBox:focus, QSpinBox:focus {{
        border: 1px solid {PRIMARY};
    }}

    QLineEdit:disabled, QTextEdit:disabled, QComboBox:disabled {{
        background-color: #F5F5F6;
        color: {TEXT_MUTED};
    }}

    QComboBox::drop-down {{
        border: none;
        width: 22px;
    }}

    QComboBox QAbstractItemView {{
        background-color: {SURFACE};
        border: 1px solid {BORDER};
        selection-background-color: {PRIMARY};
        selection-color: #FFFFFF;
        outline: none;
    }}

    /* ===== Tableaux ===== */

    QTableWidget, QTableView {{
        background-color: {SURFACE};
        alternate-background-color: {ROW_ALT};
        gridline-color: {BORDER};
        border: 1px solid {BORDER};
        border-radius: {RADIUS}px;
        selection-background-color: {PRIMARY};
        selection-color: #FFFFFF;
    }}

    QTableWidget::item, QTableView::item {{
        padding: 4px 8px;
        border: none;
    }}

    QHeaderView::section {{
        background-color: #EBEDF1;
        color: {TEXT_PRIMARY};
        padding: 8px;
        border: none;
        border-bottom: 1px solid {BORDER};
        font-weight: 600;
    }}

    QHeaderView::section:horizontal {{
        border-right: 1px solid {BORDER};
    }}

    QTableCornerButton::section {{
        background-color: #EBEDF1;
        border: none;
    }}

    /* ===== Onglets ===== */

    QTabWidget::pane {{
        border: 1px solid {BORDER};
        border-radius: {RADIUS}px;
        background: {SURFACE};
        top: -1px;
    }}

    QTabBar::tab {{
        background: transparent;
        color: {TEXT_SECONDARY};
        padding: 9px 20px;
        margin-right: 2px;
        border-top-left-radius: {RADIUS}px;
        border-top-right-radius: {RADIUS}px;
    }}

    QTabBar::tab:selected {{
        background: {SURFACE};
        color: {PRIMARY};
        font-weight: 600;
        border: 1px solid {BORDER};
        border-bottom-color: {SURFACE};
    }}

    QTabBar::tab:hover:!selected {{
        color: {PRIMARY};
    }}

    /* ===== Groupes ===== */

    QGroupBox {{
        background-color: {SURFACE};
        border: 1px solid {BORDER};
        border-radius: {RADIUS_CARD}px;
        margin-top: 16px;
        padding: 16px 14px 12px 14px;
        font-weight: 600;
    }}

    QGroupBox::title {{
        subcontrol-origin: margin;
        left: 12px;
        padding: 0 6px;
        color: {PRIMARY};
    }}

    /* ===== Barre de statut ===== */

    QStatusBar {{
        background-color: {SURFACE};
        border-top: 1px solid {BORDER};
        color: {TEXT_SECONDARY};
    }}

    /* ===== Divers ===== */

    QScrollArea {{
        border: none;
        background: transparent;
    }}

    QScrollBar:vertical {{
        width: 10px;
        background: transparent;
        margin: 0px;
    }}

    QScrollBar::handle:vertical {{
        background: #C7C9CF;
        border-radius: 5px;
        min-height: 24px;
    }}

    QScrollBar::handle:vertical:hover {{
        background: {SECONDARY};
    }}

    QScrollBar:horizontal {{
        height: 10px;
        background: transparent;
    }}

    QScrollBar::handle:horizontal {{
        background: #C7C9CF;
        border-radius: 5px;
        min-width: 24px;
    }}

    QCheckBox::indicator {{
        width: 16px;
        height: 16px;
        border: 1px solid {BORDER};
        border-radius: 3px;
        background: {SURFACE};
    }}

    QCheckBox::indicator:checked {{
        background: {PRIMARY};
        border-color: {PRIMARY};
    }}
    """


def apply_theme(app: QApplication) -> None:
    """Applique le theme a toute l'application. A appeler une seule fois,
    juste apres la creation du QApplication."""
    app.setStyle("Fusion")
    app.setStyleSheet(_stylesheet())


def style_page_title(label: QLabel) -> None:
    """Marque un QLabel comme titre de page (grande police, gras)."""
    label.setObjectName(PAGE_TITLE)


def style_dialog_title(label: QLabel) -> None:
    """Marque un QLabel comme titre d'une petite boite de dialogue (ex. A propos),
    plus discret qu'un titre de page pleine largeur."""
    label.setObjectName(DIALOG_TITLE)


def style_section_label(label: QLabel) -> None:
    """Marque un QLabel comme en-tete de sous-section a l'interieur d'une page."""
    label.setObjectName(SECTION_LABEL)


def mark_destructive(button: QPushButton) -> None:
    """Signale qu'un bouton declenche une action destructive (ex. Supprimer) :
    il doit rester visuellement distinct des autres actions."""
    button.setProperty(DESTRUCTIVE_PROPERTY, True)
    button.style().unpolish(button)
    button.style().polish(button)


def style_sidebar(list_widget: QWidget) -> None:
    """Marque le QListWidget de navigation principale comme sidebar."""
    list_widget.setObjectName(SIDEBAR_LIST)


def style_table(table: QTableWidget) -> None:
    """Ajustements communs a tous les tableaux : lignes plus hautes, pas de
    colonne de numeros de ligne, colonnes redimensionnables par l'utilisateur."""
    table.verticalHeader().setVisible(False)
    table.verticalHeader().setDefaultSectionSize(TABLE_ROW_HEIGHT)
