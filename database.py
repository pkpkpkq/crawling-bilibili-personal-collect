"""
Bilibili 收藏夹数据 SQLite 数据库管理模块

表结构:
- collections: 收藏夹列表
- videos: 视频信息（以 bv_id 为主键）
- video_collection: 视频与收藏夹的多对多关联（含收藏/取消时间）
- ups: UP主信息
- following_ups: 关注的UP主列表
- crawl_history: 爬取历史记录
"""

import sqlite3
import os
import json
import logging
import time
from contextlib import contextmanager


DB_NAME = 'bilibili_data.db'


def get_db_path(base_dir='.'):
    return os.path.join(base_dir, DB_NAME)


@contextmanager
def get_connection(db_path=None):
    """获取数据库连接的上下文管理器"""
    if db_path is None:
        db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db(db_path=None):
    """初始化数据库，创建所有表"""
    if db_path is None:
        db_path = get_db_path()
    with get_connection(db_path) as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS collections (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                media_count INTEGER DEFAULT 0,
                last_crawl_time TEXT
            );

            CREATE TABLE IF NOT EXISTS ups (
                mid INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                face_url TEXT
            );

            CREATE TABLE IF NOT EXISTS videos (
                bv_id TEXT PRIMARY KEY,
                av_id INTEGER,
                title TEXT NOT NULL,
                cover_url TEXT,
                intro TEXT,
                duration TEXT,
                up_mid INTEGER,
                play_count INTEGER DEFAULT 0,
                collect_count INTEGER DEFAULT 0,
                danmaku_count INTEGER DEFAULT 0,
                upload_time TEXT,
                publish_time TEXT,
                is_invalid INTEGER DEFAULT 0,
                FOREIGN KEY (up_mid) REFERENCES ups(mid)
            );

            CREATE TABLE IF NOT EXISTS video_collection (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                bv_id TEXT NOT NULL,
                collection_id INTEGER NOT NULL,
                fav_time TEXT,
                unfav_time TEXT,
                is_active INTEGER DEFAULT 1,
                FOREIGN KEY (bv_id) REFERENCES videos(bv_id),
                FOREIGN KEY (collection_id) REFERENCES collections(id),
                UNIQUE(bv_id, collection_id)
            );

            CREATE TABLE IF NOT EXISTS following_ups (
                mid INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                face_url TEXT
            );

            CREATE TABLE IF NOT EXISTS crawl_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                crawl_time TEXT NOT NULL,
                duration_seconds REAL,
                total_videos INTEGER DEFAULT 0,
                new_videos INTEGER DEFAULT 0,
                invalid_videos INTEGER DEFAULT 0,
                unfav_videos INTEGER DEFAULT 0,
                status TEXT DEFAULT 'success'
            );

            CREATE INDEX IF NOT EXISTS idx_vc_bv ON video_collection(bv_id);
            CREATE INDEX IF NOT EXISTS idx_vc_coll ON video_collection(collection_id);
            CREATE INDEX IF NOT EXISTS idx_videos_up ON videos(up_mid);
            CREATE INDEX IF NOT EXISTS idx_vc_fav_time ON video_collection(fav_time);
        """)
    logging.info(f"数据库已初始化: {db_path}")


# --- 写入操作 ---

def upsert_collection(conn, coll_id, name, media_count):
    """插入或更新收藏夹"""
    conn.execute("""
        INSERT INTO collections (id, name, media_count, last_crawl_time)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            name = excluded.name,
            media_count = excluded.media_count,
            last_crawl_time = excluded.last_crawl_time
    """, (coll_id, name, media_count, time.strftime('%Y-%m-%d %H:%M:%S')))


def upsert_up(conn, mid, name, face_url):
    """插入或更新UP主"""
    conn.execute("""
        INSERT INTO ups (mid, name, face_url)
        VALUES (?, ?, ?)
        ON CONFLICT(mid) DO UPDATE SET
            name = excluded.name,
            face_url = excluded.face_url
    """, (mid, name, face_url))


def upsert_video(conn, video_data):
    """插入或更新视频信息"""
    bv = video_data['BV']
    info = video_data['视频信息']
    up = video_data['up主']
    stats = video_data['观众数据']
    times = video_data['三个时间']

    # 先 upsert UP主
    upsert_up(conn, up['ID'], up['昵称'], up['头像'])

    is_invalid = 1 if video_data.get('是否失效', False) else 0

    # 如果视频已失效且数据库中有旧数据，保留旧数据中非空字段
    if is_invalid:
        existing = conn.execute("SELECT * FROM videos WHERE bv_id = ?", (bv,)).fetchone()
        if existing and existing['title'] != '已失效视频':
            # 保留旧标题等信息，只标记失效
            conn.execute("UPDATE videos SET is_invalid = 1 WHERE bv_id = ?", (bv,))
            return

    conn.execute("""
        INSERT INTO videos (bv_id, av_id, title, cover_url, intro, duration,
                           up_mid, play_count, collect_count, danmaku_count,
                           upload_time, publish_time, is_invalid)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(bv_id) DO UPDATE SET
            title = CASE WHEN excluded.title = '已失效视频' THEN videos.title ELSE excluded.title END,
            cover_url = CASE WHEN excluded.cover_url IS NULL OR excluded.cover_url = '' THEN videos.cover_url ELSE excluded.cover_url END,
            intro = CASE WHEN excluded.intro IS NULL OR excluded.intro = '' THEN videos.intro ELSE excluded.intro END,
            duration = excluded.duration,
            up_mid = excluded.up_mid,
            play_count = excluded.play_count,
            collect_count = excluded.collect_count,
            danmaku_count = excluded.danmaku_count,
            upload_time = excluded.upload_time,
            publish_time = excluded.publish_time,
            is_invalid = excluded.is_invalid
    """, (bv, video_data['id'], info['标题'], info['封面'], info['简介'], info['时长'],
          up['ID'], stats['播放量'], stats['收藏量'], stats['弹幕数量'],
          times['上传时间'], times['发布时间'], is_invalid))


def add_video_to_collection(conn, bv_id, collection_id, fav_time):
    """将视频添加到收藏夹"""
    conn.execute("""
        INSERT INTO video_collection (bv_id, collection_id, fav_time, is_active)
        VALUES (?, ?, ?, 1)
        ON CONFLICT(bv_id, collection_id) DO UPDATE SET
            fav_time = excluded.fav_time,
            is_active = 1,
            unfav_time = NULL
    """, (bv_id, collection_id, fav_time))


def mark_unfavorited(conn, bv_id, collection_id):
    """标记视频在某个收藏夹中已取消收藏"""
    unfav_time = time.strftime('%Y-%m-%d %H:%M:%S')
    conn.execute("""
        UPDATE video_collection
        SET is_active = 0, unfav_time = ?
        WHERE bv_id = ? AND collection_id = ? AND is_active = 1
    """, (unfav_time, bv_id, collection_id))


def save_collection_videos(conn, collection_id, collection_name, processed_videos):
    """
    保存一个收藏夹的所有视频数据。
    processed_videos: ProcessRawData() 处理后的字典 {str_id: video_data}
    返回: (new_count, invalid_count, unfav_count)
    """
    new_count = 0
    invalid_count = 0
    unfav_count = 0

    # 获取该收藏夹当前活跃的视频BV列表
    current_active = set()
    rows = conn.execute(
        "SELECT bv_id FROM video_collection WHERE collection_id = ? AND is_active = 1",
        (collection_id,)
    ).fetchall()
    for row in rows:
        current_active.add(row['bv_id'])

    new_bv_set = set()
    for video_data in processed_videos.values():
        bv = video_data['BV']
        new_bv_set.add(bv)

        # 检查是否为新视频
        existing = conn.execute("SELECT bv_id FROM videos WHERE bv_id = ?", (bv,)).fetchone()
        if not existing:
            new_count += 1

        # 写入视频和关联
        upsert_video(conn, video_data)
        add_video_to_collection(conn, bv, collection_id, video_data['三个时间']['收藏时间'])

        if video_data.get('是否失效', False):
            invalid_count += 1

    # 标记已取消收藏的视频
    for old_bv in current_active - new_bv_set:
        mark_unfavorited(conn, old_bv, collection_id)
        unfav_count += 1
        video = conn.execute("SELECT title FROM videos WHERE bv_id = ?", (old_bv,)).fetchone()
        if video:
            logging.info(f"{video['title']} 已取消收藏（收藏夹: {collection_name}）")

    return new_count, invalid_count, unfav_count


def save_following_ups(conn, ups_list):
    """保存关注的UP主列表"""
    conn.execute("DELETE FROM following_ups")
    for up in ups_list:
        conn.execute("""
            INSERT INTO following_ups (mid, name, face_url)
            VALUES (?, ?, ?)
            ON CONFLICT(mid) DO UPDATE SET
                name = excluded.name,
                face_url = excluded.face_url
        """, (up['ID'], up['昵称'], up['头像']))
        # 同步到 ups 表
        upsert_up(conn, up['ID'], up['昵称'], up['头像'])


def record_crawl(conn, duration_seconds, total_videos, new_videos, invalid_videos, unfav_videos, status='success'):
    """记录一次爬取历史"""
    conn.execute("""
        INSERT INTO crawl_history (crawl_time, duration_seconds, total_videos,
                                   new_videos, invalid_videos, unfav_videos, status)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (time.strftime('%Y-%m-%d %H:%M:%S'), duration_seconds,
          total_videos, new_videos, invalid_videos, unfav_videos, status))


