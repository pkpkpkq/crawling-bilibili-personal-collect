from app.ui.main_window import MainWindow


def test_qapplication_instance(qapp):
    assert qapp is not None


def test_main_window_instance(qapp):
    window = MainWindow()
    assert window is not None
