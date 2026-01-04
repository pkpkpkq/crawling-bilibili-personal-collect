import os
import json
import logging
import html
import shutil
from collections import defaultdict

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
    --invalid-bg: rgba(255, 82, 82, 0.1);
}

body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    background-color: var(--bg-color);
    color: var(--text-color);
    margin: 0;
    padding: 20px;
}

.container {
    max-width: 1600px;
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

/* Index & Shared Page Styles */
.page-controls, .controls {
    background-color: var(--card-bg);
    padding: 20px;
    border-radius: 8px;
    margin-bottom: 20px;
    display: flex;
    flex-wrap: wrap;
    gap: 15px;
    align-items: center;
}

.page-controls .search-box, .controls .search-box {
    flex-grow: 1;
    min-width: 250px;
}

.page-controls input[type="text"], .controls input[type="text"],
.controls input[type="date"] {
    width: 100%;
    padding: 10px;
    border-radius: 5px;
    border: 1px solid var(--input-border);
    background-color: var(--input-bg);
    color: var(--text-color);
    font-size: 1em;
    box-sizing: border-box;
}

.controls label {
    margin-right: 5px;
}

.folder-list, .up-list {
    list-style: none;
    padding: 0;
    display: grid;
    gap: 15px;
}

.folder-list {
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
}

.folder-list li, .up-list-item {
    background-color: var(--card-bg);
    border-radius: 8px;
    transition: transform 0.2s, box-shadow 0.2s;
}

.folder-list li:hover, .up-list-item:hover {
    transform: translateY(-3px);
    box-shadow: 0 4px 10px rgba(0,0,0,0.3);
}

.folder-list a, .up-list-item a {
    display: block;
    padding: 20px;
    font-size: 1.2em;
    font-weight: bold;
}

.up-list {
     grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
}

.up-list-item a {
    display: flex;
    align-items: center;
    gap: 15px;
    padding: 15px;
    font-size: 1em;
}

.up-list-item img {
    width: 50px;
    height: 50px;
    border-radius: 50%;
}


/* Video List Styles */
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
    cursor: pointer;
}

.video-card.invalid {
    background-color: var(--invalid-bg);
}

.video-card.hidden {
    display: none;
}

.video-card:hover {
    transform: translateY(-5px);
    box-shadow: 0 6px 15px rgba(0,0,0,0.4);
}

.video-card .cover-link {
    display: block;
    position: relative;
}

.video-card .cover {
    width: 100%;
    aspect-ratio: 16 / 9;
    object-fit: cover;
    display: block;
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

/* Modal Styles */
.modal-overlay {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0,0,0,0.7);
    display: none;
    align-items: center;
    justify-content: center;
    z-index: 1000;
}
.modal-content {
    background: var(--card-bg);
    padding: 30px;
    border-radius: 8px;
    max-width: 600px;
    width: 90%;
    box-shadow: 0 10px 30px rgba(0,0,0,0.5);
    border-top: 3px solid var(--link-color);
}
.modal-content h2 {
    margin-top: 0;
}
.modal-history-list {
    list-style: none;
    padding: 0;
}
.modal-history-list li {
    padding: 10px 0;
    border-bottom: 1px solid var(--border-color);
}
.modal-history-list li:last-child {
    border-bottom: none;
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
    z-index: 999;
}

