from enum import Enum


class Color(str, Enum):
    ANTHROPIC_NEAR_BLACK = "#141413"
    TERRACOTTA_BRAND = "#c96442"
    CORAL_ACCENT = "#d97757"
    ERROR_CRIMSON = "#b53333"
    FOCUS_BLUE = "#3898ec"
    PARCHMENT = "#f5f4ed"
    IVORY = "#faf9f5"
    PURE_WHITE = "#ffffff"
    WARM_SAND = "#e8e6dc"
    DARK_SURFACE = "#30302e"
    DEEP_DARK = "#141413"
    CHARCOAL_WARM = "#4d4c48"
    OLIVE_GRAY = "#5e5d59"
    STONE_GRAY = "#87867f"
    DARK_WARM = "#3d3d3a"
    WARM_SILVER = "#b0aea5"
    BORDER_CREAM = "#f0eee6"
    BORDER_WARM = "#e8e6dc"
    BORDER_DARK = "#30302e"
    RING_WARM = "#d1cfc5"
    CARD_BORDER = RING_WARM


class Typography:
    FONT_FAMILY_SERIF = '"LXGW WenKai", "Noto Serif CJK SC", "SimSun", "Georgia", serif'
    FONT_FAMILY_SANS = '"Microsoft YaHei UI", "Segoe UI", "Arial", sans-serif'
    FONT_FAMILY_MONO = '"Cascadia Code", "Consolas", monospace'

    SIZE_HERO = 64
    SIZE_SECTION_HEADING = 52
    SIZE_SUB_HEADING_LARGE = 36
    SIZE_SUB_HEADING = 32
    SIZE_SUB_HEADING_SMALL = 25
    SIZE_FEATURE_TITLE = 20
    SIZE_BODY_LARGE = 20
    SIZE_BODY_SERIF = 17
    SIZE_BODY_NAV = 17
    SIZE_BODY_STANDARD = 16
    SIZE_BODY_SMALL = 15
    SIZE_CAPTION = 14
    SIZE_LABEL = 12
    SIZE_OVERLINE = 10
    SIZE_MICRO = 9
    SIZE_CODE = 15


class Spacing:
    BASE = 8
    SCALE_3 = 3
    SCALE_4 = 4
    SCALE_6 = 6
    SCALE_8 = 8
    SCALE_10 = 10
    SCALE_12 = 12
    SCALE_16 = 16
    SCALE_20 = 20
    SCALE_24 = 24
    SCALE_30 = 30
    SCALE_32 = 32
    PAGE_MARGIN = 16

    BUTTON_PADDING_X = 16
    BUTTON_PADDING_Y = 8
    CARD_PADDING = 12
    SECTION_SPACING = 80


class BorderRadius:
    SHARP = 4
    SUBTLE = 6
    ROUNDED = 8
    GENEROUS = 12
    VERY_ROUNDED = 16
    HIGHLY_ROUNDED = 24
    MAXIMUM = 32


class FontWeight:
    NORMAL = 400
    MEDIUM = 500


CHART_PALETTE = [
    Color.TERRACOTTA_BRAND.value,
    Color.CORAL_ACCENT.value,
    Color.OLIVE_GRAY.value,
    Color.WARM_SAND.value,
    Color.DARK_WARM.value,
    Color.CHARCOAL_WARM.value,
]

LINK_COLOR_DEFAULT = Color.DARK_WARM.value
LINK_COLOR_HOVER = Color.TERRACOTTA_BRAND.value


