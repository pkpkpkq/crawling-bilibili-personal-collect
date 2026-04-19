import atexit
import json
import logging
import os
import subprocess
import tempfile
from typing import Any, Callable

from app.repositories import collections as collections_repo
from app.repositories import videos as videos_repo
from app.repositories.connection import get_connection

QUALITY_MAP = {
    "best": "bestvideo+bestaudio/best",
    "1080p": "bestvideo[height<=1080]+bestaudio/best[height<=1080]",
    "720p": "bestvideo[height<=720]+bestaudio/best[height<=720]",
    "480p": "bestvideo[height<=480]+bestaudio/best[height<=480]",
}


class DownloadService:
    """Reusable yt-dlp backed download service without interactive I/O."""

    def __init__(self, *, subprocess_run: Callable[..., Any] = subprocess.run):
        self.subprocess_run = subprocess_run

    @staticmethod
    def _build_error(
        code: str,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        error = {"code": code, "message": message}
        if details is not None:
            error["details"] = details
        return error

    @classmethod
    def _missing_ytdlp_error(cls) -> dict[str, Any]:
        return cls._build_error(
            "missing_ytdlp",
            "未找到 yt-dlp，请先安装: pip install yt-dlp",
            {"install_url": "https://github.com/yt-dlp/yt-dlp"},
        )

    def check_ytdlp(self) -> dict[str, Any]:
        """Check whether yt-dlp is available and return structured result."""
        try:
            result = self.subprocess_run(
                ["yt-dlp", "--version"],
                capture_output=True,
                text=True,
            )
        except FileNotFoundError:
            return {
                "success": False,
                "available": False,
                "error": self._missing_ytdlp_error(),
            }
        except Exception as exc:  # pylint: disable=broad-except
            return {
                "success": False,
                "available": False,
                "error": self._build_error(
                    "ytdlp_check_failed",
                    f"检查 yt-dlp 失败: {exc}",
                ),
            }

        if result.returncode == 0:
            version = (result.stdout or "").strip()
            logging.info(f"yt-dlp 版本: {version}")
            return {"success": True, "available": True, "version": version}

        return {
            "success": False,
            "available": False,
            "error": self._build_error(
                "ytdlp_check_failed",
                f"yt-dlp 检查失败 (返回码: {result.returncode})",
                {
                    "returncode": result.returncode,
                    "stderr": (result.stderr or "").strip(),
                },
            ),
        }

    def export_cookies_for_ytdlp(self, config_path: str = "config.json") -> dict[str, Any]:
        """Export cookie from config.json into Netscape format file for yt-dlp."""
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
        except FileNotFoundError:
            return {
                "success": False,
                "cookie_file": None,
                "error": self._build_error(
                    "config_missing",
                    f"配置文件不存在: {config_path}",
                ),
            }
        except json.JSONDecodeError as exc:
            return {
                "success": False,
                "cookie_file": None,
                "error": self._build_error(
                    "config_invalid_json",
                    f"配置文件解析失败: {exc}",
                ),
            }
        except Exception as exc:  # pylint: disable=broad-except
            return {
                "success": False,
                "cookie_file": None,
                "error": self._build_error(
                    "cookie_export_failed",
                    f"读取配置失败: {exc}",
                ),
            }

        cookie_str = config.get("cookie", "")
        if not cookie_str:
            logging.warning("config.json 中没有 cookie")
            return {
                "success": False,
                "cookie_file": None,
                "error": self._build_error(
                    "cookie_missing",
                    "config.json 中没有 cookie",
                ),
            }

        lines = ["# Netscape HTTP Cookie File", ""]
        for item in cookie_str.split(";"):
            item = item.strip()
            if "=" in item:
                key, value = item.split("=", 1)
                lines.append(
                    f".bilibili.com\tTRUE\t/\tFALSE\t0\t{key.strip()}\t{value.strip()}"
                )

        try:
            tmp = tempfile.NamedTemporaryFile(
                mode="w",
                suffix=".txt",
                prefix="bili_cookies_",
                delete=False,
                encoding="utf-8",
            )
            tmp.write("\n".join(lines))
            tmp.close()
            atexit.register(lambda: os.unlink(tmp.name) if os.path.exists(tmp.name) else None)
            logging.info("Cookie 已导出到临时文件")
            return {"success": True, "cookie_file": tmp.name}
        except Exception as exc:  # pylint: disable=broad-except
            logging.error(f"导出 cookie 失败: {exc}")
            return {
                "success": False,
                "cookie_file": None,
                "error": self._build_error(
                    "cookie_export_failed",
                    f"导出 cookie 失败: {exc}",
                ),
            }

    def get_latest_collections(self, db_path: str) -> list[dict[str, Any]]:
        """Get latest collections by name, preserving active-count lookup behavior."""
        with get_connection(db_path) as conn:
            rows = conn.execute(
                """
                SELECT sub.id, sub.name,
                       COUNT(CASE WHEN vc.is_active = 1 THEN 1 END) as active_count
                FROM (
                    SELECT id, name
                    FROM collections
                    WHERE last_crawl_time IS NOT NULL
                    AND id = (
                        SELECT id FROM collections c2
                        WHERE c2.name = collections.name
                        ORDER BY c2.last_crawl_time DESC
                        LIMIT 1
                    )
                ) sub
                LEFT JOIN video_collection vc ON sub.id = vc.collection_id
                GROUP BY sub.id
                ORDER BY sub.name
                """
            ).fetchall()
        return [dict(row) for row in rows]

    @staticmethod
    def build_download_command(
        bv_id: str,
        output_dir: str,
        cookie_file: str | None = None,
        quality: str = "best",
    ) -> list[str]:
        cmd = [
            "yt-dlp",
            "-o",
            os.path.join(output_dir, "%(title)s [%(id)s].%(ext)s"),
            "--no-playlist",
            "--embed-thumbnail",
            "--merge-output-format",
            "mp4",
            "-f",
            QUALITY_MAP.get(quality, QUALITY_MAP["best"]),
        ]

        if cookie_file and os.path.exists(cookie_file):
            cmd.extend(["--cookies", cookie_file])

        cmd.append(f"https://www.bilibili.com/video/{bv_id}")
        return cmd

    def download_video(
        self,
        bv_id: str,
        output_dir: str,
        cookie_file: str | None = None,
        quality: str = "best",
        *,
        check_dependency: bool = True,
    ) -> dict[str, Any]:
        """Download one video and return structured result."""
        if check_dependency:
            dependency_status = self.check_ytdlp()
            if not dependency_status.get("success"):
                return {
                    "success": False,
                    "bv_id": bv_id,
                    "output_dir": output_dir,
                    "error": dependency_status.get("error"),
                }

        os.makedirs(output_dir, exist_ok=True)
        cmd = self.build_download_command(bv_id, output_dir, cookie_file, quality)

        try:
            logging.info(f"开始下载: {bv_id}")
            result = self.subprocess_run(cmd, timeout=600)
        except subprocess.TimeoutExpired:
            logging.error(f"下载超时: {bv_id}")
            return {
                "success": False,
                "bv_id": bv_id,
                "output_dir": output_dir,
                "error": self._build_error(
                    "download_timeout",
                    f"下载超时: {bv_id}",
                ),
            }
        except FileNotFoundError:
            return {
                "success": False,
                "bv_id": bv_id,
                "output_dir": output_dir,
                "error": self._missing_ytdlp_error(),
            }
        except Exception as exc:  # pylint: disable=broad-except
            logging.error(f"下载出错 {bv_id}: {exc}")
            return {
                "success": False,
                "bv_id": bv_id,
                "output_dir": output_dir,
                "error": self._build_error(
                    "download_exception",
                    f"下载出错 {bv_id}: {exc}",
                ),
            }

        if result.returncode == 0:
            logging.info(f"下载成功: {bv_id}")
            return {
                "success": True,
                "bv_id": bv_id,
                "output_dir": output_dir,
            }

        logging.error(f"下载失败 {bv_id} (返回码: {result.returncode})")
        return {
            "success": False,
            "bv_id": bv_id,
            "output_dir": output_dir,
            "error": self._build_error(
                "download_failed",
                f"下载失败 {bv_id}",
                {"returncode": result.returncode},
            ),
        }

    def download_collection(
        self,
        db_path: str,
        collection_id: int,
        output_base: str = "downloads",
        quality: str = "best",
        cookie_file: str | None = None,
    ) -> dict[str, Any]:
        """Download all active videos in one collection with invalid-video skipping."""
        dependency_status = self.check_ytdlp()
        if not dependency_status.get("success"):
            return {
                "success": False,
                "collection_id": collection_id,
                "success_count": 0,
                "fail_count": 0,
                "skipped_invalid_count": 0,
                "skipped_existing_count": 0,
                "error": dependency_status.get("error"),
            }

        with get_connection(db_path) as conn:
            videos = videos_repo.get_videos_in_collection(
                conn,
                collection_id,
                include_unfav=False,
            )
            coll = collections_repo.get_collection_by_id(conn, collection_id)
            coll_name = coll["name"] if coll else str(collection_id)

        output_dir = os.path.join(output_base, coll_name)
        success_count = 0
        fail_count = 0
        skipped_invalid_count = 0
        skipped_existing_count = 0

        for video in videos:
            if video.get("is_invalid"):
                skipped_invalid_count += 1
                continue

            bv_id = video["bv_id"]
            existing = [f for f in os.listdir(output_dir) if bv_id in f] if os.path.exists(output_dir) else []
            if existing:
                logging.info(f"跳过已下载: {bv_id}")
                skipped_existing_count += 1
                continue

            result = self.download_video(
                bv_id,
                output_dir,
                cookie_file=cookie_file,
                quality=quality,
                check_dependency=False,
            )
            if result.get("success"):
                success_count += 1
            else:
                fail_count += 1

        if skipped_invalid_count:
            logging.info(
                f"跳过 {skipped_invalid_count} 个已失效视频（已被 B 站删除，无法下载）"
            )
        logging.info(f"收藏夹 {coll_name} 下载完成: 成功 {success_count}, 失败 {fail_count}")

        return {
            "success": fail_count == 0,
            "collection_id": collection_id,
            "collection_name": coll_name,
            "output_dir": output_dir,
            "success_count": success_count,
            "fail_count": fail_count,
            "skipped_invalid_count": skipped_invalid_count,
            "skipped_existing_count": skipped_existing_count,
            "error": None,
        }
