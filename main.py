import json
import os
import time
import logging
from logging.handlers import RotatingFileHandler
from concurrent.futures import ThreadPoolExecutor, as_completed
from viewing import view
from database import (
    get_db_path, get_connection, init_db,
    upsert_collection, save_collection_videos, save_following_ups,
    record_crawl, get_collection_media_count, export_all_videos_csv,
    get_all_cover_urls, get_all_up_face_urls, migrate_from_json
)
import requests
import math
import sys
import shutil
import glob


# --- Default Settings ---

DEFAULT_SETTINGS = {
    "max_workers_crawl": 3,
    "max_workers_image": 10,
    "page_delay": 0.3,
    "image_retry": 3,
    "backup_keep_count": 5,
    "enable_incremental": True,
    "csv_export": True,
}


def load_config():
    """加载配置文件，合并默认设置"""
    try:
        with open('config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
    except FileNotFoundError:
        logging.error("配置文件 config.json 不存在")
        logging.error("请先运行 getcookie.py 来生成有效的 config.json 文件。")
        sys.exit(1)
    except json.JSONDecodeError as e:
        logging.error(f"配置文件 JSON 解析错误: {e}")
        sys.exit(1)

    uid = config.get("uid")
    cookie = config.get("cookie")
    if not uid:
        logging.error("配置文件中缺少 'uid'")
        sys.exit(1)
    if not cookie:
        cookie = "_uuid=F500E27C-018D-CC3F-17E8-C64812E174DA08613infoc; buvid3=475B7DAC-0579-421B-85B7-07A4076090B734771infoc; buvid_fp=475B7DAC-0579-421B-85B7-07A4076090B734771infoc; CURRENT_FNVAL=80; blackside_state=1; rpdid=|(k|k)~~RkkJ0J'uYk|YumRkm; fingerprint3=c1d980f375c848a729ebdd130960a847; CURRENT_QUALITY=112; LIVE_BUVID=AUTO9716210898194009; fingerprint_s=be57440a1cba44ed342ad526646463d4; bp_t_offset_51541144=529073781132033226; bp_video_offset_51541144=529330083309673464; bp_t_offset_289920431=529693188424888145; fingerprint=a43248e91a776fba5e92af41d1a900e0; buvid_fp_plain=95AEE299-5E58-4AA1-92EF-CFE2BE6C6243184999infoc; SESSDATA=41ff3c64%2C1637735786%2Cff017%2A51; bili_jct=c0a63b68e972a8d1acc44a3718075b58; DedeUserID=289920431; DedeUserID__ckMd5=c43d13bc962635fe; sid=bvgle9dv; PVID=3; bp_video_offset_289920431=529757320878990660; bfe_id=5db70a86bd1cbe8a88817507134f7bb5"
        logging.warning("配置文件中缺少 'cookie'，已使用默认Cookie，将无法爬取关注的up列表和未公开内容。")

    # 合并 settings
    settings = {**DEFAULT_SETTINGS, **config.get("settings", {})}

    return uid, cookie, settings


# --- Core Functions ---

def ProcessRawData(RawData):
    NewData = {}
    for i in RawData.values():
        media = {
            "id": i['id'], "BV": i['bv_id'], "是否失效": False,
            "up主": {"ID": i['upper']['mid'], "昵称": i['upper']['name'], "头像": i['upper']['face']},
            "视频信息": {"标题": i['title'], "封面": i['cover'], "简介": i['intro'], "时长": time.strftime("%H:%M:%S", time.gmtime(i['duration']))},
            "观众数据": {"播放量": i['cnt_info']['play'], "收藏量": i['cnt_info']['collect'], "弹幕数量": i['cnt_info']['danmaku']},
            "三个时间": {"上传时间": time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(i['ctime'])), "发布时间": time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(i['pubtime'])), "收藏时间": time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(i['fav_time']))}
        }
        NewData[str(media['id'])] = media
    return NewData


# --- Bilibili API Functions ---

def verify_cookie(headers):
    """验证Cookie是否有效"""
    try:
        response = requests.get('https://api.bilibili.com/x/web-interface/nav',
                                headers=headers, timeout=5)
        data = response.json()
        return data.get('code') == 0
    except Exception as e:
        logging.warning(f"Cookie验证失败: {e}")
        return False


