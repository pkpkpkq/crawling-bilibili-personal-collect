import os
import json
import logging
import html
import shutil

# --- Asset Contents ---

CSS_CONTENT = """
:root {
    --bg-color: #1a1a1a;
    --card-bg: #2c2c2c;
    --text-color: #e0e0e0;
    --link-color: #4a90e2;
    --border-color: #444;
    --header-bg: #222;
    --input-bg: #333;
    --input-border: #555;
    --button-bg: #4a90e2;
    --button-hover-bg: #5aA0f2;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    background-color: var(--bg-color);
    color: var(--text-color);
    margin: 0;
    padding: 20px;
}

.container {
    max-width: 1200px;
    margin: 0 auto;
}

h1, h2 {
    color: var(--text-color);
    border-bottom: 2px solid var(--link-color);
    padding-bottom: 10px;
}

a {
    color: var(--link-color);
    text-decoration: none;
}

a:hover {
    text-decoration: underline;
}

/* Index Page Styles */
.folder-list {
    list-style: none;
    padding: 0;
}

.folder-list li {
    background-color: var(--card-bg);
    margin-bottom: 10px;
    border-radius: 8px;
    transition: transform 0.2s;
}

.folder-list li:hover {
    transform: translateY(-3px);
    box-shadow: 0 4px 10px rgba(0,0,0,0.3);
}

.folder-list a {
    display: block;
    padding: 20px;
    font-size: 1.2em;
    font-weight: bold;
}

/* Folder Page Styles */
.controls {
    background-color: var(--card-bg);
    padding: 20px;
    border-radius: 8px;
    margin-bottom: 20px;
    display: flex;
    flex-wrap: wrap;
    gap: 15px;
    align-items: center;
}

.controls .search-box {
    flex-grow: 1;
    min-width: 250px;
}

.controls input[type="text"],
.controls input[type="date"] {
    width: 100%;
    padding: 10px;
    border-radius: 5px;
    border: 1px solid var(--input-border);
    background-color: var(--input-bg);
    color: var(--text-color);
    font-size: 1em;
}

.controls label {
    margin-right: 5px;
}

.video-list {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
    gap: 20px;
}

.video-card {
    background-color: var(--card-bg);
    border: 1px solid var(--border-color);
    border-radius: 8px;
    overflow: hidden;
    display: flex;
    flex-direction: column;
    transition: transform 0.2s, box-shadow 0.2s;
}

.video-card.hidden {
    display: none;
}

.video-card:hover {
    transform: translateY(-5px);
    box-shadow: 0 6px 15px rgba(0,0,0,0.4);
}

.video-card .cover {
    width: 100%;
    aspect-ratio: 16 / 9;
    object-fit: cover;
}

.video-card .info {
    padding: 15px;
    display: flex;
    flex-direction: column;
    flex-grow: 1;
}

.video-card .title {
    font-size: 1.1em;
    font-weight: bold;
    margin: 0 0 10px 0;
    color: var(--text-color);
}

.video-card .meta {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 15px;
}

.video-card .meta .up-face {
    width: 40px;
    height: 40px;
    border-radius: 50%;
}

.video-card .meta .up-name {
    font-size: 0.9em;
    font-weight: bold;
}

.video-card .stats, .video-card .timestamps {
    font-size: 0.8em;
    color: #b0b0b0;
    margin-top: auto;
}
.video-card .stats p, .video-card .timestamps p {
    margin: 4px 0;
}

.video-card .bv-id {
    font-family: monospace;
    background-color: var(--input-bg);
    padding: 2px 5px;
    border-radius: 4px;
    font-size: 0.9em;
}

#back-to-top {
    position: fixed;
    bottom: 20px;
    right: 20px;
    background-color: var(--button-bg);
    color: white;
    border: none;
    border-radius: 50%;
    width: 50px;
    height: 50px;
    font-size: 24px;
    cursor: pointer;
    display: none;
    transition: background-color 0.3s, opacity 0.3s;
    opacity: 0.7;
}

#back-to-top:hover {
    background-color: var(--button-hover-bg);
    opacity: 1;
}
"""

