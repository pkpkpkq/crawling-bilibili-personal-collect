import pytest


def _get_qtbot_or_skip(request):
    try:
        return request.getfixturevalue("qtbot")
    except pytest.FixtureLookupError:
        pytest.skip("pytest-qt fixture not available")


def _get_qt_api_or_skip():
    qt_compat = pytest.importorskip("pytestqt.qt_compat")
    return qt_compat.qt_api


def test_qtbot_can_manage_widget_headlessly(request):
    qtbot = _get_qtbot_or_skip(request)
    qt_api = _get_qt_api_or_skip()

    widget = qt_api.QtWidgets.QWidget()
    widget.setObjectName("qt-harness-smoke")
    qtbot.addWidget(widget)

    widget.show()
    qtbot.wait(20)

    assert widget.objectName() == "qt-harness-smoke"


def test_qtbot_wait_signal_smoke(request):
    qtbot = _get_qtbot_or_skip(request)
    qt_api = _get_qt_api_or_skip()

    line_edit = qt_api.QtWidgets.QLineEdit()
    qtbot.addWidget(line_edit)

    with qtbot.waitSignal(line_edit.textChanged, timeout=1000):
        line_edit.setText("pytest-qt-ok")

    assert line_edit.text() == "pytest-qt-ok"
