import os


class CacheService:
    """Shared resolver for cached cover and UP avatar paths."""

    CACHE_ROOT = "cache"
    COVERS_DIR = "covers"
    UP_FACES_DIR = "up_faces"

    def __init__(self, base_dir: str = "."):
        self.base_dir = os.path.abspath(base_dir)

    @staticmethod
    def _to_posix(path: str) -> str:
        return path.replace("\\", "/")

    def _cache_relative(self, *parts: str) -> str:
        return self._to_posix(os.path.join(self.CACHE_ROOT, *parts))

    @staticmethod
    def _report_relative(path: str) -> str:
        return path if path.startswith("../") else f"../{path}"

    def _cache_dir_path(self, *parts: str) -> str:
        return os.path.join(self.base_dir, self.CACHE_ROOT, *parts)

    @staticmethod
    def _ensure_dir(path: str) -> None:
        os.makedirs(path, exist_ok=True)

    def get_cover_relative_path(self, bv_id: str) -> str:
        return self._cache_relative(self.COVERS_DIR, f"{bv_id}.jpg")

    def get_up_face_relative_path(self, mid: str | int) -> str:
        return self._cache_relative(self.UP_FACES_DIR, f"{mid}.jpg")

    def get_cover_report_path(self, bv_id: str) -> str:
        return self._report_relative(self.get_cover_relative_path(bv_id))

    def get_up_face_report_path(self, mid: str | int) -> str:
        return self._report_relative(self.get_up_face_relative_path(mid))

    def get_cover_file_path(self, bv_id: str) -> str:
        cover_dir = self._cache_dir_path(self.COVERS_DIR)
        self._ensure_dir(cover_dir)
        return os.path.join(cover_dir, f"{bv_id}.jpg")

    def get_up_face_file_path(self, mid: str | int) -> str:
        face_dir = self._cache_dir_path(self.UP_FACES_DIR)
        self._ensure_dir(face_dir)
        return os.path.join(face_dir, f"{mid}.jpg")