#back-to-top:hover {
    background-color: var(--button-hover-bg);
    opacity: 1;
}
"""

JS_CONTENT = """
document.addEventListener('DOMContentLoaded', () => {
    // --- Universal Elements & Logic ---
    const backToTopButton = document.getElementById('back-to-top');
    const videoList = document.querySelector('.video-list');

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
            document.body.scrollTop = 0; // Safari
            document.documentElement.scrollTop = 0; // Chrome, Firefox, IE, Opera
        };
    }

    // Modal logic for video history
    const modalOverlay = document.getElementById('modal-overlay');
    if (modalOverlay && (videoList || document.getElementById('global-search-results'))) {
        const container = videoList || document.getElementById('global-search-results');
        container.addEventListener('click', (e) => {
            const card = e.target.closest('.video-card');
            if (card && card.dataset.history) {
                 // Prevent modal from opening if user clicks a link
                if (e.target.tagName === 'A' || e.target.closest('a')) {
                    return;
                }
                
                const history = JSON.parse(card.dataset.history);
                const modalList = document.getElementById('modal-history-list');
                const modalTitle = document.getElementById('modal-title');
                
                modalTitle.textContent = card.dataset.title;
                modalList.innerHTML = ''; // Clear previous history
                
                history.sort((a,b) => new Date(b.fav_time) - new Date(a.fav_time));

                history.forEach(item => {
                    const li = document.createElement('li');
                    li.textContent = `于 ${item.fav_time} 收藏于《${item.collection}》`;
                    modalList.appendChild(li);
                });
                modalOverlay.style.display = 'flex';
            }
        });

        modalOverlay.addEventListener('click', (e) => {
            if (e.target === modalOverlay) {
                modalOverlay.style.display = 'none';
            }
        });
    }

    // --- Page Specific Logic ---
    const pageId = document.body.id;

    if (pageId === 'page-index') {
        handleGlobalSearch();
    } else if (pageId === 'page-folder') {
        handleFolderSearch();
    } else if (pageId === 'page-up-list') {
        handleUpListSearch();
    }
});

function handleFolderSearch() {
    const searchInput = document.getElementById('searchInput');
    const favDateStart = document.getElementById('favDateStart');
    const favDateEnd = document.getElementById('favDateEnd');
    const pubDateStart = document.getElementById('pubDateStart');
    const pubDateEnd = document.getElementById('pubDateEnd');
    const videoCards = document.querySelectorAll('.video-card');

    function filter() {
        const searchText = searchInput.value.toLowerCase();
        const favStart = favDateStart.value ? new Date(favDateStart.value) : null;
        const favEnd = favDateEnd.value ? new Date(favDateEnd.value) : null;
        const pubStart = pubDateStart.value ? new Date(pubDateStart.value) : null;
        const pubEnd = pubDateEnd.value ? new Date(pubDateEnd.value) : null;

        videoCards.forEach(card => {
            const title = card.dataset.title.toLowerCase();
            const bv = card.dataset.bv.toLowerCase();
            const upName = card.dataset.up.toLowerCase();
            const favTime = new Date(card.dataset.favtime);
            const pubTime = new Date(card.dataset.pubtime);

            const matchesSearch = title.includes(searchText) || bv.includes(searchText) || upName.includes(searchText);
            const matchesFavDate = (!favStart || favTime >= favStart) && (!favEnd || favTime <= favEnd);
            const matchesPubDate = (!pubStart || pubTime >= pubStart) && (!pubEnd || pubTime <= pubEnd);

            if (matchesSearch && matchesFavDate && matchesPubDate) {
                card.classList.remove('hidden');
            } else {
                card.classList.add('hidden');
            }
        });
    }

    searchInput.addEventListener('keyup', filter);
    [favDateStart, favDateEnd, pubDateStart, pubDateEnd].forEach(el => el.addEventListener('change', filter));
}

