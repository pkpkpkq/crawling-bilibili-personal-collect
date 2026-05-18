"""Tests for shared UI component primitives."""

from pathlib import Path

from PySide6.QtCore import Qt, QRect
from PySide6.QtGui import QPainter, QPixmap
from PySide6.QtWidgets import QApplication, QStyleOptionViewItem, QVBoxLayout, QWidget

from app.models import PagedProxyModel, UpListRowRole, UpListRowsModel
from app.theme import Color, Spacing
from app.ui.components import (
    BaseCardDelegate,
    CardListView,
    EmptyState,
    FilterBar,
    LogPanel,
    PageHeader,
    PaginationBar,
    StatusBadge,
    SummaryCard,
    SurfaceCard,
)
from app.ui.strings import BTN_NEXT_PAGE, BTN_PREV_PAGE, EMPTY_NO_DATA


EVIDENCE_DIR = Path(__file__).resolve().parents[1] / ".sisyphus" / "evidence"


def _up_rows(count: int):
    return [
        {
            "mid": index,
            "name": f"UP {index:03d}",
            "face_url": f"https://example.invalid/{index}.jpg",
        }
        for index in range(1, count + 1)
    ]


class _TestCardDelegate(BaseCardDelegate):
    def _subtitle_text(self, index):
        return "播放 100\n收藏 20"

    def _link_text(self, index):
        return "查看详情"

    def _expanded_content(self, index):
        return "展开内容第一行\n展开内容第二行"


class TestPageHeader:
    def test_instantiation(self, qtbot):
        w = PageHeader("Title", "Sub")
        qtbot.addWidget(w)
        assert w.title_label.text() == "Title"
        assert w.title_label.objectName() == "page-header-title"
        assert w.subtitle_label is not None
        assert w.subtitle_label.text() == "Sub"
        assert w.subtitle_label.objectName() == "page-header-subtitle"

    def test_without_subtitle(self, qtbot):
        w = PageHeader("Solo")
        qtbot.addWidget(w)
        assert w.subtitle_label is None

    def test_set_title(self, qtbot):
        w = PageHeader("Old")
        qtbot.addWidget(w)
        w.set_title("New")
        assert w.title_label.text() == "New"

    def test_set_subtitle_lazily(self, qtbot):
        w = PageHeader("T")
        qtbot.addWidget(w)
        assert w.subtitle_label is None
        w.set_subtitle("Late sub")
        assert w.subtitle_label is not None
        assert w.subtitle_label.text() == "Late sub"
        assert w.subtitle_label.objectName() == "page-header-subtitle"


class TestSurfaceCard:
    def test_instantiation(self, qtbot):
        w = SurfaceCard()
        qtbot.addWidget(w)
        assert w.objectName() == "surface-card"
        margins = w.card_layout.contentsMargins()
        assert margins.left() == Spacing.CARD_PADDING
        assert margins.top() == Spacing.CARD_PADDING

    def test_add_child(self, qtbot):
        w = SurfaceCard()
        qtbot.addWidget(w)
        child = QWidget()
        w.card_layout.addWidget(child)
        assert w.card_layout.count() == 1


class TestSummaryCard:
    def test_instantiation(self, qtbot):
        w = SummaryCard("视频总数", "42")
        qtbot.addWidget(w)
        assert w.title_label.objectName() == "summary-card-title"
        assert w.title_label.text() == "视频总数"
        assert w.value_label.objectName() == "summary-card-value"
        assert w.value_label.text() == "42"

    def test_set_value(self, qtbot):
        w = SummaryCard("X", "0")
        qtbot.addWidget(w)
        w.set_value("99")
        assert w.value_label.text() == "99"


class TestEmptyState:
    def test_instantiation_with_subtitle(self, qtbot):
        w = EmptyState("Nothing here", "Try a different filter")
        qtbot.addWidget(w)
        assert w.title_label.objectName() == "empty-state-title"
        assert w.title_label.text() == "Nothing here"
        assert w.subtitle_label is not None
        assert w.subtitle_label.objectName() == "empty-state-subtitle"
        assert w.subtitle_label.text() == "Try a different filter"

    def test_default_title_uses_constant(self, qtbot):
        w = EmptyState()
        qtbot.addWidget(w)
        assert w.title_label.text() == EMPTY_NO_DATA

    def test_set_subtitle_lazily(self, qtbot):
        w = EmptyState("T")
        qtbot.addWidget(w)
        assert w.subtitle_label is None
        w.set_subtitle("Late sub")
        assert w.subtitle_label is not None
        assert w.subtitle_label.objectName() == "empty-state-subtitle"


