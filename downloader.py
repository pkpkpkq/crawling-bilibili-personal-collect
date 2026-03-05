"""
Bilibili 收藏视频下载模块
基于 yt-dlp 实现，支持从数据库中选择视频下载

使用前需安装: pip install yt-dlp
"""

import os
import sys
import json
import logging
import subprocess
import tempfile
import atexit
from database import get_connection, get_videos_in_collection


def check_ytdlp():
    """检查 yt-dlp 是否已安装"""
    try:
        result = subprocess.run(['yt-dlp', '--version'], capture_output=True, text=True)
        logging.info(f"yt-dlp 版本: {result.stdout.strip()}")
        return True
    except FileNotFoundError:
        return False


def download_video(bv_id, output_dir, cookie_file=None, quality='best'):
    """
    下载单个视频
    
    Args:
        bv_id: 视频 BV 号
        output_dir: 输出目录
        cookie_file: cookie 文件路径（可选）
        quality: 画质选择 ('best', '1080p', '720p', '480p')
    
    Returns:
        bool: 下载是否成功
    """
    url = f'https://www.bilibili.com/video/{bv_id}'
    os.makedirs(output_dir, exist_ok=True)

    cmd = [
        'yt-dlp',
        '-o', os.path.join(output_dir, '%(title)s [%(id)s].%(ext)s'),
        '--no-playlist',
        '--embed-thumbnail',
        '--merge-output-format', 'mp4',
    ]

    # 画质设置
    quality_map = {
        'best': 'bestvideo+bestaudio/best',
        '1080p': 'bestvideo[height<=1080]+bestaudio/best[height<=1080]',
        '720p': 'bestvideo[height<=720]+bestaudio/best[height<=720]',
        '480p': 'bestvideo[height<=480]+bestaudio/best[height<=480]',
    }
    cmd.extend(['-f', quality_map.get(quality, quality_map['best'])])

    # Cookie 支持
    if cookie_file and os.path.exists(cookie_file):
        cmd.extend(['--cookies', cookie_file])

    cmd.append(url)

    try:
        logging.info(f"开始下载: {bv_id}")
        result = subprocess.run(cmd, timeout=600)
        if result.returncode == 0:
            logging.info(f"下载成功: {bv_id}")
            return True
        else:
            logging.error(f"下载失败 {bv_id} (返回码: {result.returncode})")
            return False
    except subprocess.TimeoutExpired:
        logging.error(f"下载超时: {bv_id}")
        return False
    except Exception as e:
        logging.error(f"下载出错 {bv_id}: {e}")
        return False


def export_cookies_for_ytdlp(config_path='config.json'):
    """
    从 config.json 导出 cookie 为 Netscape 格式的临时文件（yt-dlp 可用）。
    文件在进程退出时自动删除。
    """
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        cookie_str = config.get('cookie', '')
        if not cookie_str:
            logging.warning("config.json 中没有 cookie")
            return None

        lines = ['# Netscape HTTP Cookie File', '']
        for item in cookie_str.split(';'):
            item = item.strip()
            if '=' in item:
                key, value = item.split('=', 1)
                lines.append(f'.bilibili.com\tTRUE\t/\tFALSE\t0\t{key.strip()}\t{value.strip()}')

        # 写入临时文件，进程退出时自动清理
        tmp = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', prefix='bili_cookies_',
                                          delete=False, encoding='utf-8')
        tmp.write('\n'.join(lines))
        tmp.close()
        atexit.register(lambda: os.unlink(tmp.name) if os.path.exists(tmp.name) else None)
        logging.info(f"Cookie 已导出到临时文件")
        return tmp.name
    except Exception as e:
        logging.error(f"导出 cookie 失败: {e}")
        return None


def get_latest_collections(db_path):
    """获取最新的收藏夹列表（按名称去重，仅保留最近爬取的记录）"""
    with get_connection(db_path) as conn:
        # 先按名称分组，取 last_crawl_time 最新的那个 id
        rows = conn.execute("""
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
        """).fetchall()
    return rows


def download_collection(db_path, collection_id, output_base='downloads', quality='best',
                        cookie_file=None):
    """
    下载整个收藏夹的视频
    自动跳过已失效的视频（已被 B 站删除，无法下载）
    """
    with get_connection(db_path) as conn:
        videos = get_videos_in_collection(conn, collection_id, include_unfav=False)
        coll = conn.execute("SELECT name FROM collections WHERE id = ?", (collection_id,)).fetchone()
        coll_name = coll['name'] if coll else str(collection_id)

    output_dir = os.path.join(output_base, coll_name)
    success_count = 0
    fail_count = 0
    skip_invalid = 0

    for video in videos:
        if video['is_invalid']:
            skip_invalid += 1
            continue

        bv_id = video['bv_id']
        # 检查是否已下载
        existing = [f for f in os.listdir(output_dir) if bv_id in f] if os.path.exists(output_dir) else []
        if existing:
            logging.info(f"跳过已下载: {bv_id}")
            continue

        if download_video(bv_id, output_dir, cookie_file, quality):
            success_count += 1
        else:
            fail_count += 1

    if skip_invalid:
        logging.info(f"跳过 {skip_invalid} 个已失效视频（已被 B 站删除，无法下载）")
    logging.info(f"收藏夹 {coll_name} 下载完成: 成功 {success_count}, 失败 {fail_count}")
    return success_count, fail_count


def interactive_download(db_path='bilibili_data.db'):
    """交互式下载界面"""
    if not check_ytdlp():
        print("\n❌ 未找到 yt-dlp，请先安装:")
        print("   pip install yt-dlp")
        print("   或访问: https://github.com/yt-dlp/yt-dlp")
        return

    # 导出 cookie 到临时文件
    cookie_file = export_cookies_for_ytdlp()

    collections = get_latest_collections(db_path)

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
        print(f"\n  A. 下载单个视频（输入 BV 号）")
        print(f"  Q. 退出")

        choice = input("\n请选择 (编号/A/Q): ").strip()

        if choice.lower() == 'q':
            break
        elif choice.lower() == 'a':
            bv = input("请输入 BV 号: ").strip()
            if not bv.startswith('BV'):
                bv = 'BV' + bv
            quality = input("画质 (best/1080p/720p/480p, 默认 best): ").strip() or 'best'
            download_video(bv, 'downloads', cookie_file, quality)
        else:
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(collections):
                    coll = collections[idx]
                    print(f"\n选择了: {coll['name']}")
                    quality = input("画质 (best/1080p/720p/480p, 默认 best): ").strip() or 'best'
                    download_collection(db_path, coll['id'], 'downloads', quality, cookie_file)
                else:
                    print("无效的选择")
            except ValueError:
                print("无效的输入")


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    interactive_download()
