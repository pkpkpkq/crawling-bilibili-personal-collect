import pytest
from PySide6.QtWidgets import QMessageBox
from PySide6.QtCore import Qt
from app.ui.pages.settings_page import SettingsPage

def test_settings_page_invalid_cookie(qtbot, mocker):
    mocker.patch("app.services.config_service.load_config", return_value=("123", "", {}))
    mock_save = mocker.patch("app.services.config_service.save_config")
    mock_msgbox = mocker.patch.object(QMessageBox, "warning")
    
    page = SettingsPage()
    qtbot.addWidget(page)
    
    # Put invalid cookie
    page.text_cookie.setPlainText("invalid_cookie_str")
    
    qtbot.mouseClick(page.btn_save, Qt.LeftButton)
    
    # Should not save
    mock_save.assert_not_called()
    mock_msgbox.assert_called_once()
    args = mock_msgbox.call_args[0]
    assert "Invalid Cookie" in args[1]