# --- 读取操作 ---

def get_all_collections(conn):
    """获取所有收藏夹"""
    return conn.execute("SELECT * FROM collections ORDER BY name").fetchall()


def get_collection_by_id(conn, coll_id):
    """获取单个收藏夹"""
    return conn.execute("SELECT * FROM collections WHERE id = ?", (coll_id,)).fetchone()


def get_collection_media_count(conn, coll_id):
    """获取收藏夹已记录的 media_count"""
    row = conn.execute("SELECT media_count FROM collections WHERE id = ?", (coll_id,)).fetchone()
    return row['media_count'] if row else None


def get_videos_in_collection(conn, collection_id, include_unfav=True):
    """获取收藏夹中的所有视频"""
    query = """
        SELECT v.*, vc.fav_time, vc.unfav_time, vc.is_active,
               u.name as up_name, u.face_url as up_face_url,
               c.name as collection_name
        FROM video_collection vc
        JOIN videos v ON vc.bv_id = v.bv_id
        JOIN ups u ON v.up_mid = u.mid
        JOIN collections c ON vc.collection_id = c.id
        WHERE vc.collection_id = ?
    """
    if not include_unfav:
        query += " AND vc.is_active = 1"
    query += " ORDER BY vc.fav_time DESC"
    return conn.execute(query, (collection_id,)).fetchall()


