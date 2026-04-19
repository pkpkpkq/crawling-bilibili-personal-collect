from app.theme import Color, Typography, Spacing, BorderRadius, get_base_stylesheet


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
