import json
import logging
import math
import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import Any, Callable, Mapping

import requests

from app.services.auth_service import verify_cookie_headers
from app.services.cache_service import CacheService
from app.services.config_service import DEFAULT_SETTINGS as SERVICE_DEFAULT_SETTINGS
from database import (
    get_all_cover_urls,
    get_all_up_face_urls,
    get_collection_incremental_info,
    get_connection,
    get_db_path,
    init_db,
    migrate_from_json,
    record_crawl,
    save_collection_videos,
    save_following_ups,
    upsert_collection,
)


DEFAULT_SETTINGS = dict(SERVICE_DEFAULT_SETTINGS)


@dataclass
class CrawlRunResult:
    success: bool
    duration_seconds: float
    stats: dict[str, int]
    error: str | None = None


class CrawlService:
    """Headless crawl orchestration for CLI and automation entrypoints."""

    def __init__(
        self,
        *,
        request_get: Callable[..., Any] = requests.get,
        sleep_func: Callable[[float], None] = time.sleep,
        perf_counter_func: Callable[[], float] = time.perf_counter,
    ):
        self.request_get = request_get
        self.sleep_func = sleep_func
        self.perf_counter_func = perf_counter_func
        self._api_semaphore = threading.Semaphore(2)

    @staticmethod
    def _resolve_worker_count(raw_value: Any, fallback: int) -> int:
        try:
            return max(1, int(raw_value))
        except (TypeError, ValueError):
            return fallback

    def _rate_limited_get(self, url: str, **kwargs):
        with self._api_semaphore:
            response = self.request_get(url, **kwargs)
            self.sleep_func(0.5)
            return response

    @staticmethod
    def build_headers(cookie: str) -> dict[str, str]:
        return {
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36",
            "Referer": "https://www.bilibili.com/",
            "cookie": cookie,
        }

    @staticmethod
    def process_raw_data(raw_data):
        new_data = {}
        for item in raw_data.values():
            upper = item.get("upper") or {}
            cnt = item.get("cnt_info") or {}
            is_invalid = (
                item.get("attr", 0) in (1, 9)
                or item.get("title") == "已失效视频"
                or upper.get("mid", 0) == 0
            )
            media = {
                "id": item.get("id", 0),
                "BV": item.get("bv_id", ""),
                "是否失效": is_invalid,
                "up主": {
                    "ID": upper.get("mid", 0),
                    "昵称": upper.get("name", "未知"),
                    "头像": upper.get("face", ""),
                },
                "视频信息": {
                    "标题": item.get("title", "未知标题"),
                    "封面": item.get("cover", ""),
                    "简介": item.get("intro", ""),
                    "时长": time.strftime("%H:%M:%S", time.gmtime(item.get("duration", 0))),
                },
                "观众数据": {
                    "播放量": cnt.get("play", 0),
                    "收藏量": cnt.get("collect", 0),
                    "弹幕数量": cnt.get("danmaku", 0),
                },
                "三个时间": {
                    "上传时间": time.strftime(
                        "%Y-%m-%d %H:%M:%S", time.localtime(item.get("ctime", 0))
                    ),
                    "发布时间": time.strftime(
                        "%Y-%m-%d %H:%M:%S", time.localtime(item.get("pubtime", 0))
                    ),
                    "收藏时间": time.strftime(
                        "%Y-%m-%d %H:%M:%S", time.localtime(item.get("fav_time", 0))
                    ),
                },
            }
            new_data[str(media["id"])] = media
        return new_data

    def verify_cookie(self, headers: Mapping[str, str]) -> bool:
        result = verify_cookie_headers(
            headers,
            timeout=5,
            require_login=False,
            request_get=self.request_get,
        )
        if not result.valid and result.error:
            logging.warning(f"Cookie验证失败: {result.error}")
        return result.valid

    def get_favorite_id_list(self, uid: Any, headers: Mapping[str, str]):
        url = "https://api.bilibili.com/x/v3/fav/folder/created/list-all"
        params = {"up_mid": uid, "jsonp": "jsonp"}
        try:
            response = self.request_get(
                url=url,
                params=params,
                headers=dict(headers),
                timeout=10,
            )
            if hasattr(response, "raise_for_status"):
                response.raise_for_status()
            assign = response.json()
            if assign.get("code") != 0:
                logging.error(f"获取收藏夹列表失败: {assign.get('message', 'API返回错误')}")
                return None
            logging.info("收藏夹列表获取成功")
            return assign.get("data", {}).get("list", [])
        except requests.RequestException as exc:
            logging.error(f"请求收藏夹ID API时发生网络错误: {exc}")
            return None

    def get_following_ups(self, uid: Any, headers: Mapping[str, str]):
        logging.info("开始爬取关注的UP主列表...")
        url = "https://api.bilibili.com/x/relation/followings"
        params = {
            "vmid": uid,
            "ps": 50,
            "pn": 1,
            "order": "desc",
            "order_type": "attention",
            "jsonp": "jsonp",
        }
        all_following_ups = []
        consecutive_empty_pages = 0
        max_consecutive_empty = 2
        while True:
            try:
                response = self._rate_limited_get(
                    url,
                    params=params,
                    headers=dict(headers),
                    timeout=10,
                )
                if hasattr(response, "raise_for_status"):
                    response.raise_for_status()
                data = response.json()
                if data.get("code") == 0:
                    following_list = data.get("data", {}).get("list", [])
                    if not following_list:
                        consecutive_empty_pages += 1
                        logging.warning(
                            f"关注列表第 {params['pn']} 页为空（连续空页: {consecutive_empty_pages}/{max_consecutive_empty}）"
                        )
                        if consecutive_empty_pages >= max_consecutive_empty:
                            logging.info("已获取所有关注的UP主。")
                            break
                    else:
                        consecutive_empty_pages = 0
                        for up in following_list:
                            all_following_ups.append(
                                {"ID": up["mid"], "昵称": up["uname"], "头像": up["face"]}
                            )
                    logging.info(
                        f"成功爬取第 {params['pn']} 页关注列表，已获取 {len(all_following_ups)} 位UP主。"
                    )
                    params["pn"] += 1
                    self.sleep_func(1)
                else:
                    logging.error(
                        f"获取关注列表时出错: {data.get('message', '未知API错误')}"
                    )
                    break
            except requests.Timeout:
                logging.error(f"第 {params['pn']} 页关注列表请求超时")
                break
            except requests.RequestException as exc:
                logging.error(f"请求关注列表API时发生网络错误: {exc}")
                break
            except Exception as exc:  # pylint: disable=broad-except
                logging.error(f"处理关注列表数据时发生未知错误: {exc}")
                break
        logging.info(f"关注的UP主列表爬取完成，共 {len(all_following_ups)} 位。")
        return all_following_ups

    def get_one_favorite(
        self,
        media_id,
        max_page,
        headers,
        page_delay=0.3,
    ):
        url = "https://api.bilibili.com/x/v3/fav/resource/list"
        params = {
            "ps": 20,
            "keyword": "",
            "order": "mtime",
            "type": 0,
            "tid": 0,
            "platform": "web",
            "jsonp": "jsonp",
            "pn": 1,
            "media_id": media_id,
        }
        data = {}
        for pn in range(1, max_page):
            params["pn"] = pn
            logging.info(f"正在爬取收藏夹 {media_id} 第 {pn} 页")
            try:
                response = self._rate_limited_get(
                    url,
                    params=params,
                    headers=dict(headers),
                    timeout=10,
                )
                if hasattr(response, "raise_for_status"):
                    response.raise_for_status()
                json_data = response.json()
                if json_data.get("code") != 0:
                    logging.error(
                        f"收藏夹 {media_id} 第 {pn} 页API返回错误: {json_data.get('message', '未知错误')}"
                    )
                    break
                medias_list = json_data.get("data", {}).get("medias", [])
                if not medias_list:
                    break
                for item in medias_list:
                    data[str(item["id"])] = item
            except requests.Timeout:
                logging.error(f"收藏夹 {media_id} 第 {pn} 页请求超时")
                break
            except requests.RequestException as exc:
                logging.error(f"收藏夹 {media_id} 第 {pn} 页网络错误: {exc}")
                break
            except json.JSONDecodeError as exc:
                logging.error(f"收藏夹 {media_id} 第 {pn} 页JSON解析错误: {exc}")
                break
            if pn < max_page - 1:
                self.sleep_func(page_delay)
        return data

    def crawl_one_favorite(self, fav_item, headers, db_path, settings):
        coll_id = fav_item["id"]
        coll_name = fav_item["title"]
        media_count = fav_item["media_count"]
        api_mtime = fav_item.get("mtime", 0)

        if settings.get("enable_incremental", True):
            with get_connection(db_path) as conn:
                old_count, old_mtime = get_collection_incremental_info(conn, coll_id)
            if (
                old_count is not None
                and old_count == media_count
                and old_mtime is not None
                and old_mtime >= api_mtime
            ):
                logging.info(f"跳过 {coll_name}（media_count 和 mtime 均无变化）")
                return {
                    "name": coll_name,
                    "skipped": True,
                    "new": 0,
                    "invalid": 0,
                    "unfav": 0,
                }

        logging.info(f"爬取中...当前正在爬取 {coll_name}")
        max_page = math.ceil(media_count / 20) + 1
        raw_data = self.get_one_favorite(
            coll_id,
            max_page,
            headers,
            settings.get("page_delay", 0.3),
        )
        processed = self.process_raw_data(raw_data)

        with get_connection(db_path) as conn:
            upsert_collection(conn, coll_id, coll_name, media_count, api_mtime)
            new_count, invalid_count, unfav_count = save_collection_videos(
                conn,
                coll_id,
                coll_name,
                processed,
            )

        logging.info(
            f"收藏夹 {coll_name} 完成: {len(processed)} 条, 新增 {new_count}, 失效 {invalid_count}, 取消收藏 {unfav_count}"
        )
        return {
            "name": coll_name,
            "skipped": False,
            "new": new_count,
            "invalid": invalid_count,
            "unfav": unfav_count,
        }

    def fetch_image(self, url, path, retry_count=3):
        if not (url and isinstance(url, str) and url.startswith(("http://", "https://"))):
            return False
        if os.path.exists(path):
            return True
        for attempt in range(retry_count):
            try:
                response = self.request_get(
                    url,
                    headers={"Referer": "https://www.bilibili.com/"},
                    timeout=10,
                )
                if response.status_code == 200 and "image" in response.headers.get(
                    "Content-Type", ""
                ):
                    os.makedirs(os.path.dirname(path), exist_ok=True)
                    with open(path, "wb") as file:
                        file.write(response.content)
                    return True
            except Exception:  # pylint: disable=broad-except
                pass
            if attempt < retry_count - 1:
                self.sleep_func(2**attempt)
        return False

    def sync_images(
        self,
        db_path: str,
        settings: Mapping[str, Any],
        *,
        report_dir: str = "html_report",
        cache_service: CacheService | None = None,
    ):
        cache_service = cache_service or CacheService()

        with get_connection(db_path) as conn:
            cover_urls = get_all_cover_urls(conn)
            face_urls = get_all_up_face_urls(conn)

        max_workers = self._resolve_worker_count(settings.get("max_workers_image", 10), 10)
        retry_count = self._resolve_worker_count(settings.get("image_retry", 3), 3)

        logging.info(
            f"开始下载图片（封面 {len(cover_urls)} 张, 头像 {len(face_urls)} 张, {max_workers} 线程）..."
        )

        futures = []
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            for bv, url in cover_urls.items():
                cover_path = cache_service.get_cover_file_path(bv)
                futures.append(executor.submit(self.fetch_image, url, cover_path, retry_count))

            for mid, url in face_urls.items():
                face_path = cache_service.get_up_face_file_path(mid)
                futures.append(executor.submit(self.fetch_image, url, face_path, retry_count))

            success = sum(1 for future in as_completed(futures) if future.result() is True)

        logging.info(f"图片下载完成：{success}/{len(futures)} 张成功")
        return {"success": success, "total": len(futures)}

    @staticmethod
    def initialize_database(db_path: str):
        init_db(db_path)

        json_dir = "收藏夹信息/"
        if os.path.exists(json_dir):
            with get_connection(db_path) as conn:
                count = conn.execute("SELECT COUNT(*) as c FROM videos").fetchone()["c"]
            if count == 0:
                logging.info("检测到旧 JSON 数据且数据库为空，正在自动迁移...")
                migrate_from_json(json_dir, db_path)

    @staticmethod
    def persist_following_ups(db_path: str, following_ups: list[dict[str, Any]]):
        if not following_ups:
            return
        with get_connection(db_path) as conn:
            save_following_ups(conn, following_ups)

    @staticmethod
    def record_success(db_path: str, duration_seconds: float, stats: Mapping[str, int]):
        with get_connection(db_path) as conn:
            record_crawl(
                conn,
                duration_seconds,
                stats["total"],
                stats["new"],
                stats["invalid"],
                stats["unfav"],
            )

    @staticmethod
    def record_failure(db_path: str):
        with get_connection(db_path) as conn:
            record_crawl(conn, 0, 0, 0, 0, 0, status="failed")

    def run_headless_crawl(
        self,
        uid: Any,
        cookie: str,
        settings: Mapping[str, Any],
        *,
        db_path: str | None = None,
        report_dir: str = "html_report",
    ) -> CrawlRunResult:
        resolved_db_path = db_path or get_db_path()
        run_settings = dict(DEFAULT_SETTINGS)
        run_settings.update(dict(settings or {}))

        try:
            self.initialize_database(resolved_db_path)

            base_headers = self.build_headers(cookie)
            if not self.verify_cookie(base_headers):
                logging.warning("Cookie可能已过期，某些功能（如爬取关注列表）可能无法正常工作")

            start_time = self.perf_counter_func()
            total_stats = {"new": 0, "invalid": 0, "unfav": 0, "total": 0}

            fav_list = self.get_favorite_id_list(uid, base_headers)
            if not fav_list:
                raise RuntimeError("获取收藏夹列表失败，终止爬取。")

            following_ups = self.get_following_ups(uid, base_headers)
            self.persist_following_ups(resolved_db_path, following_ups)

            max_workers_crawl = self._resolve_worker_count(
                run_settings.get("max_workers_crawl", 3),
                3,
            )
            logging.info(
                f"开始并发爬取 {len(fav_list)} 个收藏夹（{max_workers_crawl} 线程）..."
            )

            with ThreadPoolExecutor(max_workers=max_workers_crawl) as executor:
                future_to_fav = {
                    executor.submit(
                        self.crawl_one_favorite,
                        fav,
                        base_headers,
                        resolved_db_path,
                        run_settings,
                    ): fav
                    for fav in fav_list
                }
                for future in as_completed(future_to_fav):
                    fav = future_to_fav[future]
                    try:
                        result = future.result()
                        if not result.get("skipped"):
                            total_stats["new"] += result["new"]
                            total_stats["invalid"] += result["invalid"]
                            total_stats["unfav"] += result["unfav"]
                    except Exception as exc:  # pylint: disable=broad-except
                        logging.error(
                            f"爬取收藏夹 {fav.get('title', '未知收藏夹')} 时发生错误: {exc}",
                            exc_info=True,
                        )

            self.sync_images(resolved_db_path, run_settings, report_dir=report_dir)

            with get_connection(resolved_db_path) as conn:
                total_stats["total"] = conn.execute(
                    "SELECT COUNT(*) as c FROM videos"
                ).fetchone()["c"]

            duration_seconds = self.perf_counter_func() - start_time
            self.record_success(resolved_db_path, duration_seconds, total_stats)

            logging.info(
                f"爬取完成！耗时 {time.strftime('%M:%S', time.gmtime(duration_seconds))}"
            )
            logging.info(
                f"统计: 总视频 {total_stats['total']}, 新增 {total_stats['new']}, "
                f"失效 {total_stats['invalid']}, 取消收藏 {total_stats['unfav']}"
            )

            return CrawlRunResult(
                success=True,
                duration_seconds=duration_seconds,
                stats=total_stats,
            )

        except Exception as exc:  # pylint: disable=broad-except
            logging.error(f"爬取主流程发生错误: {exc}", exc_info=True)
            try:
                self.record_failure(resolved_db_path)
            except Exception:  # pylint: disable=broad-except
                pass
            return CrawlRunResult(
                success=False,
                duration_seconds=0,
                stats={"new": 0, "invalid": 0, "unfav": 0, "total": 0},
                error=str(exc),
            )
