from app.models import PagedProxyModel, UpListRowRole, UpListRowsModel


def _rows(count: int):
    return [
        {
            "mid": index,
            "name": f"UP {index:03d}",
            "face_url": f"https://example.invalid/{index}.jpg",
        }
        for index in range(1, count + 1)
    ]


def _visible_mids(proxy: PagedProxyModel):
    return [proxy.data(proxy.index(i, 0), int(UpListRowRole.MID)) for i in range(proxy.rowCount())]


def test_paged_proxy_default_is_50_items_per_page(qapp):
    source = UpListRowsModel(_rows(120))
    proxy = PagedProxyModel()
    proxy.setSourceModel(source)

    assert proxy.pageSize() == 50
    assert proxy.pageCount() == 3
    assert proxy.currentPage() == 1
    assert proxy.rowCount() == 50
    assert _visible_mids(proxy)[0] == 1
    assert _visible_mids(proxy)[-1] == 50


def test_paged_proxy_navigation_and_bounds(qapp):
    source = UpListRowsModel(_rows(120))
    proxy = PagedProxyModel(page_size=50)
    proxy.setSourceModel(source)

    proxy.nextPage()
    assert proxy.currentPage() == 2
    assert proxy.rowCount() == 50
    assert _visible_mids(proxy)[0] == 51
    assert _visible_mids(proxy)[-1] == 100

    proxy.nextPage()
    assert proxy.currentPage() == 3
    assert proxy.rowCount() == 20
    assert _visible_mids(proxy)[0] == 101
    assert _visible_mids(proxy)[-1] == 120

    # Clamps to last page.
    proxy.setCurrentPage(99)
    assert proxy.currentPage() == 3

    proxy.previousPage()
    assert proxy.currentPage() == 2


def test_paged_proxy_page_size_change_recomputes_page_count(qapp):
    source = UpListRowsModel(_rows(120))
    proxy = PagedProxyModel(page_size=50)
    proxy.setSourceModel(source)

    proxy.setCurrentPage(3)
    proxy.setPageSize(30)

    assert proxy.pageSize() == 30
    assert proxy.pageCount() == 4
    assert proxy.currentPage() == 3
    assert proxy.rowCount() == 30
    assert _visible_mids(proxy)[0] == 61


def test_paged_proxy_handles_empty_source(qapp):
    source = UpListRowsModel([])
    proxy = PagedProxyModel()
    proxy.setSourceModel(source)

    assert proxy.pageCount() == 1
    assert proxy.currentPage() == 1
    assert proxy.rowCount() == 0