function handleGlobalSearch() {
    const searchInput = document.getElementById('globalSearchInput');
    const resultsContainer = document.getElementById('global-search-results');
    const indexList = document.getElementById('index-list');
    let videoIndex = null;

    async function loadIndexAndSearch() {
        // Fetch index only once
        if (!videoIndex) {
            try {
                const response = await fetch('html_report/视频索引.json');
                if (!response.ok) throw new Error('Network response was not ok.');
                videoIndex = await response.json();
            } catch (error) {
                console.error("Failed to load video index:", error);
                resultsContainer.innerHTML = '<p>无法加载视频索引，搜索功能不可用。</p>';
                resultsContainer.style.display = 'block';
                indexList.style.display = 'none';
                return;
            }
        }
        search();
    }

    function search() {
        const query = searchInput.value.toLowerCase();
        if (query.length < 1) { // Show full list if search is cleared
            resultsContainer.style.display = 'none';
            indexList.style.display = 'block';
            return;
        }

        const results = Object.values(videoIndex).filter(video => {
            return video.info.title.toLowerCase().includes(query) ||
                   video.bvid.toLowerCase().includes(query) ||
                   video.info.up_name.toLowerCase().includes(query);
        });
        
        results.sort((a,b) => new Date(b.latest_fav_time) - new Date(a.latest_fav_time));

        indexList.style.display = 'none';
        resultsContainer.style.display = 'grid';
        resultsContainer.innerHTML = '';

        if (results.length === 0) {
            resultsContainer.innerHTML = '<p>没有找到匹配的视频。</p>';
            return;
        }

        results.forEach(video => {
            const card = document.createElement('div');
            card.className = 'video-card';
            if (video.info.is_invalid) {
                card.classList.add('invalid');
            }
            card.dataset.history = JSON.stringify(video.history);
            card.dataset.title = video.info.title;

            const coverPath = 'html_report/' + video.info.cover_path;
            const upFacePath = 'html_report/' + video.info.up_face_path;

            card.innerHTML = `
                <a class="cover-link" href="https://www.bilibili.com/video/${video.bvid}" target="_blank">
                    <img src="${coverPath}" alt="${video.info.title}" class="cover" loading="lazy">
                </a>
                <div class="info">
                    <h3 class="title">
                        <a href="https://www.bilibili.com/video/${video.bvid}" target="_blank">${video.info.title}</a>
                    </h3>
                    <div class="meta">
                         <a href="https://space.bilibili.com/${video.info.up_id}" target="_blank">
                            <img src="${upFacePath}" alt="${video.info.up_name}" class="up-face" loading="lazy">
                        </a>
                        <a href="https://space.bilibili.com/${video.info.up_id}" target="_blank">
                            <span class="up-name">${video.info.up_name}</span>
                        </a>
                    </div>
                    <div class="timestamps">
                        <p>最新收藏于: ${video.latest_fav_time}</p>
                        <p>位于: 《${video.latest_collection}》</p>
                        <p class="bv-id">${video.bvid}</p>
                    </div>
                </div>
            `;
            resultsContainer.appendChild(card);
        });
    }

    searchInput.addEventListener('keyup', loadIndexAndSearch);
}

function handleUpListSearch() {
    const searchInput = document.getElementById('upSearchInput');
    const upItems = document.querySelectorAll('.up-list-item');

    searchInput.addEventListener('keyup', () => {
        const query = searchInput.value.toLowerCase();
        upItems.forEach(item => {
            const upName = item.dataset.upName.toLowerCase();
            if (upName.includes(query)) {
                item.classList.remove('hidden');
            } else {
                item.classList.add('hidden');
            }
        });
    });
}
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
<body id="page-{page_id}">
    <div class="container">
        <h1>{header}</h1>
        {body}
    </div>
    <div id="modal-overlay">
        <div id="modal-content">
            <h2 id="modal-title"></h2>
            <ul id="modal-history-list"></ul>
        </div>
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
    <h2>收藏夹列表</h2>
    <ul class="folder-list">{folder_links}</ul>
    <h2>工具</h2>
    <ul class="folder-list">
        <li><a href="{up_list_path}">查看已关注的UP主列表</a></li>
    </ul>
</div>
"""

FOLDER_PAGE_BODY_TEMPLATE = """
<a href="../index.html">&larr; 返回首页</a>
<div class="controls">
    <div class="search-box">
        <label for="searchInput">在此收藏夹内搜索:</label>
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
</div>
<div class="video-list">
    {video_cards}
</div>
"""

VIDEO_CARD_TEMPLATE = """
<div class="video-card {is_invalid_class}" 
     data-title="{title_attr}"
     data-bv="{bv}"
     data-up="{up_name_attr}"
     data-favtime="{fav_time_iso}" 
     data-pubtime="{pub_time_iso}"
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

# --- Data Processing Functions ---