def GetFavoriteIDList(uid, headers):
    """获取收藏夹列表，返回列表而非写入文件"""
    url = 'https://api.bilibili.com/x/v3/fav/folder/created/list-all'
    params = {'up_mid': uid, 'jsonp': 'jsonp'}
    try:
        response = requests.get(url=url, params=params, headers=headers)
        response.raise_for_status()
        assign = response.json()
        if assign.get('code') != 0:
            logging.error(f"获取收藏夹列表失败: {assign.get('message', 'API返回错误')}")
            return None
        logging.info('收藏夹列表获取成功')
        return assign.get('data', {}).get('list', [])
    except requests.RequestException as e:
        logging.error(f"请求收藏夹ID API时发生网络错误: {e}")
        return None


def GetFollowingUPs(uid, headers):
    """爬取关注的UP主列表，返回列表"""
    logging.info("开始爬取关注的UP主列表...")
    url = 'https://api.bilibili.com/x/relation/followings'
    params = {'vmid': uid, 'ps': 50, 'pn': 1, 'order': 'desc', 'order_type': 'attention', 'jsonp': 'jsonp'}
    all_following_ups = []
    consecutive_empty_pages = 0
    max_consecutive_empty = 2
    while True:
        try:
            response = requests.get(url, params=params, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data.get('code') == 0:
                following_list = data.get('data', {}).get('list', [])
                if not following_list:
                    consecutive_empty_pages += 1
                    logging.warning(f"关注列表第 {params['pn']} 页为空（连续空页: {consecutive_empty_pages}/{max_consecutive_empty}）")
                    if consecutive_empty_pages >= max_consecutive_empty:
                        logging.info("已获取所有关注的UP主。")
                        break
                else:
                    consecutive_empty_pages = 0
                    for up in following_list:
                        all_following_ups.append({"ID": up['mid'], "昵称": up['uname'], "头像": up['face']})
                logging.info(f"成功爬取第 {params['pn']} 页关注列表，已获取 {len(all_following_ups)} 位UP主。")
                params['pn'] += 1
                time.sleep(1)
            else:
                logging.error(f"获取关注列表时出错: {data.get('message', '未知API错误')}")
                break
        except requests.Timeout:
            logging.error(f"第 {params['pn']} 页关注列表请求超时")
            break
        except requests.RequestException as e:
            logging.error(f"请求关注列表API时发生网络错误: {e}")
            break
        except Exception as e:
            logging.error(f"处理关注列表数据时发生未知错误: {e}")
            break
    logging.info(f"关注的UP主列表爬取完成，共 {len(all_following_ups)} 位。")
    return all_following_ups


def GetOneFavorite(Media_Id, MaxPage, headers, page_delay=0.3):
    """爬取单个收藏夹的所有视频"""
    url = 'https://api.bilibili.com/x/v3/fav/resource/list'
    params = {'ps': 20, 'keyword': '', 'order': 'mtime', 'type': 0, 'tid': 0, 'platform': 'web', 'jsonp': 'jsonp', 'pn': 1, 'media_id': Media_Id}
    data = {}
    for pn in range(1, MaxPage):
        params['pn'] = pn
        logging.info(f"正在爬取收藏夹 {Media_Id} 第 {pn} 页")
        try:
            response = requests.get(url=url, params=params, headers=headers, timeout=10)
            response.raise_for_status()
            json_data = response.json()
            if json_data.get('code') != 0:
                logging.error(f"收藏夹 {Media_Id} 第 {pn} 页API返回错误: {json_data.get('message', '未知错误')}")
                break
            medias_list = json_data.get('data', {}).get('medias', [])
            if not medias_list:
                break
            for i in medias_list:
                data[str(i['id'])] = i
        except requests.Timeout:
            logging.error(f"收藏夹 {Media_Id} 第 {pn} 页请求超时")
            break
        except requests.RequestException as e:
            logging.error(f"收藏夹 {Media_Id} 第 {pn} 页网络错误: {e}")
            break
        except json.JSONDecodeError as e:
            logging.error(f"收藏夹 {Media_Id} 第 {pn} 页JSON解析错误: {e}")
            break
        # 翻页延迟
        if pn < MaxPage - 1:
            time.sleep(page_delay)
    return data


def crawl_one_favorite(fav_item, headers, db_path, settings):
    """爬取并保存一个收藏夹到数据库，返回统计信息。
    每个线程创建自己的数据库连接，避免跨线程共享 conn。
    """
    coll_id = fav_item['id']
    coll_name = fav_item['title']
    media_count = fav_item['media_count']

    # 增量爬取：对比 media_count（线程安全：独立连接）
    if settings.get('enable_incremental', True):
        with get_connection(db_path) as conn:
            old_count = get_collection_media_count(conn, coll_id)
        if old_count is not None and old_count == media_count:
            logging.info(f"跳过 {coll_name}（media_count 无变化: {media_count}）")
            return {'name': coll_name, 'skipped': True, 'new': 0, 'invalid': 0, 'unfav': 0}

    logging.info(f"爬取中...当前正在爬取 {coll_name}")
    max_page = math.ceil(media_count / 20) + 1
    raw_data = GetOneFavorite(coll_id, max_page, headers, settings.get('page_delay', 0.3))
    processed = ProcessRawData(raw_data)

    # 写入数据库（线程安全：独立连接）
    with get_connection(db_path) as conn:
        upsert_collection(conn, coll_id, coll_name, media_count)
        new_count, invalid_count, unfav_count = save_collection_videos(
            conn, coll_id, coll_name, processed
        )

    logging.info(f"收藏夹 {coll_name} 完成: {len(processed)} 条, 新增 {new_count}, 失效 {invalid_count}, 取消收藏 {unfav_count}")
    return {'name': coll_name, 'skipped': False, 'new': new_count, 'invalid': invalid_count, 'unfav': unfav_count}


# --- Image Fetching ---

def fetch_image(url, path, retry_count=3):
    """下载单张图片，支持重试"""
    if not (url and isinstance(url, str) and url.startswith(('http://', 'https://'))):
        return
    if os.path.exists(path):
        return
    for attempt in range(retry_count):
        try:
            response = requests.get(url, headers={'Referer': 'https://www.bilibili.com/'}, timeout=10)
            if response.status_code == 200 and 'image' in response.headers.get('Content-Type', ''):
                os.makedirs(os.path.dirname(path), exist_ok=True)
                with open(path, 'wb') as f:
                    f.write(response.content)
                return
        except Exception:
            pass
        if attempt < retry_count - 1:
            time.sleep(2 ** attempt)


def GetAllImages(conn, report_dir, settings):
    """从数据库获取URL并下载所有图片（封面去重存储）"""
    cover_urls = get_all_cover_urls(conn)
    face_urls = get_all_up_face_urls(conn)
    max_workers = settings.get('max_workers_image', 10)
    retry_count = settings.get('image_retry', 3)

    cover_dir = os.path.join(report_dir, '视频封面')
    face_dir = os.path.join(report_dir, 'up头像')
    os.makedirs(cover_dir, exist_ok=True)
    os.makedirs(face_dir, exist_ok=True)

    logging.info(f"开始下载图片（封面 {len(cover_urls)} 张, 头像 {len(face_urls)} 张, {max_workers} 线程）...")

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # 封面：统一以 BV 号为文件名（去重）
        for bv, url in cover_urls.items():
            cover_path = os.path.join(cover_dir, f'{bv}.jpg')
            executor.submit(fetch_image, url, cover_path, retry_count)

        # 头像
        for mid, url in face_urls.items():
            face_path = os.path.join(face_dir, f'{mid}.jpg')
            executor.submit(fetch_image, url, face_path, retry_count)

    logging.info("所有图片下载完成。")


# --- Cleanup ---

def cleanup_old_backups(keep_count=5):
    """清理旧的备份文件夹，保留最近 keep_count 个"""
    backups = sorted(glob.glob('收藏夹信息_backup_*'))
    if len(backups) > keep_count:
        for old_backup in backups[:-keep_count]:
            try:
                shutil.rmtree(old_backup)
                logging.info(f"已清理旧备份: {old_backup}")
            except OSError as e:
                logging.warning(f"清理备份失败 {old_backup}: {e}")


def cleanup_temp():
    """清理临时文件"""
    temp_dir = os.path.join('.', 'temp')
    if os.path.exists(temp_dir):
        try:
            shutil.rmtree(temp_dir)
            logging.info("已清理临时文件目录 temp/")
        except OSError as e:
            logging.warning(f"清理临时文件失败: {e}")


# --- Main Execution ---

if __name__ == "__main__":
    # 配置日志同时输出到文件和控制台
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(module)s - %(message)s')

    file_handler = logging.FileHandler('bilibili_crawler.log', mode='w', encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 1. 加载配置
    UID, COOKIE, SETTINGS = load_config()

    # 2. 设置通用请求头
    base_headers = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36',
        'Referer': 'https://www.bilibili.com/',
        'cookie': COOKIE
    }

    if not verify_cookie(base_headers):
        logging.warning("Cookie可能已过期，某些功能（如爬取关注列表）可能无法正常工作")

    # 3. 初始化数据库
    db_path = get_db_path()
    init_db(db_path)

    # 如果存在旧的 JSON 数据且数据库为空，自动迁移
    json_dir = '收藏夹信息/'
    if os.path.exists(json_dir):
        with get_connection(db_path) as conn:
            count = conn.execute("SELECT COUNT(*) as c FROM videos").fetchone()['c']
        if count == 0:
            logging.info("检测到旧 JSON 数据且数据库为空，正在自动迁移...")
            migrate_from_json(json_dir, db_path)

    # 4. 执行爬取流程
    report_dir = 'html_report'
    crawling_successful = False
    total_stats = {'new': 0, 'invalid': 0, 'unfav': 0, 'total': 0}

    try:
        STime = time.perf_counter()

        # 4a. 获取收藏夹列表
        fav_list = GetFavoriteIDList(UID, base_headers)
        if not fav_list:
            raise Exception("获取收藏夹列表失败，终止爬取。")

        # 4b. 爬取关注的UP主
        following_ups = GetFollowingUPs(UID, base_headers)

        # 4c. 保存关注UP主（在主线程中完成）
        if following_ups:
            with get_connection(db_path) as conn:
                save_following_ups(conn, following_ups)

        # 4d. 并发爬取所有收藏夹 (A1a)
        # 每个线程在 crawl_one_favorite 内部创建自己的数据库连接
        max_workers_crawl = SETTINGS.get('max_workers_crawl', 3)
        logging.info(f"开始并发爬取 {len(fav_list)} 个收藏夹（{max_workers_crawl} 线程）...")

        with ThreadPoolExecutor(max_workers=max_workers_crawl) as executor:
            future_to_fav = {
                executor.submit(crawl_one_favorite, fav, base_headers, db_path, SETTINGS): fav
                for fav in fav_list
            }
            for future in as_completed(future_to_fav):
                fav = future_to_fav[future]
                try:
                    result = future.result()
                    if not result.get('skipped'):
                        total_stats['new'] += result['new']
                        total_stats['invalid'] += result['invalid']
                        total_stats['unfav'] += result['unfav']
                except Exception as e:
                    logging.error(f"爬取收藏夹 {fav['title']} 时发生错误: {e}", exc_info=True)

        # 4d. 下载图片（封面去重存储 B4）
        with get_connection(db_path) as conn:
            GetAllImages(conn, report_dir, SETTINGS)
            total_stats['total'] = conn.execute("SELECT COUNT(*) as c FROM videos").fetchone()['c']

        ETime = time.perf_counter()
        crawl_duration = ETime - STime
        crawling_successful = True

        # 记录爬取历史
        with get_connection(db_path) as conn:
            record_crawl(conn, crawl_duration, total_stats['total'],
                         total_stats['new'], total_stats['invalid'],
                         total_stats['unfav'])

        logging.info(f"爬取完成！耗时 {time.strftime('%M:%S', time.gmtime(crawl_duration))}")
        logging.info(f"统计: 总视频 {total_stats['total']}, 新增 {total_stats['new']}, "
                     f"失效 {total_stats['invalid']}, 取消收藏 {total_stats['unfav']}")

    except Exception as e:
        logging.error(f"爬取主流程发生错误: {e}", exc_info=True)
        # 记录失败
        try:
            with get_connection(db_path) as conn:
                record_crawl(conn, 0, 0, 0, 0, 0, status='failed')
        except Exception:
            pass

    # 5. 清理工作 (B2, B3)
    cleanup_old_backups(SETTINGS.get('backup_keep_count', 5))
    cleanup_temp()

    # 6. 生成HTML报告
    if crawling_successful:
        STime = time.perf_counter()
        try:
            view(db_path, report_dir)
            ETime = time.perf_counter()
            logging.info(f"生成HTML报告所用时间: {time.strftime('%M:%S', time.gmtime(ETime - STime))}")
        except Exception as e:
            logging.error(f"生成HTML报告时发生错误: {e}", exc_info=True)

        # 7. 导出 CSV (C3a)
        if SETTINGS.get('csv_export', True):
            try:
                with get_connection(db_path) as conn:
                    export_all_videos_csv(conn, '收藏夹数据.csv')
            except Exception as e:
                logging.error(f"导出CSV时发生错误: {e}", exc_info=True)
    else:
        logging.info("由于爬取失败，跳过HTML报告生成。")
