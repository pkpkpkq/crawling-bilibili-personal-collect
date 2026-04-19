"""
Bilibili 收藏视频下载模块
基于 yt-dlp 实现，支持从数据库中选择视频下载

使用前需安装: pip install yt-dlp
"""

import logging

from app.services.download_service import DownloadService


def _get_service() -> DownloadService:
    return DownloadService()


def check_ytdlp(service: DownloadService | None = None):
    """检查 yt-dlp 是否已安装"""
    active_service = service or _get_service()
    result = active_service.check_ytdlp()
    return bool(result.get("success"))


def download_video(
    bv_id,
    output_dir,
    cookie_file=None,
    quality="best",
    service: DownloadService | None = None,
):
    """
    下载单个视频

    Returns:
        bool: 下载是否成功
    """
    active_service = service or _get_service()
    result = active_service.download_video(
        bv_id,
        output_dir,
        cookie_file=cookie_file,
        quality=quality,
    )
    return bool(result.get("success"))


def export_cookies_for_ytdlp(
    config_path="config.json",
    service: DownloadService | None = None,
):
    """
    从 config.json 导出 cookie 为 Netscape 格式的临时文件（yt-dlp 可用）。
    文件在进程退出时自动删除。
    """
    active_service = service or _get_service()
    result = active_service.export_cookies_for_ytdlp(config_path)
    if result.get("success"):
        return result.get("cookie_file")
    return None


def get_latest_collections(db_path, service: DownloadService | None = None):
    """获取最新的收藏夹列表（按名称去重，仅保留最近爬取的记录）"""
    active_service = service or _get_service()
    return active_service.get_latest_collections(db_path)


def download_collection(
    db_path,
    collection_id,
    output_base="downloads",
    quality="best",
    cookie_file=None,
    service: DownloadService | None = None,
):
    """
    下载整个收藏夹的视频
    自动跳过已失效的视频（已被 B 站删除，无法下载）
    """
    active_service = service or _get_service()
    result = active_service.download_collection(
        db_path,
        collection_id,
        output_base=output_base,
        quality=quality,
        cookie_file=cookie_file,
    )
    return result.get("success_count", 0), result.get("fail_count", 0)


def interactive_download(db_path="bilibili_data.db"):
    """交互式下载界面"""
    service = _get_service()

    ytdlp_status = service.check_ytdlp()
    if not ytdlp_status.get("success"):
        print("\n❌ 未找到 yt-dlp，请先安装:")
        print("   pip install yt-dlp")
        print("   或访问: https://github.com/yt-dlp/yt-dlp")
        return

    cookie_result = service.export_cookies_for_ytdlp()
    cookie_file = cookie_result.get("cookie_file") if cookie_result.get("success") else None

    collections = service.get_latest_collections(db_path)

    if not collections:
        print("❌ 数据库中没有收藏夹数据，请先运行 main.py 爬取数据。")
        return

    while True:
        print("\n" + "=" * 60)
        print("  Bilibili 视频下载工具")
        print("=" * 60)
        print("\n收藏夹列表:")
        for i, coll in enumerate(collections, 1):
            print(f"  {i}. {coll['name']} ({coll['active_count']} 个视频)")
        print("\n  A. 下载单个视频（输入 BV 号）")
        print("  Q. 退出")

        choice = input("\n请选择 (编号/A/Q): ").strip()

        if choice.lower() == "q":
            break
        if choice.lower() == "a":
            bv = input("请输入 BV 号: ").strip()
            if not bv.startswith("BV"):
                bv = "BV" + bv
            quality = input("画质 (best/1080p/720p/480p, 默认 best): ").strip() or "best"
            service.download_video(bv, "downloads", cookie_file=cookie_file, quality=quality)
            continue

        try:
            idx = int(choice) - 1
        except ValueError:
            print("无效的输入")
            continue

        if not 0 <= idx < len(collections):
            print("无效的选择")
            continue

        coll = collections[idx]
        print(f"\n选择了: {coll['name']}")
        quality = input("画质 (best/1080p/720p/480p, 默认 best): ").strip() or "best"
        service.download_collection(
            db_path,
            coll["id"],
            output_base="downloads",
            quality=quality,
            cookie_file=cookie_file,
        )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    interactive_download()