JS_CONTENT = """
document.addEventListener('DOMContentLoaded', () => {
    const searchInput = document.getElementById('searchInput');
    const favDateStart = document.getElementById('favDateStart');
    const favDateEnd = document.getElementById('favDateEnd');
    const pubDateStart = document.getElementById('pubDateStart');
    const pubDateEnd = document.getElementById('pubDateEnd');
    const videoCards = document.querySelectorAll('.video-card');
    const backToTopButton = document.getElementById('back-to-top');

    function filterVideos() {
        const searchText = searchInput.value.toLowerCase();
        const favStart = favDateStart.value ? new Date(favDateStart.value) : null;
        const favEnd = favDateEnd.value ? new Date(favDateEnd.value) : null;
        const pubStart = pubDateStart.value ? new Date(pubDateStart.value) : null;
        const pubEnd = pubDateEnd.value ? new Date(pubDateEnd.value) : null;

        videoCards.forEach(card => {
            const title = card.dataset.title.toLowerCase();
            const bv = card.dataset.bv.toLowerCase();
            const favTime = new Date(card.dataset.favtime);
            const pubTime = new Date(card.dataset.pubtime);

            const matchesSearch = title.includes(searchText) || bv.includes(searchText);
            
            const matchesFavDate = (!favStart || favTime >= favStart) && (!favEnd || favTime <= favEnd);

            const matchesPubDate = (!pubStart || pubTime >= pubStart) && (!pubEnd || pubTime <= pubEnd);

            if (matchesSearch && matchesFavDate && matchesPubDate) {
                card.classList.remove('hidden');
            } else {
                card.classList.add('hidden');
            }
        });
    }

    if (searchInput) {
        searchInput.addEventListener('keyup', filterVideos);
        favDateStart.addEventListener('change', filterVideos);
        favDateEnd.addEventListener('change', filterVideos);
        pubDateStart.addEventListener('change', filterVideos);
        pubDateEnd.addEventListener('change', filterVideos);
    }
    
    // Back to top button logic
    if (backToTopButton) {
        window.onscroll = () => {
            if (document.body.scrollTop > 100 || document.documentElement.scrollTop > 100) {
                backToTopButton.style.display = "block";
            } else {
                backToTopButton.style.display = "none";
            }
        };

        backToTopButton.onclick = () => {
            document.body.scrollTop = 0; // For Safari
            document.documentElement.scrollTop = 0; // For Chrome, Firefox, IE and Opera
        };
    }
});
"""

# --- HTML Templates ---

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <link rel="stylesheet" href="{css_path}">
</head>
<body>
    <div class="container">
        <h1>{header}</h1>
        {body}
    </div>
    <script src="{js_path}"></script>
</body>
</html>
"""

FOLDER_PAGE_BODY_TEMPLATE = """
<a href="../index.html">&larr; 返回收藏夹列表</a>
<div class="controls">
    <div class="search-box">
        <label for="searchInput">搜索:</label>
        <input type="text" id="searchInput" placeholder="标题或BV号...">
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
</div>
<div class="video-list">
    {video_cards}
</div>
<button id="back-to-top" title="返回顶部">&uarr;</button>
"""

VIDEO_CARD_TEMPLATE = """
<div class="video-card" 
     data-title="{title}" 
     data-bv="{bv}" 
     data-favtime="{fav_time_iso}" 
     data-pubtime="{pub_time_iso}">
    <a href="https://www.bilibili.com/video/{bv}" target="_blank">
        <img src="{cover_path}" alt="{title}" class="cover" loading="lazy" onerror="this.onerror=null;this.src='data:image/svg+xml,%3Csvg xmlns=\'http://www.w3.org/2000/svg\' viewBox=\'0 0 16 9\'%3E%3Crect width=\'16\' height=\'9\' fill=\'%23333\'/%3E%3C/svg%3E';">
    </a>
    <div class="info">
        <h3 class="title">
            <a href="https://www.bilibili.com/video/{bv}" target="_blank">{title}</a>
        </h3>
        <div class="meta">
            <a href="https://space.bilibili.com/{up_id}" target="_blank">
                <img src="{up_face_path}" alt="{up_name}" class="up-face" loading="lazy" onerror="this.onerror=null;this.src='data:image/svg+xml,%3Csvg xmlns=\'http://www.w3.org/2000/svg\' viewBox=\'0 0 1 1\'%3E%3Crect width=\'1\' height=\'1\' fill=\'%23555\'/%3E%3C/svg%3E';">
            </a>
            <a href="https://space.bilibili.com/{up_id}" target="_blank">
                <span class="up-name">{up_name}</span>
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

# --- Main view function ---

