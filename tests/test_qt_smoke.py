import pytest
from PySide6.QtWidgets import QApplication


def test_qapplication_instance(qapp):
    assert qapp is not None