def get_video_history(conn, bv_id):
    """获取视频的收藏历史（跨收藏夹）"""
    rows = conn.execute("""
        SELECT vc.fav_time, vc.unfav_time, vc.is_active, c.name as collection_name
        FROM video_collection vc
        JOIN collections c ON vc.collection_id = c.id
        WHERE vc.bv_id = ?
        ORDER BY vc.fav_time
    """, (bv_id,)).fetchall()

    history = []
    for row in rows:
        history.append({
            "type": "add",
            "collection": row['collection_name'],
            "time": row['fav_time']
        })
        if row['unfav_time']:
            history.append({
                "type": "remove",
                "collection": row['collection_name'],
                "time": row['unfav_time']
            })
    return history


def get_all_videos_index(conn):
    """获取所有视频的索引数据（用于全局搜索）"""
    rows = conn.execute("""
        SELECT v.bv_id, v.title, v.cover_url, v.is_invalid,
               v.up_mid, u.name as up_name, u.face_url as up_face_url,
               v.play_count, v.collect_count, v.danmaku_count, v.duration,
               v.publish_time
        FROM videos v
        JOIN ups u ON v.up_mid = u.mid
    """).fetchall()

    video_index = {}
    for row in rows:
        bv = row['bv_id']
        history = get_video_history(conn, bv)

        # 获取所有关联的收藏夹
        vc_rows = conn.execute("""
            SELECT vc.*, c.name as collection_name
            FROM video_collection vc
            JOIN collections c ON vc.collection_id = c.id
            WHERE vc.bv_id = ?
            ORDER BY vc.fav_time DESC
        """, (bv,)).fetchall()

        # 确定最新状态
        is_unfavorited = all(r['is_active'] == 0 for r in vc_rows) if vc_rows else False
        latest_active = next((r for r in vc_rows if r['is_active']), None)
        latest_any = vc_rows[0] if vc_rows else None
        latest = latest_active or latest_any

        latest_collection = latest['collection_name'] if latest else 'N/A'
        latest_fav_time = latest['fav_time'] if latest else 'N/A'

        video_index[bv] = {
            "bvid": bv,
            "info": {
                "title": row['title'],
                "up_name": row['up_name'],
                "up_id": row['up_mid'],
                "is_invalid": bool(row['is_invalid']),
                "is_unfavorited": is_unfavorited,
                "cover_path": f"视频封面/{bv}.jpg",
                "up_face_path": f"up头像/{row['up_mid']}.jpg",
            },
            "history": history,
            "latest_collection": latest_collection,
            "latest_fav_time": latest_fav_time,
        }

    return video_index