def view(RPath, report_dir_name):
    """
    Generates a self-contained HTML report.
    RPath: Path to the '收藏夹信息' directory.
    report_dir_name: Name of the directory to store the report assets (e.g., 'html_report').
    """
    logging.info("Starting HTML report generation with self-creating assets...")

    # Define paths
    project_root = '.'
    report_path = os.path.join(project_root, report_dir_name)
    assets_path = os.path.join(report_path, 'assets')
    
    # --- Create report structure and asset files ---
    os.makedirs(assets_path, exist_ok=True)

    css_file_path = os.path.join(assets_path, 'style.css')
    js_file_path = os.path.join(assets_path, 'main.js')

    if not os.path.exists(css_file_path):
        logging.info("Generating CSS file...")
        with open(css_file_path, 'w', encoding='utf-8') as f:
            f.write(CSS_CONTENT)

    if not os.path.exists(js_file_path):
        logging.info("Generating JavaScript file...")
        with open(js_file_path, 'w', encoding='utf-8') as f:
            f.write(JS_CONTENT)

    try:
        favorite_files = [f for f in os.listdir(RPath) if f.endswith('.json')]
        logging.info(f"Found favorite folders: {[f.split('.')[0] for f in favorite_files]}")
    except FileNotFoundError:
        logging.error(f"Source directory for JSON data not found: {RPath}")
        return

    # --- Generate index.html in the project root ---
    index_links = []
    for fav_file in sorted(favorite_files):
        folder_name = fav_file.split('.')[0]
        safe_folder_name = html.escape(folder_name)
        page_file_name = f"fav-{safe_folder_name}.html"
        link = f'<li><a href="{os.path.join(report_dir_name, page_file_name).replace("\\", "/")}">{safe_folder_name}</a></li>'
        index_links.append(link)

    index_body = f'<ul class="folder-list">{"".join(index_links)}</ul>'
    index_html = HTML_TEMPLATE.format(
        title="Bilibili 收藏夹报告",
        header="收藏夹列表",
        body=index_body,
        css_path=os.path.join(report_dir_name, 'assets/style.css').replace('\\', '/'),
        js_path=os.path.join(report_dir_name, 'assets/main.js').replace('\\', '/')
    )

    with open(os.path.join(project_root, 'index.html'), 'w', encoding='utf-8') as f:
        f.write(index_html)
    logging.info("Generated index.html in project root.")

    # --- Generate individual folder pages inside the report directory ---
    for fav_file in favorite_files:
        folder_name = fav_file.split('.')[0]
        safe_folder_name = html.escape(folder_name)
        page_file_name = f"fav-{safe_folder_name}.html"
        
        try:
            with open(os.path.join(RPath, fav_file), 'r', encoding='utf-8') as f:
                data = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError) as e:
            logging.error(f"Could not read or parse {fav_file}: {e}")
            continue

        video_cards = []
        sorted_videos = sorted(data.values(), key=lambda x: x['三个时间']['收藏时间'], reverse=True)

        for video in sorted_videos:
            # Paths are now relative to the project root, for the check
            cover_path_check = os.path.join('html_report', '视频封面', folder_name, f"{video['BV']}.jpg")
            up_face_path_check = os.path.join('html_report', 'up头像', f"{video['up主']['ID']}.jpg")

            # Paths for the HTML src attribute are relative to the HTML file's location
            cover_path_src = os.path.join('视频封面', folder_name, f"{video['BV']}.jpg").replace('\\', '/')
            up_face_path_src = os.path.join('up头像', f"{video['up主']['ID']}.jpg").replace('\\', '/')

            card_html = VIDEO_CARD_TEMPLATE.format(
                title=html.escape(video['视频信息']['标题']),
                bv=html.escape(video['BV']),
                cover_path=cover_path_src,
                up_face_path=up_face_path_src,
                up_name=html.escape(video['up主']['昵称']),
                up_id=video['up主']['ID'],
                play=video['观众数据']['播放量'],
                collect=video['观众数据']['收藏量'],
                danmaku=video['观众数据']['弹幕数量'],
                duration=video['视频信息']['时长'],
                fav_time=video['三个时间']['收藏时间'],
                pub_time=video['三个时间']['发布时间'],
                fav_time_iso=video['三个时间']['收藏时间'].replace(' ', 'T'),
                pub_time_iso=video['三个时间']['发布时间'].replace(' ', 'T')
            )
            video_cards.append(card_html)

        folder_body = FOLDER_PAGE_BODY_TEMPLATE.format(video_cards="".join(video_cards))
        folder_html = HTML_TEMPLATE.format(
            title=f"收藏夹: {safe_folder_name}",
            header=f"收藏夹: {safe_folder_name}",
            body=folder_body,
            css_path="assets/style.css",
            js_path="assets/main.js"
        )
        
        with open(os.path.join(report_path, page_file_name), 'w', encoding='utf-8') as f:
            f.write(folder_html)
        logging.info(f"Generated page: {page_file_name} inside {report_dir_name}")

    logging.info("HTML report generation complete.")
    logging.info(f"You can now open the main report file: {os.path.abspath(os.path.join(project_root, 'index.html'))}")