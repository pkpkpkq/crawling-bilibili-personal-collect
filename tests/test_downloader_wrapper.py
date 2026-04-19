from importlib import import_module
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_downloader_module_removed():
    assert not (ROOT / 'downloader.py').exists()
    try:
        import_module('downloader')
    except ImportError:
        pass
    else:
        raise AssertionError('importing downloader should fail')
