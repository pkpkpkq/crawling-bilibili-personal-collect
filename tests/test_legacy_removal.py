from importlib import import_module
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_legacy_modules_are_gone():
    for module_name in ('server', 'viewing', 'getcookie', 'downloader'):
        module_path = ROOT / f'{module_name}.py'
        assert not module_path.exists(), f'{module_path} should be removed'
        try:
            import_module(module_name)
        except ImportError:
            pass
        else:
            raise AssertionError(f'importing {module_name} should fail')