def build_video_index(RPath, report_dir):
    logging.info("Building global video index...")
    video_index = defaultdict(lambda: {"bvid": "", "info": {}, "history": []})
    
    json_files = [f for f in os.listdir(RPath) if f.endswith('.json') and f != '关注UP列表.json']

    for file_name in json_files:
        collection_name = file_name.rsplit('.', 1)[0]
        try:
            with open(os.path.join(RPath, file_name), 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            for video_id, video_data in data.items():
                bvid = video_data['BV']
                video_index[bvid]['bvid'] = bvid
                
                # Add history
                video_index[bvid]['history'].append({
                    "collection": collection_name,
                    "fav_time": video_data['三个时间']['收藏时间']
                })

                # Store video info (only once)
                if not video_index[bvid]['info']:
                    video_index[bvid]['info'] = {
                        "title": video_data['视频信息']['标题'],
                        "up_name": video_data['up主']['昵称'],
                        "up_id": video_data['up主']['ID'],
                        "is_invalid": video_data.get('是否失效', False),
                         "cover_path": os.path.join('视频封面', collection_name, f"{bvid}.jpg").replace('\\', '/') ,
                        "up_face_path": os.path.join('up头像', f"{video_data['up主']['ID']}.jpg").replace('\\', '/')
                    }
        except Exception as e:
            logging.error(f"Failed to process {file_name}: {e}")

    # Determine latest collection
    for bvid, data in video_index.items():
        data['history'].sort(key=lambda x: x['fav_time'], reverse=True)
        if data['history']:
            data['latest_collection'] = data['history'][0]['collection']
            data['latest_fav_time'] = data['history'][0]['fav_time']

    index_path = os.path.join(report_dir, '视频索引.json')
    with open(index_path, 'w', encoding='utf-8') as f:
        json.dump(video_index, f, ensure_ascii=False)
    logging.info(f"Global video index built and saved to {index_path}")
    return video_index


# --- Main View Generation Function ---

def view(RPath, report_dir_name):
    logging.info("--- Starting HTML Report Generation ---")

    project_root = '.'
    report_path = os.path.join(project_root, report_dir_name)
    assets_path = os.path.join(report_path, 'assets')
    os.makedirs(assets_path, exist_ok=True)
    logging.info(f"Report directory '{report_path}' and assets directory '{assets_path}' are ready.")

    try:
        with open(os.path.join(assets_path, 'style.css'), 'w', encoding='utf-8') as f:
            f.write(CSS_CONTENT)
        logging.info(f"Successfully wrote {os.path.join(assets_path, 'style.css')}")
        with open(os.path.join(assets_path, 'main.js'), 'w', encoding='utf-8') as f:
            f.write(JS_CONTENT)
        logging.info(f"Successfully wrote {os.path.join(assets_path, 'main.js')}")
    except Exception as e:
        logging.error(f"Failed to write asset files: {e}")
        return

    try:
        video_index = build_video_index(RPath, report_path)
        logging.info(f"Successfully built video index with {len(video_index)} videos.")
    except Exception as e:
        logging.error(f"Failed during build_video_index: {e}")
        return
    
    all_files = [f for f in os.listdir(RPath) if f.endswith('.json')]
    fav_files = sorted([f for f in all_files if f not in ['关注UP列表.json', '视频索引.json']])
    
    # --- Generate UP List Page ---
    try:
        up_list_path = os.path.join(RPath, '关注UP列表.json')
        up_list_items = []
        if os.path.exists(up_list_path):
            with open(up_list_path, 'r', encoding='utf-8') as f:
                ups = json.load(f)
            for up in sorted(ups, key=lambda x: x['昵称']):
                up_face_path = os.path.join('up头像', f"{up['ID']}.jpg").replace('\\', '/')
                up_list_items.append(f'''<li class="up-list-item" data-up-name="{html.escape(up['昵称'])}"><a href="https://space.bilibili.com/{up['ID']}" target="_blank"><img src="{up_face_path}" alt="{html.escape(up['昵称'])}"><span>{html.escape(up['昵称'])}</span></a></li>''')
        
        up_list_body = UP_LIST_PAGE_BODY_TEMPLATE.format(up_list_items="".join(up_list_items))
        up_list_html_path = os.path.join(report_path, "关注UP列表.html")
        with open(up_list_html_path, 'w', encoding='utf-8') as f:
            f.write(HTML_TEMPLATE.format(title="关注的UP主列表", header="关注的UP主列表", body=up_list_body, css_path="assets/style.css", js_path="assets/main.js", page_id="up-list"))
        logging.info(f"Successfully wrote {up_list_html_path}")
    except Exception as e:
        logging.error(f"Failed to generate UP list page: {e}")

    # --- Generate Index Page ---
    try:
        folder_links = []
        for fav_file in fav_files:
            folder_name = fav_file.rsplit('.', 1)[0]
            page_file_name = f"fav-{html.escape(folder_name)}.html"
            link_path = os.path.join(report_dir_name, page_file_name).replace("\\", "/")
            folder_links.append(f'<li><a href="{link_path}">{html.escape(folder_name)}</a></li>')

        index_body = INDEX_BODY_TEMPLATE.format(folder_links="".join(folder_links), up_list_path=os.path.join(report_dir_name, '关注UP列表.html').replace('\\', '/'))
        index_html_path = os.path.join(project_root, 'index.html')
        with open(index_html_path, 'w', encoding='utf-8') as f:
            f.write(HTML_TEMPLATE.format(title="Bilibili 收藏夹报告", header="Bilibili 收藏夹报告", body=index_body, css_path=os.path.join(report_dir_name, 'assets/style.css').replace('\\', '/'), js_path=os.path.join(report_dir_name, 'assets/main.js').replace('\\', '/'), page_id="index"))
        logging.info(f"Successfully wrote {index_html_path}")
    except Exception as e:
        logging.error(f"Failed to generate index.html: {e}")

    # --- Generate Individual Folder Pages ---
    for fav_file in fav_files:
        try:
            folder_name = fav_file.rsplit('.', 1)[0]
            with open(os.path.join(RPath, fav_file), 'r', encoding='utf-8') as f:
                data = json.load(f)

            video_cards = []
            sorted_videos = sorted(data.values(), key=lambda x: x['三个时间']['收藏时间'], reverse=True)

            for video in sorted_videos:
                bvid = video['BV']
                video_history = video_index.get(bvid, {}).get('history', [])
                
                card_html = VIDEO_CARD_TEMPLATE.format(
                    title_attr=html.escape(video['视频信息']['标题']), title_html=html.escape(video['视频信息']['标题']),
                    bv=html.escape(bvid),
                    cover_path=os.path.join('视频封面', folder_name, f"{bvid}.jpg").replace('\\', '/'),
                    up_face_path=os.path.join('up头像', f"{video['up主']['ID']}.jpg").replace('\\', '/'),
                    up_name_attr=html.escape(video['up主']['昵称']), up_name_html=html.escape(video['up主']['昵称']),
                    up_id=video['up主']['ID'],
                    play=video['观众数据']['播放量'], collect=video['观众数据']['收藏量'], danmaku=video['观众数据']['弹幕数量'],
                    duration=video['视频信息']['时长'],
                    fav_time=video['三个时间']['收藏时间'], pub_time=video['三个时间']['发布时间'],
                    fav_time_iso=video['三个时间']['收藏时间'].replace(' ', 'T'), pub_time_iso=video['三个时间']['发布时间'].replace(' ', 'T'),
                    history_json=html.escape(json.dumps(video_history, ensure_ascii=False)),
                    is_invalid_class='invalid' if video.get('是否失效') else ''
                )
                video_cards.append(card_html)

            folder_body = FOLDER_PAGE_BODY_TEMPLATE.format(video_cards="".join(video_cards))
            page_file_name = f"fav-{html.escape(folder_name)}.html"
            folder_html_path = os.path.join(report_path, page_file_name)
            with open(folder_html_path, 'w', encoding='utf-8') as f:
                f.write(HTML_TEMPLATE.format(title=f"收藏夹: {html.escape(folder_name)}", header=f"收藏夹: {html.escape(folder_name)}", body=folder_body, css_path="assets/style.css", js_path="assets/main.js", page_id="folder"))
            logging.info(f"Successfully wrote {folder_html_path}")
        except Exception as e:
            logging.error(f"Failed to generate page for {fav_file}: {e}")

    logging.info("--- HTML Report Generation Finished ---")
