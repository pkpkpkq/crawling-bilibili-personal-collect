import os
import tempfile
import json
from PySide6.QtWidgets import QMessageBox
from PySide6.QtCore import Qt
from app.ui.pages.settings_page import SettingsPage
from app.services import config_service

def test_settings_page_config_roundtrip(qtbot, mocker):
    with tempfile.NamedTemporaryFile(delete=False, mode='w', encoding='utf-8') as f:
        json.dump({"uid": "roundtrip", "cookie": "SESSDATA=123; DedeUserID=456", "settings": {"max_workers_crawl": 2}}, f)
        temp_path = f.name
        
    orig_load = config_service.load_config
    orig_save = config_service.save_config
    
    mocker.patch("app.ui.pages.settings_page.config_service.load_config", side_effect=lambda: orig_load(temp_path))
    mocker.patch("app.ui.pages.settings_page.config_service.save_config", side_effect=lambda uid, cookie, settings: orig_save(uid, cookie, temp_path, settings))
    
    try:
        page = SettingsPage()
        qtbot.addWidget(page)
        
        assert page.uid == "roundtrip"
        assert page.spin_max_workers_crawl.value() == 2
        
        page.spin_max_workers_crawl.setValue(4)
        mocker.patch.object(QMessageBox, "information")
        
        qtbot.mouseClick(page.btn_save, Qt.LeftButton)
        
        uid, cookie, settings = orig_load(temp_path)
        assert uid == "roundtrip"
        assert settings["max_workers_crawl"] == 4
    finally:
        os.remove(temp_path)