def get_all_following_ups(conn):
    """获取所有关注的UP主"""
    return conn.execute("SELECT * FROM following_ups ORDER BY name").fetchall()


def get_all_up_face_urls(conn):
    """获取所有UP主的头像URL"""
    return {str(row['mid']): row['face_url']
            for row in conn.execute("SELECT mid, face_url FROM ups").fetchall()}


def get_all_cover_urls(conn):
    """获取所有视频封面URL（以BV号为键）"""
    return {row['bv_id']: row['cover_url']
            for row in conn.execute("SELECT bv_id, cover_url FROM videos").fetchall()}


# --- 统计查询 ---

def get_stats(conn):
    """获取统计数据（用于仪表盘）"""
    stats = {}

    # 基础统计
    stats['total_videos'] = conn.execute("SELECT COUNT(*) as c FROM videos").fetchone()['c']
    stats['total_collections'] = conn.execute("SELECT COUNT(*) as c FROM collections").fetchone()['c']
    stats['total_ups'] = conn.execute("SELECT COUNT(DISTINCT up_mid) as c FROM videos").fetchone()['c']
    stats['invalid_videos'] = conn.execute("SELECT COUNT(*) as c FROM videos WHERE is_invalid = 1").fetchone()['c']
    stats['following_ups'] = conn.execute("SELECT COUNT(*) as c FROM following_ups").fetchone()['c']

    # 每个收藏夹的视频数量
    stats['collection_counts'] = [
        {"name": row['name'], "count": row['c']}
        for row in conn.execute("""
            SELECT c.name, COUNT(vc.bv_id) as c
            FROM collections c
            LEFT JOIN video_collection vc ON c.id = vc.collection_id AND vc.is_active = 1
            GROUP BY c.id
            ORDER BY c DESC
        """).fetchall()
    ]

    # TOP 10 收藏最多的UP主
    stats['top_ups'] = [
        {"name": row['name'], "mid": row['up_mid'], "count": row['c']}
        for row in conn.execute("""
            SELECT u.name, v.up_mid, COUNT(*) as c
            FROM videos v
            JOIN ups u ON v.up_mid = u.mid
            GROUP BY v.up_mid
            ORDER BY c DESC
            LIMIT 10
        """).fetchall()
    ]

    # 按月收藏趋势（最近12个月）
    stats['monthly_trend'] = [
        {"month": row['m'], "count": row['c']}
        for row in conn.execute("""
            SELECT strftime('%Y-%m', fav_time) as m, COUNT(*) as c
            FROM video_collection
            WHERE fav_time IS NOT NULL
            GROUP BY m
            ORDER BY m DESC
            LIMIT 12
        """).fetchall()
    ]
    stats['monthly_trend'].reverse()

    # 最近失效的视频
    stats['recent_invalid'] = [
        {"title": row['title'], "bv_id": row['bv_id'],
         "up_name": row['up_name'], "collection": row['collection_name']}
        for row in conn.execute("""
            SELECT v.title, v.bv_id, u.name as up_name, c.name as collection_name
            FROM videos v
            JOIN ups u ON v.up_mid = u.mid
            JOIN video_collection vc ON v.bv_id = vc.bv_id
            JOIN collections c ON vc.collection_id = c.id
            WHERE v.is_invalid = 1
            ORDER BY vc.fav_time DESC
            LIMIT 20
        """).fetchall()
    ]

    # 最近取消收藏的视频
    stats['recent_unfav'] = [
        {"title": row['title'], "bv_id": row['bv_id'],
         "up_name": row['up_name'], "collection": row['collection_name'],
         "unfav_time": row['unfav_time']}
        for row in conn.execute("""
            SELECT v.title, v.bv_id, u.name as up_name, c.name as collection_name,
                   vc.unfav_time
            FROM video_collection vc
            JOIN videos v ON vc.bv_id = v.bv_id
            JOIN ups u ON v.up_mid = u.mid
            JOIN collections c ON vc.collection_id = c.id
            WHERE vc.is_active = 0 AND vc.unfav_time IS NOT NULL
            ORDER BY vc.unfav_time DESC
            LIMIT 20
        """).fetchall()
    ]

    # 视频时长分布
    stats['duration_distribution'] = {}
    for row in conn.execute("SELECT duration FROM videos WHERE duration IS NOT NULL").fetchall():
        dur = row['duration']
        try:
            parts = dur.split(':')
            total_seconds = int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
            if total_seconds < 60:
                bucket = '<1分钟'
            elif total_seconds < 300:
                bucket = '1-5分钟'
            elif total_seconds < 600:
                bucket = '5-10分钟'
            elif total_seconds < 1800:
                bucket = '10-30分钟'
            elif total_seconds < 3600:
                bucket = '30-60分钟'
            else:
                bucket = '>1小时'
            stats['duration_distribution'][bucket] = stats['duration_distribution'].get(bucket, 0) + 1
        except (ValueError, IndexError):
            pass

    # 爬取历史
    stats['crawl_history'] = [
        dict(row) for row in conn.execute("""
            SELECT * FROM crawl_history ORDER BY crawl_time DESC LIMIT 10
        """).fetchall()
    ]

    return stats


