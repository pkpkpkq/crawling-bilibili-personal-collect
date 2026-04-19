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


class Typography:
    FONT_FAMILY_SERIF = '"Georgia", serif'
    FONT_FAMILY_SANS = '"Arial", sans-serif'
    FONT_FAMILY_MONO = '"Courier New", monospace'

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

    BUTTON_PADDING_X = 16
    BUTTON_PADDING_Y = 8
    CARD_PADDING = 24
    SECTION_SPACING = 80


class BorderRadius:
    SHARP = 4
    ROUNDED = 8


def get_base_stylesheet() -> str:
    return f"""
        QWidget {{
            background-color: {Color.PARCHMENT.value};
            color: {Color.ANTHROPIC_NEAR_BLACK.value};
            font-family: {Typography.FONT_FAMILY_SANS};
            font-size: {Typography.SIZE_BODY_STANDARD}px;
        }}
        
        QMainWindow {{
            background-color: {Color.PARCHMENT.value};
        }}

        QPushButton {{
            background-color: {Color.TERRACOTTA_BRAND.value};
            color: {Color.PURE_WHITE.value};
            border: none;
            border-radius: {BorderRadius.SHARP}px;
            padding: {Spacing.BUTTON_PADDING_Y}px {Spacing.BUTTON_PADDING_X}px;
            font-weight: 500;
        }}

        QPushButton:hover {{
            background-color: {Color.CORAL_ACCENT.value};
        }}
        
        QLabel {{
            background-color: transparent;
        }}
        
        QLabel#h1 {{
            font-family: {Typography.FONT_FAMILY_SERIF};
            font-size: {Typography.SIZE_SUB_HEADING}px;
            font-weight: 500;
        }}
    """
