from app.ui.main_window import MainWindow


def test_main_window_creation(qapp):
    window = MainWindow()
    assert window is not None
    assert window.windowTitle() == "Bilibili Personal Collect"

    assert window.centralWidget() is not None
    layout = window.centralWidget().layout()
    assert layout is not None

    widgets = [layout.itemAt(i).widget() for i in range(layout.count())]
    assert any(w.metaObject().className() == "QListWidget" for w in widgets)
    assert any(w.metaObject().className() == "QStackedWidget" for w in widgets)