# --- CSV 导出 ---

def export_all_videos_csv(conn, output_path):
    """导出所有视频数据为 CSV"""
    import csv
    rows = conn.execute("""
        SELECT v.bv_id, v.title, v.duration, u.name as up_name, u.mid as up_mid,
               v.play_count, v.collect_count, v.danmaku_count,
               v.upload_time, v.publish_time, v.is_invalid,
               GROUP_CONCAT(c.name, '; ') as collections,
               MAX(vc.fav_time) as latest_fav_time
        FROM videos v
        JOIN ups u ON v.up_mid = u.mid
        LEFT JOIN video_collection vc ON v.bv_id = vc.bv_id AND vc.is_active = 1
        LEFT JOIN collections c ON vc.collection_id = c.id
        GROUP BY v.bv_id
        ORDER BY latest_fav_time DESC
    """).fetchall()

    with open(output_path, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        writer.writerow(['BV号', '标题', '时长', 'UP主', 'UP主ID',
                         '播放量', '收藏量', '弹幕数', '上传时间', '发布时间',
                         '是否失效', '所在收藏夹', '最新收藏时间'])
        for row in rows:
            writer.writerow([
                row['bv_id'], row['title'], row['duration'],
                row['up_name'], row['up_mid'],
                row['play_count'], row['collect_count'], row['danmaku_count'],
                row['upload_time'], row['publish_time'],
                '是' if row['is_invalid'] else '否',
                row['collections'] or '(已取消收藏)',
                row['latest_fav_time'] or ''
            ])
    logging.info(f"已导出 {len(rows)} 条视频数据到 {output_path}")
    return len(rows)


# --- 从旧 JSON 数据迁移 ---

def migrate_from_json(json_dir, db_path=None):
    """从旧的 JSON 文件格式迁移数据到 SQLite"""
    if db_path is None:
        db_path = get_db_path()

    init_db(db_path)
    logging.info(f"开始从 {json_dir} 迁移数据到 SQLite...")

    json_files = [f for f in os.listdir(json_dir)
                  if f.endswith('.json') and f != '关注UP列表.json']

    with get_connection(db_path) as conn:
        # 迁移收藏夹数据
        for file_name in json_files:
            collection_name = file_name.rsplit('.', 1)[0]
            file_path = os.path.join(json_dir, file_name)

            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            except (json.JSONDecodeError, FileNotFoundError) as e:
                logging.warning(f"读取 {file_name} 失败: {e}")
                continue

            # 创建一个临时的 collection id（用负的 hash 值）
            coll_id = abs(hash(collection_name)) % (10 ** 9)
            upsert_collection(conn, coll_id, collection_name, len(data))

            for video_id, video_data in data.items():
                try:
                    upsert_video(conn, video_data)
                    add_video_to_collection(
                        conn, video_data['BV'], coll_id,
                        video_data['三个时间']['收藏时间']
                    )
                    if video_data.get('是否取消了收藏'):
                        mark_unfavorited(conn, video_data['BV'], coll_id)
                except Exception as e:
                    logging.warning(f"迁移视频 {video_id} 失败: {e}")

            logging.info(f"已迁移收藏夹: {collection_name} ({len(data)} 条)")

        # 迁移关注UP列表
        following_path = os.path.join(json_dir, '关注UP列表.json')
        if os.path.exists(following_path):
            try:
                with open(following_path, 'r', encoding='utf-8') as f:
                    ups = json.load(f)
                save_following_ups(conn, ups)
                logging.info(f"已迁移关注UP主列表 ({len(ups)} 位)")
            except Exception as e:
                logging.warning(f"迁移关注UP列表失败: {e}")

    logging.info("数据迁移完成！")