def get_base_stylesheet() -> str:
    return f"""
        /* === Base Widgets === */
        QWidget {{
            background-color: {Color.PARCHMENT.value};
            color: {Color.ANTHROPIC_NEAR_BLACK.value};
            font-family: {Typography.FONT_FAMILY_SANS};
            font-size: {Typography.SIZE_BODY_STANDARD}px;
        }}

        QMainWindow {{
            background-color: {Color.PARCHMENT.value};
        }}

        /* === Buttons === */
        QPushButton {{
            background-color: {Color.TERRACOTTA_BRAND.value};
            color: {Color.IVORY.value};
            border: none;
            border-radius: {BorderRadius.ROUNDED}px;
            padding: {Spacing.BUTTON_PADDING_Y}px {Spacing.BUTTON_PADDING_X}px;
            font-weight: 500;
            font-size: {Typography.SIZE_BODY_STANDARD}px;
        }}

        QPushButton:hover {{
            background-color: {Color.CORAL_ACCENT.value};
        }}

        QPushButton:pressed {{
            background-color: {Color.DARK_WARM.value};
        }}

        QPushButton:disabled {{
            background-color: {Color.WARM_SAND.value};
            color: {Color.STONE_GRAY.value};
        }}

        QPushButton#secondary-btn {{
            background-color: {Color.IVORY.value};
            border: 1px solid {Color.WARM_SAND.value};
            color: {Color.CHARCOAL_WARM.value};
            border-radius: {BorderRadius.SUBTLE}px;
            padding: 6px 16px;
        }}

        QPushButton#secondary-btn:hover {{
            background-color: {Color.WARM_SAND.value};
        }}

        /* === Labels === */
        QLabel {{
            background-color: transparent;
        }}

        QLabel#h1 {{
            font-family: {Typography.FONT_FAMILY_SERIF};
            font-size: {Typography.SIZE_SUB_HEADING}px;
            font-weight: 500;
            color: {Color.ANTHROPIC_NEAR_BLACK.value};
        }}

        QLabel#h2 {{
            font-family: {Typography.FONT_FAMILY_SERIF};
            font-size: {Typography.SIZE_SUB_HEADING_SMALL}px;
            font-weight: 500;
            color: {Color.ANTHROPIC_NEAR_BLACK.value};
        }}

        QLabel#subtitle {{
            font-size: {Typography.SIZE_BODY_LARGE}px;
            color: {Color.OLIVE_GRAY.value};
        }}

        QLabel#caption {{
            font-size: {Typography.SIZE_CAPTION}px;
            color: {Color.STONE_GRAY.value};
        }}

        QLabel#page-header-subtitle {{
            font-size: {Typography.SIZE_BODY_STANDARD}px;
            color: {Color.OLIVE_GRAY.value};
        }}

        QTextEdit#log-panel-text-edit {{
            font-family: {Typography.FONT_FAMILY_MONO};
            font-size: {Typography.SIZE_CAPTION}px;
            color: {Color.CHARCOAL_WARM.value};
            background-color: {Color.IVORY.value};
        }}

        /* === Inputs === */
        QLineEdit {{
            background-color: {Color.IVORY.value};
            border: 1px solid {Color.BORDER_CREAM.value};
            border-radius: {BorderRadius.GENEROUS}px;
            padding: 8px 12px;
            font-size: {Typography.SIZE_BODY_STANDARD}px;
            color: {Color.ANTHROPIC_NEAR_BLACK.value};
            selection-background-color: {Color.TERRACOTTA_BRAND.value};
            selection-color: {Color.IVORY.value};
        }}

        QLineEdit:focus {{
            border: 1px solid {Color.TERRACOTTA_BRAND.value};
        }}

        QLineEdit::placeholder {{
            color: {Color.STONE_GRAY.value};
        }}

        QTextEdit {{
            background-color: {Color.IVORY.value};
            border: 1px solid {Color.BORDER_CREAM.value};
            border-radius: {BorderRadius.ROUNDED}px;
            padding: 8px 12px;
            font-size: {Typography.SIZE_BODY_STANDARD}px;
            color: {Color.ANTHROPIC_NEAR_BLACK.value};
        }}

        QTextEdit:focus {{
            border: 1px solid {Color.TERRACOTTA_BRAND.value};
        }}

        /* === Combo Boxes === */
        QComboBox {{
            background-color: {Color.IVORY.value};
            border: 1px solid {Color.BORDER_CREAM.value};
            border-radius: {BorderRadius.ROUNDED}px;
            padding: 6px 12px;
            font-size: {Typography.SIZE_BODY_STANDARD}px;
            color: {Color.ANTHROPIC_NEAR_BLACK.value};
            min-width: 120px;
        }}

        QComboBox:hover {{
            border: 1px solid {Color.RING_WARM.value};
        }}

        QComboBox:focus {{
            border: 1px solid {Color.TERRACOTTA_BRAND.value};
        }}

        QComboBox::drop-down {{
            border: none;
            width: 24px;
        }}

        QComboBox QAbstractItemView {{
            background-color: {Color.IVORY.value};
            border: 1px solid {Color.BORDER_WARM.value};
            border-radius: {BorderRadius.ROUNDED}px;
            selection-background-color: {Color.WARM_SAND.value};
            selection-color: {Color.ANTHROPIC_NEAR_BLACK.value};
            outline: none;
        }}

        /* === Tables === */
        QTableView, QTreeView {{
            background-color: {Color.IVORY.value};
            alternate-background-color: {Color.PARCHMENT.value};
            border: 1px solid {Color.BORDER_CREAM.value};
            border-radius: {BorderRadius.ROUNDED}px;
            gridline-color: {Color.BORDER_CREAM.value};
            selection-background-color: {Color.WARM_SAND.value};
            selection-color: {Color.ANTHROPIC_NEAR_BLACK.value};
            outline: none;
        }}

        QHeaderView::section {{
            background-color: {Color.PARCHMENT.value};
            color: {Color.CHARCOAL_WARM.value};
            border: none;
            border-bottom: 1px solid {Color.BORDER_WARM.value};
            border-right: 1px solid {Color.BORDER_CREAM.value};
            padding: 8px 12px;
            font-weight: 500;
            font-size: {Typography.SIZE_CAPTION}px;
        }}

        /* === List Widgets === */
        QListWidget {{
            background-color: {Color.IVORY.value};
            border: 1px solid {Color.BORDER_CREAM.value};
            border-radius: {BorderRadius.ROUNDED}px;
            outline: none;
        }}

        QListWidget::item {{
            padding: 8px 16px;
            border-bottom: 1px solid {Color.BORDER_CREAM.value};
            color: {Color.ANTHROPIC_NEAR_BLACK.value};
        }}

        QListWidget::item:hover {{
            background-color: {Color.PARCHMENT.value};
        }}

        QListWidget::item:selected {{
            background-color: {Color.WARM_SAND.value};
            color: {Color.ANTHROPIC_NEAR_BLACK.value};
        }}

        /* === List Views === */
        QListView {{
            background-color: {Color.IVORY.value};
            border: 1px solid {Color.BORDER_CREAM.value};
            border-radius: {BorderRadius.ROUNDED}px;
            outline: none;
        }}

        QListView::item {{
            border-bottom: 1px solid {Color.BORDER_CREAM.value};
        }}

        QListView::item:hover {{
            background-color: {Color.PARCHMENT.value};
        }}

        QListView::item:selected {{
            background-color: {Color.WARM_SAND.value};
        }}

        /* === Scroll Bars === */
        QScrollBar:vertical {{
            background-color: transparent;
            width: 8px;
            margin: 4px 0px;
        }}

        QScrollBar::handle:vertical {{
            background-color: {Color.RING_WARM.value};
            border-radius: 4px;
            min-height: 30px;
        }}

        QScrollBar::handle:vertical:hover {{
            background-color: {Color.STONE_GRAY.value};
        }}

        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0px;
        }}

        QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
            background: none;
        }}

        QScrollBar:horizontal {{
            background-color: transparent;
            height: 8px;
            margin: 0px 4px;
        }}

        QScrollBar::handle:horizontal {{
            background-color: {Color.RING_WARM.value};
            border-radius: 4px;
            min-width: 30px;
        }}

        QScrollBar::handle:horizontal:hover {{
            background-color: {Color.STONE_GRAY.value};
        }}

        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
            width: 0px;
        }}

        QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{
            background: none;
        }}

        /* === Progress Bar === */
        QProgressBar {{
            background-color: {Color.WARM_SAND.value};
            border: none;
            border-radius: {BorderRadius.SUBTLE}px;
            text-align: center;
            color: {Color.CHARCOAL_WARM.value};
            font-size: {Typography.SIZE_CAPTION}px;
            min-height: 20px;
        }}

        QProgressBar::chunk {{
            background-color: {Color.TERRACOTTA_BRAND.value};
            border-radius: {BorderRadius.SUBTLE}px;
        }}

        /* === Group Boxes === */
        QGroupBox {{
            background-color: {Color.PURE_WHITE.value};
            border: 1px solid {Color.RING_WARM.value};
            border-radius: {BorderRadius.ROUNDED}px;
            margin-top: 16px;
            padding-top: 24px;
            font-weight: 500;
        }}

        QGroupBox::title {{
            subcontrol-origin: margin;
            left: 16px;
            padding: 0 8px;
            color: {Color.CHARCOAL_WARM.value};
        }}

        /* === Check Boxes & Radio Buttons === */
        QCheckBox, QRadioButton {{
            spacing: 10px;
            color: {Color.ANTHROPIC_NEAR_BLACK.value};
            font-size: {Typography.SIZE_BODY_STANDARD}px;
            padding: 6px 4px;
        }}

        QCheckBox::indicator, QRadioButton::indicator {{
            width: 20px;
            height: 20px;
            border: 2px solid {Color.RING_WARM.value};
            border-radius: 4px;
            background-color: {Color.IVORY.value};
        }}

        QCheckBox::indicator:hover, QRadioButton::indicator:hover {{
            border-color: {Color.TERRACOTTA_BRAND.value};
        }}

        QCheckBox::indicator:checked, QRadioButton::indicator:checked {{
            background-color: {Color.TERRACOTTA_BRAND.value};
            border-color: {Color.TERRACOTTA_BRAND.value};
        }}

        QRadioButton::indicator {{
            border-radius: 10px;
        }}

        /* === Spin Boxes === */
        QSpinBox, QDoubleSpinBox {{
            background-color: {Color.IVORY.value};
            border: 1px solid {Color.BORDER_CREAM.value};
            border-radius: {BorderRadius.ROUNDED}px;
            padding: 4px 8px;
            color: {Color.ANTHROPIC_NEAR_BLACK.value};
        }}

QSpinBox:focus, QDoubleSpinBox:focus {{
    border: 1px solid {Color.TERRACOTTA_BRAND.value};
}}

QSpinBox::up-button, QDoubleSpinBox::up-button {{
    subcontrol-origin: border;
    subcontrol-position: top right;
    width: 20px;
    border-left: 1px solid {Color.BORDER_CREAM.value};
    border-radius: {BorderRadius.SUBTLE}px;
}}

QSpinBox::down-button, QDoubleSpinBox::down-button {{
    subcontrol-origin: border;
    subcontrol-position: bottom right;
    width: 20px;
    border-left: 1px solid {Color.BORDER_CREAM.value};
    border-top: 1px solid {Color.BORDER_CREAM.value};
    border-radius: {BorderRadius.SUBTLE}px;
}}

QSpinBox::up-arrow, QDoubleSpinBox::up-arrow {{
    width: 8px;
    height: 8px;
    border-left: 2px solid {Color.CHARCOAL_WARM.value};
    border-top: 2px solid {Color.CHARCOAL_WARM.value};
    margin-right: 4px;
}}

QSpinBox::down-arrow, QDoubleSpinBox::down-arrow {{
    width: 8px;
    height: 8px;
    border-left: 2px solid {Color.CHARCOAL_WARM.value};
    border-bottom: 2px solid {Color.CHARCOAL_WARM.value};
    margin-right: 4px;
}}

QDateEdit {{
            background-color: {Color.IVORY.value};
            border: 1px solid {Color.BORDER_CREAM.value};
            border-radius: {BorderRadius.ROUNDED}px;
            padding: 4px 8px;
            color: {Color.ANTHROPIC_NEAR_BLACK.value};
        }}

        QDateEdit:focus {{
            border: 1px solid {Color.TERRACOTTA_BRAND.value};
        }}

        /* === Tool Tips === */
        QToolTip {{
            background-color: {Color.DARK_SURFACE.value};
            color: {Color.IVORY.value};
            border: 1px solid {Color.BORDER_DARK.value};
            border-radius: {BorderRadius.SUBTLE}px;
            padding: 6px 10px;
            font-size: {Typography.SIZE_CAPTION}px;
        }}

        /* === Tab Widget === */
        QTabWidget::pane {{
            border: 1px solid {Color.BORDER_CREAM.value};
            border-radius: {BorderRadius.ROUNDED}px;
            background-color: {Color.IVORY.value};
        }}

        QTabBar::tab {{
            background-color: {Color.PARCHMENT.value};
            border: 1px solid {Color.BORDER_CREAM.value};
            border-bottom: none;
            border-top-left-radius: {BorderRadius.ROUNDED}px;
            border-top-right-radius: {BorderRadius.ROUNDED}px;
            padding: 8px 16px;
            color: {Color.OLIVE_GRAY.value};
        }}

        QTabBar::tab:selected {{
            background-color: {Color.IVORY.value};
            color: {Color.ANTHROPIC_NEAR_BLACK.value};
            font-weight: 500;
        }}

        QTabBar::tab:hover:!selected {{
            background-color: {Color.WARM_SAND.value};
        }}

        /* === Component Object Names === */
        QLabel#page-header-title {{
            font-family: {Typography.FONT_FAMILY_SERIF};
            font-size: {Typography.SIZE_SUB_HEADING}px;
            font-weight: 500;
            color: {Color.ANTHROPIC_NEAR_BLACK.value};
        }}

        QLabel#summary-card-title {{
            font-size: {Typography.SIZE_BODY_STANDARD}px;
            color: {Color.CHARCOAL_WARM.value};
        }}

        QLabel#summary-card-value {{
            font-size: {Typography.SIZE_SUB_HEADING_LARGE}px;
            font-weight: 500;
            color: {Color.ANTHROPIC_NEAR_BLACK.value};
        }}

        QLabel#empty-state-title {{
            font-size: {Typography.SIZE_FEATURE_TITLE}px;
            font-weight: 500;
            color: {Color.OLIVE_GRAY.value};
        }}

        QLabel#empty-state-subtitle {{
            font-size: {Typography.SIZE_BODY_STANDARD}px;
            color: {Color.STONE_GRAY.value};
        }}

        QLabel#status-badge {{
            padding: {Spacing.SCALE_8}px;
            border-radius: {BorderRadius.ROUNDED}px;
            background-color: {Color.IVORY.value};
            border: 1px solid {Color.WARM_SAND.value};
        }}

QWidget#surface-card {{
    background-color: {Color.PURE_WHITE.value};
    border: 1px solid {Color.RING_WARM.value};
    border-radius: {BorderRadius.ROUNDED}px;
}}

/* === Calendar Widget === */
QCalendarWidget QWidget {{
    background-color: {Color.IVORY.value};
}}

QCalendarWidget QToolButton {{
    background-color: {Color.PARCHMENT.value};
    color: {Color.ANTHROPIC_NEAR_BLACK.value};
    border-radius: {BorderRadius.ROUNDED}px;
    padding: 4px 8px;
}}

QCalendarWidget QToolButton:hover {{
    background-color: {Color.WARM_SAND.value};
}}

QCalendarWidget QAbstractItemView {{
    background-color: {Color.IVORY.value};
    selection-background-color: {Color.TERRACOTTA_BRAND.value};
    selection-color: {Color.IVORY.value};
    border-radius: {BorderRadius.ROUNDED}px;
}}

QCalendarWidget QSpinBox {{
    background-color: {Color.IVORY.value};
    border: 1px solid {Color.BORDER_CREAM.value};
    border-radius: {BorderRadius.GENEROUS}px;
}}

QCalendarWidget QMenu {{
    background-color: {Color.IVORY.value};
    border: 1px solid {Color.BORDER_CREAM.value};
    border-radius: {BorderRadius.ROUNDED}px;
}}
"""
