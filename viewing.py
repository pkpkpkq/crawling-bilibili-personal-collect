import os
import json
import logging
import html
from database import (
    get_connection,
    get_all_collections,
    get_videos_in_collection,
    get_video_history,
    get_all_videos_index,
    get_all_following_ups,
    get_stats,
)

# --- Asset Contents ---
# CSS and JS are stored in templates/ directory for maintainability.

_TEMPLATE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")


def _read_template(filename):
    with open(os.path.join(_TEMPLATE_DIR, filename), "r", encoding="utf-8") as f:
        return f.read()


# --- HTML Templates ---

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <link rel="stylesheet" href="{css_path}">
    {extra_head}
</head>
<body id="page-{page_id}">
    <div class="container">
        <h1>{header}</h1>
        {body}
    </div>
    <button id="back-to-top" title="返回顶部">&uarr;</button>
    <script src="{js_path}"></script>
</body>
</html>
"""

INDEX_BODY_TEMPLATE = """
<div class="page-controls">
    <div class="search-box">
        <label for="globalSearchInput">全局搜索:</label>
        <input type="text" id="globalSearchInput" placeholder="在所有收藏的视频中搜索标题、BV号、UP主...">
    </div>
</div>
<div id="global-search-results" class="video-list" style="display: none;"></div>
<div id="index-list">
    {dashboard_html}
    <h2>收藏夹列表</h2>
    <ul class="folder-list">{folder_links}</ul>
    <h2>工具</h2>
    <ul class="folder-list">
        <li><a href="{up_list_path}">查看已关注的UP主列表</a></li>
    </ul>
</div>
<script id="dashboard-stats" type="application/json">{stats_json}</script>
"""

FOLDER_PAGE_BODY_TEMPLATE = """
<a href="../index.html">&larr; 返回首页</a>
<div class="controls">
    <div class="search-box">
        <label for="searchInput">搜索:</label>
        <input type="text" id="searchInput" placeholder="标题、BV号、UP主...">
    </div>
    <div>
        <label for="favDateStart">收藏时间:</label>
        <input type="date" id="favDateStart">
        <span>-</span>
        <input type="date" id="favDateEnd">
    </div>
    <div>
        <label for="pubDateStart">发布时间:</label>
        <input type="date" id="pubDateStart">
        <span>-</span>
        <input type="date" id="pubDateEnd">
    </div>
    <div>
        <label><input type="checkbox" id="showCurrentOnly"> 仅显示当前</label>
    </div>
    <div>
        <label for="sortSelect">排序:</label>
        <select id="sortSelect">
            <option value="fav_desc">收藏时间 ↓</option>
            <option value="fav_asc">收藏时间 ↑</option>
            <option value="pub_desc">发布时间 ↓</option>
            <option value="pub_asc">发布时间 ↑</option>
            <option value="play_desc">播放量 ↓</option>
            <option value="collect_desc">收藏量 ↓</option>
            <option value="danmaku_desc">弹幕数 ↓</option>
            <option value="duration_desc">时长 ↓</option>
        </select>
    </div>
    <button class="export-btn" id="exportCsvBtn">导出 CSV</button>
</div>
<div class="video-list">
    {video_cards}
</div>
"""

VIDEO_CARD_TEMPLATE = """
<div class="video-card {status_class}"
     data-title="{title_attr}"
     data-bv="{bv}"
     data-up="{up_name_attr}"
     data-favtime="{fav_time_iso}"
     data-pubtime="{pub_time_iso}"
     data-play="{play}"
     data-collect="{collect}"
     data-danmaku="{danmaku}"
     data-duration="{duration}"
     data-history='{history_json}'>
    <a class="cover-link" href="https://www.bilibili.com/video/{bv}" target="_blank">
        <img src="{cover_path}" alt="{title_attr}" class="cover" loading="lazy">
    </a>
    <div class="info">
        <h3 class="title">
            <a href="https://www.bilibili.com/video/{bv}" target="_blank">{title_html}</a>
        </h3>
        <div class="meta">
            <a href="https://space.bilibili.com/{up_id}" target="_blank">
                <img src="{up_face_path}" alt="{up_name_attr}" class="up-face" loading="lazy">
            </a>
            <a href="https://space.bilibili.com/{up_id}" target="_blank">
                <span class="up-name">{up_name_html}</span>
            </a>
        </div>
        <div class="stats">
            <p>播放: {play} | 收藏: {collect} | 弹幕: {danmaku}</p>
            <p>时长: {duration}</p>
        </div>
        <div class="timestamps">
            <p>收藏于: {fav_time}</p>
            <p>发布于: {pub_time}</p>
            <p class="bv-id">{bv}</p>
        </div>
    </div>
</div>
"""

UP_LIST_PAGE_BODY_TEMPLATE = """
<a href="../index.html">&larr; 返回首页</a>
<div class="controls">
    <div class="search-box">
        <label for="upSearchInput">搜索UP主:</label>
        <input type="text" id="upSearchInput" placeholder="输入UP主昵称...">
    </div>
