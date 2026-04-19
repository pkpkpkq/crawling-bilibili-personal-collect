from PySide6.QtWidgets import QMessageBox
from PySide6.QtCore import Qt
from app.ui.pages.settings_page import SettingsPage

def test_settings_page_init(qtbot, mocker):
    mocker.patch("app.services.config_service.load_config", return_value=("123", "cookie", {}))
    page = SettingsPage()
    qtbot.addWidget(page)
    
    assert page.spin_max_workers_crawl.value() == 3  # default
    assert page.text_cookie.toPlainText() == "cookie"

def test_settings_page_save(qtbot, mocker):
    mocker.patch("app.services.config_service.load_config", return_value=("123", "cookie", {}))
    mock_save = mocker.patch("app.services.config_service.save_config")
    mock_msgbox = mocker.patch.object(QMessageBox, "information")
    
    page = SettingsPage()
    qtbot.addWidget(page)
    
    page.spin_max_workers_crawl.setValue(5)
    
    # We also need to mock parse_manual_cookie_input
    mocker.patch("app.services.auth_service.parse_manual_cookie_input", return_value={"success": True})
    
    qtbot.mouseClick(page.btn_save, Qt.LeftButton)
    
    mock_save.assert_called_once()
    called_args = mock_save.call_args[1]
    assert called_args["settings"]["max_workers_crawl"] == 5
    mock_msgbox.assert_called_once()