class TestStatusBadge:
    def test_instantiation(self, qtbot):
        b = StatusBadge("Idle", "info")
        qtbot.addWidget(b)
        assert b.objectName() == "status-badge"
        assert b.text() == "Idle"

    def test_kind_info_color(self, qtbot):
        b = StatusBadge("Idle", "info")
        qtbot.addWidget(b)
        assert Color.CHARCOAL_WARM.value in b.styleSheet()

    def test_kind_success_color(self, qtbot):
        b = StatusBadge("Done", "success")
        qtbot.addWidget(b)
        assert Color.TERRACOTTA_BRAND.value in b.styleSheet()

    def test_kind_error_color(self, qtbot):
        b = StatusBadge("Failed", "error")
        qtbot.addWidget(b)
        assert Color.ERROR_CRIMSON.value in b.styleSheet()

    def test_kind_switching(self, qtbot):
        b = StatusBadge("A", "info")
        qtbot.addWidget(b)
        assert Color.CHARCOAL_WARM.value in b.styleSheet()
        b.set_status("B", "error")
        assert Color.ERROR_CRIMSON.value in b.styleSheet()
        assert b.text() == "B"
        b.set_status("C", "success")
        assert Color.TERRACOTTA_BRAND.value in b.styleSheet()

    def test_unknown_kind_falls_back(self, qtbot):
        b = StatusBadge("X", "unknown_kind")
        qtbot.addWidget(b)
        assert Color.CHARCOAL_WARM.value in b.styleSheet()


class TestLogPanel:
    def test_instantiation(self, qtbot):
        w = LogPanel()
        qtbot.addWidget(w)
        assert w.text_edit.isReadOnly()

    def test_append_and_clear(self, qtbot):
        w = LogPanel()
        qtbot.addWidget(w)
        w.append_log("line 1")
        w.append_log("line 2")
        assert "line 1" in w.text_edit.toPlainText()
        assert "line 2" in w.text_edit.toPlainText()
        w.clear_logs()
        assert w.text_edit.toPlainText() == ""


class TestPaginationBar:
    def test_instantiation_buttons_disabled(self, qtbot):
        w = PaginationBar()
        qtbot.addWidget(w)
        assert not w.prev_button.isEnabled()
        assert not w.next_button.isEnabled()
        assert w.prev_button.text() == BTN_PREV_PAGE
        assert w.next_button.text() == BTN_NEXT_PAGE

    def test_update_first_page(self, qtbot):
        w = PaginationBar()
        qtbot.addWidget(w)
        w.update(current=1, total_pages=5, total_items=250)
        assert not w.prev_button.isEnabled()
        assert w.next_button.isEnabled()
        assert "1" in w.page_label.text()
        assert "5" in w.page_label.text()

    def test_update_middle_page(self, qtbot):
        w = PaginationBar()
        qtbot.addWidget(w)
        w.update(current=3, total_pages=5, total_items=250)
        assert w.prev_button.isEnabled()
        assert w.next_button.isEnabled()

    def test_update_last_page(self, qtbot):
        w = PaginationBar()
        qtbot.addWidget(w)
        w.update(current=5, total_pages=5, total_items=250)
        assert w.prev_button.isEnabled()
        assert not w.next_button.isEnabled()

    def test_single_page(self, qtbot):
        w = PaginationBar()
        qtbot.addWidget(w)
        w.update(current=1, total_pages=1, total_items=10)
        assert not w.prev_button.isEnabled()
        assert not w.next_button.isEnabled()

    def test_zero_pages(self, qtbot):
        w = PaginationBar()
        qtbot.addWidget(w)
        w.update(current=0, total_pages=0, total_items=0)
        assert not w.prev_button.isEnabled()
        assert not w.next_button.isEnabled()