</div>
<ul class="up-list">
    {up_list_items}
</ul>
"""


# --- Dashboard HTML Generation ---


def generate_dashboard_html(stats):
    """生成仪表盘 HTML"""
    if not stats:
        return ""

    html_parts = ["<h2>数据总览</h2>"]

    # Stat cards
    html_parts.append('<div class="dashboard">')
    cards = [
        ("green", stats.get("total_videos", 0), "总视频数"),
        ("blue", stats.get("total_collections", 0), "收藏夹数"),
        ("purple", stats.get("total_ups", 0), "收藏 UP 主数"),
        ("orange", stats.get("following_ups", 0), "关注 UP 主数"),
        ("red", stats.get("invalid_videos", 0), "失效视频数"),
    ]
    for color, number, label in cards:
        html_parts.append(
            f'<div class="stat-card {color}"><div class="stat-number">{number}</div><div class="stat-label">{label}</div></div>'
        )
    html_parts.append("</div>")

    # Charts
    html_parts.append('<div class="charts-grid">')
    html_parts.append(
        '<div class="chart-container"><h3>📊 各收藏夹视频数量</h3><canvas id="chart-collections"></canvas></div>'
    )
    html_parts.append(
        '<div class="chart-container"><h3>📈 按月收藏趋势</h3><canvas id="chart-trend"></canvas></div>'
    )
    html_parts.append(
        '<div class="chart-container"><h3>🏆 TOP 10 收藏最多的 UP 主</h3><canvas id="chart-top-ups"></canvas></div>'
    )
    html_parts.append(
        '<div class="chart-container"><h3>🎯 视频时长分布</h3><canvas id="chart-duration"></canvas></div>'
    )
    html_parts.append("</div>")

    # Recent invalid videos
    if stats.get("recent_invalid"):
        html_parts.append(
            '<div class="recent-list"><h3>⚠️ 最近失效的视频</h3><table><tr><th>标题</th><th>UP主</th><th>收藏夹</th><th>BV号</th></tr>'
        )
        for v in stats["recent_invalid"][:10]:
            html_parts.append(
                f'<tr><td>{html_escape(v["title"])}</td><td>{html_escape(v["up_name"])}</td><td>{html_escape(v["collection"])}</td><td><a href="https://www.bilibili.com/video/{v["bv_id"]}" target="_blank">{v["bv_id"]}</a></td></tr>'
            )
        html_parts.append("</table></div>")

    # Recent unfavorited videos
    if stats.get("recent_unfav"):
        html_parts.append(
            '<div class="recent-list"><h3>📤 最近取消收藏的视频</h3><table><tr><th>标题</th><th>UP主</th><th>收藏夹</th><th>取消时间</th></tr>'
        )
        for v in stats["recent_unfav"][:10]:
            html_parts.append(
                f"<tr><td>{html_escape(v['title'])}</td><td>{html_escape(v['up_name'])}</td><td>{html_escape(v['collection'])}</td><td>{v['unfav_time']}</td></tr>"
            )
        html_parts.append("</table></div>")

    return "\n".join(html_parts)


def html_escape(text):
    """安全的 HTML 转义"""
    if text is None:
        return ""
    return html.escape(str(text))


# --- Main View Generation Function ---


def view(db_path, report_dir_name):
    logging.info("---Starting HTML Report Generation---")

    project_root = "."
    report_path = os.path.join(project_root, report_dir_name)
    assets_path = os.path.join(report_path, "assets")
    os.makedirs(assets_path, exist_ok=True)

    try:
        with open(os.path.join(assets_path, "style.css"), "w", encoding="utf-8") as f:
            f.write(_read_template("style.css"))
        with open(os.path.join(assets_path, "main.js"), "w", encoding="utf-8") as f:
            f.write(_read_template("main.js"))
        logging.info("Asset files written.")
    except Exception as e:
        logging.error(f"Failed to write asset files: {e}")
        return

    with get_connection(db_path) as conn:
        # Build and save video index for global search
        video_index = get_all_videos_index(conn)
        index_path = os.path.join(report_path, "视频索引.json")
        with open(index_path, "w", encoding="utf-8") as f:
            json.dump(video_index, f, ensure_ascii=False)
        logging.info(f"Video index saved ({len(video_index)} videos)")

        # Get data
        collections = get_all_collections(conn)
        following_ups = get_all_following_ups(conn)
        stats = get_stats(conn)

        # --- Generate UP List Page ---
        up_list_items = []
        for up in following_ups:
            up_face_path = f"up头像/{up['mid']}.jpg"
            up_list_items.append(f'''<li class="up-list-item" data-up-name="{html_escape(up["name"])}">
                    <div class="up-link">
                        <img src="{up_face_path}" alt="{html_escape(up["name"])}">
                        <a class="up-name-link" href="https://space.bilibili.com/{up["mid"]}" target="_blank">{html_escape(up["name"])}</a>
                    </div>
                </li>''')

        up_list_page_html = HTML_TEMPLATE.format(
            title="关注的UP主列表",
            header="关注的UP主列表",
            body=UP_LIST_PAGE_BODY_TEMPLATE.format(
                up_list_items="".join(up_list_items)
            ),
            css_path="assets/style.css",
            js_path="assets/main.js",
            page_id="up-list",
            extra_head="",
        )
        with open(
            os.path.join(report_path, "关注UP列表.html"), "w", encoding="utf-8"
        ) as f:
            f.write(up_list_page_html)

        # --- Generate Index Page ---
        folder_links = []
        for coll in collections:
            page_file_name = f"fav-{coll['id']}.html"
            link_path = os.path.join(report_dir_name, page_file_name).replace("\\", "/")
            folder_links.append(
                f'<li><a href="{link_path}">{html_escape(coll["name"])}</a></li>'
            )

        dashboard_html = generate_dashboard_html(stats)
        stats_json = json.dumps(stats, ensure_ascii=False)

        index_body = INDEX_BODY_TEMPLATE.format(
            folder_links="".join(folder_links),
            up_list_path=os.path.join(report_dir_name, "关注UP列表.html").replace(
                "\\", "/"
            ),
            dashboard_html=dashboard_html,
            stats_json=stats_json,
        )
        chart_js_cdn = '<script src="https://cdn.jsdelivr.net/npm/chart.js@4"></script>'
        index_html = HTML_TEMPLATE.format(
            title="Bilibili 收藏夹报告",
            header="Bilibili 收藏夹报告",
            body=index_body,
            css_path=os.path.join(report_dir_name, "assets/style.css").replace(
                "\\", "/"
            ),
            js_path=os.path.join(report_dir_name, "assets/main.js").replace("\\", "/"),
            page_id="index",
            extra_head=chart_js_cdn,
        )
        with open(os.path.join(project_root, "index.html"), "w", encoding="utf-8") as f:
            f.write(index_html)
        logging.info("Generated index.html")

        # --- Generate Individual Folder Pages ---
        for coll in collections:
            coll_id = coll["id"]
            coll_name = coll["name"]

            videos = get_videos_in_collection(conn, coll_id, include_unfav=True)

            video_cards = []
            for video in videos:
                bvid = video["bv_id"]
                video_history = get_video_history(conn, bvid)

                # Check latest collection
                latest_coll_row = conn.execute(
                    """
                    SELECT c.name FROM video_collection vc
                    JOIN collections c ON vc.collection_id = c.id
                    WHERE vc.bv_id = ? AND vc.is_active = 1
                    ORDER BY vc.fav_time DESC LIMIT 1
                """,
                    (bvid,),
                ).fetchone()
                latest_collection = (
                    latest_coll_row["name"] if latest_coll_row else coll_name
                )

                status_class = ""
                if video["is_invalid"]:
                    status_class = "invalid"
                elif not video["is_active"] or latest_collection != coll_name:
                    status_class = "moved"

                fav_time = video["fav_time"] or ""
                pub_time = video["publish_time"] or ""

                card_html = VIDEO_CARD_TEMPLATE.format(
                    title_attr=html_escape(video["title"]),
                    title_html=html_escape(video["title"]),
                    bv=html_escape(bvid),
                    cover_path=f"视频封面/{bvid}.jpg",
                    up_face_path=f"up头像/{video['up_mid']}.jpg",
                    up_name_attr=html_escape(video["up_name"]),
                    up_name_html=html_escape(video["up_name"]),
                    up_id=video["up_mid"],
                    play=video["play_count"],
                    collect=video["collect_count"],
                    danmaku=video["danmaku_count"],
                    duration=video["duration"] or "",
                    fav_time=fav_time,
                    pub_time=pub_time,
                    fav_time_iso=fav_time.replace(" ", "T") if fav_time else "",
                    pub_time_iso=pub_time.replace(" ", "T") if pub_time else "",
                    history_json=html_escape(
                        json.dumps(video_history, ensure_ascii=False)
                    ),
                    status_class=status_class,
                )
                video_cards.append(card_html)

            folder_body = FOLDER_PAGE_BODY_TEMPLATE.format(
                video_cards="".join(video_cards)
            )
            folder_html = HTML_TEMPLATE.format(
                title=f"收藏夹: {html_escape(coll_name)}",
                header=f"收藏夹: {html_escape(coll_name)}",
                body=folder_body,
                css_path="assets/style.css",
                js_path="assets/main.js",
                page_id="folder",
                extra_head="",
            )
            with open(
                os.path.join(report_path, f"fav-{coll_id}.html"),
                "w",
                encoding="utf-8",
            ) as f:
                f.write(folder_html)
            logging.info(f"Generated page for {coll_name}")

    logging.info("---HTML Report Generation Finished---")
