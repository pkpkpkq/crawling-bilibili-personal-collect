from app.theme import (
    Color,
    Typography,
    Spacing,
    BorderRadius,
    FontWeight,
    CHART_PALETTE,
    LINK_COLOR_DEFAULT,
    LINK_COLOR_HOVER,
    get_base_stylesheet,
)


def test_theme_tokens_exist():
    assert Color.ANTHROPIC_NEAR_BLACK.value == "#141413"
    assert Color.TERRACOTTA_BRAND.value == "#c96442"
    assert Typography.SIZE_HERO == 64
    assert Spacing.BASE == 8
    assert BorderRadius.SHARP == 4


def test_stylesheet_generation():
    stylesheet = get_base_stylesheet()
    assert Color.PARCHMENT.value in stylesheet
    assert Color.TERRACOTTA_BRAND.value in stylesheet
    assert str(Spacing.BUTTON_PADDING_X) in stylesheet


def test_font_weight_tokens_exist():
    assert FontWeight.NORMAL == 400
    assert FontWeight.MEDIUM == 500


def test_chart_palette_exists_and_warm():
    assert len(CHART_PALETTE) >= 6
    all_color_values = [v.value for v in Color]
    for c in CHART_PALETTE:
        assert c in all_color_values


def test_link_color_tokens_exist():
    assert LINK_COLOR_DEFAULT == Color.DARK_WARM.value
    assert LINK_COLOR_HOVER == Color.TERRACOTTA_BRAND.value


def test_component_object_name_styles_in_stylesheet():
    stylesheet = get_base_stylesheet()
    assert "QLabel#page-header-title" in stylesheet
    assert "QLabel#summary-card-value" in stylesheet
    assert "QLabel#empty-state-title" in stylesheet
    assert "QWidget#surface-card" in stylesheet
    assert "QLabel#status-badge" in stylesheet
    assert "QPushButton#secondary-btn" in stylesheet