class TestFilterBar:
    def test_instantiation_without_sort(self, qtbot):
        w = FilterBar()
        qtbot.addWidget(w)
        assert w.sort_combo is None
        assert w.search_input is not None

    def test_instantiation_with_sort(self, qtbot):
        w = FilterBar(sort_items=["A", "B"])
        qtbot.addWidget(w)
        assert w.sort_combo is not None
        assert w.sort_combo.count() == 2


class TestCardListView:
    def test_bind_paged_proxy_keeps_page_slice_at_50(self, qtbot):
        source = UpListRowsModel(_up_rows(120))
        proxy = PagedProxyModel()
        proxy.setSourceModel(source)

        view = CardListView()
        pager = PaginationBar()
        qtbot.addWidget(view)
        qtbot.addWidget(pager)

        view.bind_paged_proxy(proxy, pager)

        assert view.objectName() == "card-list-view"
        assert view.model() is proxy
        assert proxy.pageSize() == 50
        assert proxy.rowCount() == 50
        assert proxy.data(proxy.index(49, 0), int(UpListRowRole.MID)) == 50

        pager.next_button.click()
        assert proxy.currentPage() == 2
        assert proxy.rowCount() == 50
        assert proxy.data(proxy.index(0, 0), int(UpListRowRole.MID)) == 51


class TestBaseCardDelegate:
    def test_size_hint_changes_when_expanded(self, qtbot):
        source = UpListRowsModel(_up_rows(1))
        delegate = _TestCardDelegate()
        index = source.index(0, 0)
        option = QStyleOptionViewItem()
        option.rect = QRect(0, 0, 400, 80)

        collapsed = delegate.sizeHint(option, index)
        with qtbot.waitSignal(delegate.sizeHintChanged, timeout=1000):
            delegate.toggleExpanded(index)
        expanded = delegate.sizeHint(option, index)

        assert expanded.height() > collapsed.height()

    def test_hit_test_link_only_within_link_rect(self, qtbot):
        source = UpListRowsModel(_up_rows(1))
        delegate = _TestCardDelegate()
        index = source.index(0, 0)
        option = QStyleOptionViewItem()
        option.rect = QRect(0, 0, 400, 140)
        pixmap = QPixmap(400, 140)
        pixmap.fill(Qt.GlobalColor.transparent)

        painter = QPainter(pixmap)
        delegate.paint(painter, option, index)
        painter.end()

        link_rect = next(iter(delegate._link_rect.values()))
        assert delegate.hitTestLink(link_rect.center(), index)
        assert not delegate.hitTestLink(option.rect.bottomRight(), index)

    def test_painting_smoke_does_not_crash(self, qtbot):
        source = UpListRowsModel(_up_rows(1))
        delegate = _TestCardDelegate()
        index = source.index(0, 0)
        option = QStyleOptionViewItem()
        option.rect = QRect(0, 0, 420, 180)
        pixmap = QPixmap(420, 180)
        pixmap.fill(Qt.GlobalColor.transparent)

        painter = QPainter(pixmap)
        delegate.paint(painter, option, index)
        painter.end()

        assert not pixmap.isNull()


class TestScreenshotGrab:
    def test_screenshot(self, qtbot):
        container = QWidget()
        qtbot.addWidget(container)
        container.setObjectName("screenshot-container")
        layout = QVBoxLayout(container)

        header = PageHeader("数据概览", "收藏夹统计")
        layout.addWidget(header)

        card = SurfaceCard()
        summary = SummaryCard("视频总数", "1,234")
        card.card_layout.addWidget(summary)
        layout.addWidget(card)

        empty = EmptyState("暂无数据", "试试换个筛选条件")
        layout.addWidget(empty)

        badge = StatusBadge("爬取完成", "success")
        layout.addWidget(badge)

        pager = PaginationBar()
        pager.update(current=2, total_pages=10, total_items=500)
        layout.addWidget(pager)

        container.resize(800, 600)
        container.show()
        QApplication.processEvents()

        EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
        out = EVIDENCE_DIR / "task-2-components.png"
        container.grab().save(str(out))
        assert out.exists()
        assert out.stat().st_size > 0
