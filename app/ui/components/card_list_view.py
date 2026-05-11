"""CardListView — reusable list view for card delegates with smooth scrolling."""

from PySide6.QtCore import QAbstractItemModel
from PySide6.QtWidgets import QListView

from app.models import PagedProxyModel
from app.theme import Spacing
from app.ui.components.pagination_bar import PaginationBar


class CardListView(QListView):
    """List view wrapper for model/proxy-backed card rows.

    The view deliberately owns no filtering, sorting, or paging behavior. Any
    ``QAbstractItemModel`` can be assigned via ``setModel``; paging remains the
    responsibility of ``PagedProxyModel`` and optional external controls.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("card-list-view")
        self.setUniformItemSizes(False)
        self.setSpacing(Spacing.SCALE_12)
        self.setContentsMargins(
            Spacing.SCALE_8,
            Spacing.SCALE_8,
            Spacing.SCALE_8,
            Spacing.SCALE_8,
        )
        self.setViewportMargins(0, 0, 0, Spacing.SCALE_8)
        self.setSelectionMode(QListView.SelectionMode.SingleSelection)
        self.setResizeMode(QListView.ResizeMode.Adjust)

        # Enable smooth pixel-based scrolling (instead of item-based jumps)
        self.setVerticalScrollMode(QListView.ScrollMode.ScrollPerPixel)
        self.setHorizontalScrollMode(QListView.ScrollMode.ScrollPerPixel)
        self.verticalScrollBar().setSingleStep(20)

    def setModel(self, model: QAbstractItemModel | None) -> None:  # noqa: N802
        """Accept any Qt item model or proxy without adding custom logic."""
        super().setModel(model)

    def mouseMoveEvent(self, event):  # noqa: N802
        """Track link hover state for delegate underline effect."""
        delegate = self.itemDelegate()
        if hasattr(delegate, "set_hover_link") and hasattr(delegate, "hitTestLink"):
            index = self.indexAt(event.pos())
            pos = self.viewport().mapFromGlobal(event.globalPos())
            key = delegate._index_key(index) if index.isValid() and hasattr(delegate, "_index_key") else None
            if index.isValid() and delegate.hitTestLink(pos, index):
                delegate.set_hover_link(key)
            else:
                delegate.set_hover_link(None)

            if hasattr(delegate, "hitTestUpLink") and hasattr(delegate, "setUpHoverLink"):
                if index.isValid() and delegate.hitTestUpLink(pos, index):
                    delegate.setUpHoverLink(key)
                else:
                    delegate.setUpHoverLink(None)
        super().mouseMoveEvent(event)

    def bind_paged_proxy(
        self,
        proxy: PagedProxyModel,
        pagination_bar: PaginationBar | None = None,
    ) -> None:
        """Bind a ``PagedProxyModel`` and optionally wire a ``PaginationBar``."""
        self.setModel(proxy)
        if pagination_bar is None:
            return

        pagination_bar.prev_button.clicked.connect(proxy.previousPage)
        pagination_bar.next_button.clicked.connect(proxy.nextPage)

        def refresh() -> None:
            pagination_bar.update(
                current=proxy.currentPage(),
                total_pages=proxy.pageCount(),
                total_items=proxy.totalRowCount(),
            )

        proxy.modelReset.connect(refresh)
        proxy.rowsInserted.connect(refresh)
        proxy.rowsRemoved.connect(refresh)
        proxy.layoutChanged.connect(refresh)
        pagination_bar.prev_button.clicked.connect(refresh)
        pagination_bar.next_button.clicked.connect(refresh)
        refresh()
