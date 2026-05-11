"""BaseCardDelegate — shared painting helpers for card-list rows."""

from PySide6.QtCore import QModelIndex, QPersistentModelIndex, QRect, QSize, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import QStyleOptionViewItem, QStyledItemDelegate

from app.theme import BorderRadius, Color, Spacing, Typography


class BaseCardDelegate(QStyledItemDelegate):
    """Base delegate skeleton for warm card rows.

    Subclasses override the text hooks to read application-specific model roles;
    this class only handles generic warm-surface painting, sizing, link hit
    tracking, and expanded-row state.

    Template-method hooks (override in subclasses):
        _title_color(option)       – title pen colour (default ANTHROPIC_NEAR_BLACK)
        _configure_title_font(...)  – mutate title font (e.g. setStrikeOut)
        _text_rect(...)            – override text area (e.g. to leave room for a cover)
        _paint_extras(...)         – paint badges / covers / extra links; returns new y
        _expanded_y_start(...)     – adjust where expanded content begins
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._link_rect: dict[object, QRect] = {}
        self._hovered_link_key: object | None = None
        self._expanded_rows: set[object] = set()
        # Layout state set during paint() for use by _paint_extras()
        self._title_y: int = 0
        self._title_height: int = 0
        self._body_font: QFont | None = None
        self._body_line_height: int = 0

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex) -> None:
        painter.save()
        self._paint_index = index
        self._paint_option = option
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        card_rect = option.rect.adjusted(
            Spacing.SCALE_8,
            Spacing.SCALE_6,
            -Spacing.SCALE_8,
            -Spacing.SCALE_6,
        )
        
        shadow_rect = card_rect.translated(0, 2)
        painter.setBrush(QColor(Color.BORDER_WARM.value))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(shadow_rect, BorderRadius.GENEROUS, BorderRadius.GENEROUS)

        painter.setBrush(QColor(Color.PURE_WHITE.value))
        painter.setPen(QPen(QColor(Color.CARD_BORDER.value), 1))
        painter.drawRoundedRect(card_rect, BorderRadius.GENEROUS, BorderRadius.GENEROUS)

        content_rect = card_rect.adjusted(
            Spacing.CARD_PADDING,
            Spacing.SCALE_8,
            -Spacing.CARD_PADDING,
            -Spacing.SCALE_8,
        )
        text_rect = self._text_rect(card_rect, content_rect, index)
        y = text_rect.top()

        title_font = QFont(option.font)
        title_font.setPixelSize(Typography.SIZE_FEATURE_TITLE)
        title_font.setWeight(QFont.Weight.Medium)
        self._configure_title_font(title_font, option, index)
        painter.setFont(title_font)
        painter.setPen(QColor(self._title_color(option)))
        title_height = painter.fontMetrics().height()
        self._title_y = y
        self._title_height = title_height
        painter.drawText(
            QRect(text_rect.left(), y, text_rect.width(), title_height),
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
            self._title_text(index),
        )
        y += title_height + Spacing.SCALE_8

        body_font = QFont(option.font)
        body_font.setPixelSize(Typography.SIZE_BODY_STANDARD)
        painter.setFont(body_font)
        painter.setPen(QColor(Color.OLIVE_GRAY.value))
        self._body_font = body_font
        metadata = self._subtitle_text(index)
        if metadata:
            line_height = painter.fontMetrics().height()
            self._body_line_height = line_height
            for line in metadata.splitlines():
                painter.drawText(
                    QRect(text_rect.left(), y, text_rect.width(), line_height),
                    Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                    line,
                )
                y += line_height + Spacing.SCALE_4

        link_text = self._link_text(index)
        key = self._index_key(index)
        if link_text:
            link_font = QFont(body_font)
            link_font.setWeight(QFont.Weight.Medium)
            link_font.setUnderline(False)
            painter.setFont(link_font)
            is_hovered = self._hovered_link_key == key
            painter.setPen(QColor(Color.TERRACOTTA_BRAND.value if is_hovered else Color.DARK_WARM.value))
            metrics = painter.fontMetrics()
            link_width = metrics.horizontalAdvance(link_text)
            link_height = metrics.height()
            link_rect = QRect(text_rect.left(), y, link_width, link_height)
            self._link_rect[key] = link_rect
            painter.drawText(
                link_rect,
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                link_text,
            )
            # Terracotta underline — fully opaque on hover, semi-transparent otherwise
            underline_y = link_rect.bottom() + 2
            underline_alpha = 255 if is_hovered else 100
            terracotta = QColor(Color.TERRACOTTA_BRAND.value)
            terracotta.setAlpha(underline_alpha)
            underline_pen = QPen(terracotta, 1)
            painter.setPen(underline_pen)
            painter.drawLine(link_rect.left(), underline_y, link_rect.right(), underline_y)
            y += link_height + Spacing.SCALE_8
        else:
            self._link_rect.pop(key, None)

        y = self._paint_extras(painter, option, index, content_rect, text_rect, y)

        expanded = self._expanded_content(index) if self._is_expanded(index) else ""
        if expanded:
            painter.setFont(body_font)
            painter.setPen(QColor(Color.CHARCOAL_WARM.value))
            line_height = painter.fontMetrics().height()
            y = self._expanded_y_start(y, content_rect, index)
            y += Spacing.SCALE_4
            for line in expanded.splitlines():
                painter.drawText(
                    QRect(content_rect.left(), y, content_rect.width(), line_height),
                    Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                    line,
                )
                y += line_height + Spacing.SCALE_4

        painter.restore()

    def sizeHint(self, option: QStyleOptionViewItem, index: QModelIndex) -> QSize:  # noqa: N802
        body_lines = max(1, len(self._subtitle_text(index).splitlines()) if self._subtitle_text(index) else 0)
        link_lines = 1 if self._link_text(index) else 0
        expanded_lines = 0
        if self._is_expanded(index):
            expanded = self._expanded_content(index)
            expanded_lines = len(expanded.splitlines()) if expanded else 1

        # Use real font metrics for accurate line-height calculation
        title_font = QFont(option.font)
        title_font.setPixelSize(Typography.SIZE_FEATURE_TITLE)
        from PySide6.QtGui import QFontMetrics
        title_line_h = QFontMetrics(title_font).height()

        body_font = QFont(option.font)
        body_font.setPixelSize(Typography.SIZE_BODY_STANDARD)
        body_line_h = QFontMetrics(body_font).height()

        height = (
            Spacing.SCALE_6 * 2       # outer card margin (top+bottom)
            + Spacing.SCALE_8 * 2     # inner content padding (top+bottom)
            + title_line_h            # title
            + Spacing.SCALE_8         # gap after title
            + body_lines * (body_line_h + Spacing.SCALE_4)  # subtitle lines
            + link_lines * (body_line_h + Spacing.SCALE_8)  # link line
            + expanded_lines * (body_line_h + Spacing.SCALE_4)  # expanded lines
            + Spacing.SCALE_8         # bottom padding
        )
        return QSize(option.rect.width() if option.rect.width() > 0 else 320, height)

    def hitTestLink(self, position, index: QModelIndex) -> bool:  # noqa: N802
        """Return whether ``position`` falls inside the last painted link rect."""
        rect = self._link_rect.get(self._index_key(index))
        return bool(rect and rect.contains(position))

    def set_hover_link(self, key: object | None) -> None:
        """Set which link is currently hovered. Triggers repaint if changed."""
        if self._hovered_link_key != key:
            self._hovered_link_key = key
            if self.parent():
                self.parent().viewport().update()

    def toggleExpanded(self, index: QModelIndex) -> None:  # noqa: N802
        """Toggle expanded state and notify the view to recalculate row height."""
        key = self._index_key(index)
        if key in self._expanded_rows:
            self._expanded_rows.remove(key)
        else:
            self._expanded_rows.add(key)
        self.sizeHintChanged.emit(index)

    def _title_text(self, index: QModelIndex) -> str:
        return str(index.data(Qt.ItemDataRole.DisplayRole) or "")

    def _subtitle_text(self, index: QModelIndex) -> str:
        return ""

    def _link_text(self, index: QModelIndex) -> str:
        return ""

    def _expanded_content(self, index: QModelIndex) -> str:
        return ""

    def _index_key(self, index: QModelIndex) -> object:
        role_key = index.data(Qt.ItemDataRole.UserRole)
        if role_key is not None:
            return role_key
        return QPersistentModelIndex(index)

    def _is_expanded(self, index: QModelIndex) -> bool:
        return self._index_key(index) in self._expanded_rows

    # -- Template-method hooks (override in subclasses) ---------------------

    def _title_color(self, option: QStyleOptionViewItem) -> str:
        return Color.ANTHROPIC_NEAR_BLACK.value

    def _configure_title_font(self, font: QFont, option: QStyleOptionViewItem, index: QModelIndex) -> None:
        """Mutate *font* in-place (e.g. setStrikeOut). Default does nothing."""

    def _text_rect(self, card_rect: QRect, content_rect: QRect, index: QModelIndex) -> QRect:
        """Return the text-area rectangle. Default returns *content_rect* as-is."""
        return content_rect

    def _paint_extras(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex,
                      content_rect: QRect, text_rect: QRect, y: int) -> int:
        """Paint badges / covers / extra links. Return the new *y* cursor. Default is a no-op."""
        return y

    def _expanded_y_start(self, y: int, content_rect: QRect, index: QModelIndex) -> int:
        """Adjust where expanded content begins. Default returns *y* unchanged."""
        return y
