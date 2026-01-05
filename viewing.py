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
    --moved-bg: rgba(74, 144, 226, 0.1);
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
.controls input[type="date"], .controls input[type="checkbox"] {
    padding: 10px;
    border-radius: 5px;
    border: 1px solid var(--input-border);
    background-color: var(--input-bg);
    color: var(--text-color);
    font-size: 1em;
    box-sizing: border-box;
}
.controls input[type="text"] {
    width: 100%;
}
.controls label {
    margin-right: 5px;
    cursor: pointer;
    display: inline-flex;
    align-items: center;
    gap: 5px;
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
    cursor: pointer;
}

.folder-list li:hover, .up-list-item:hover {
    transform: translateY(-3px);
    box-shadow: 0 4px 10px rgba(0,0,0,0.3);
}

.folder-list a {
    display: block;
    padding: 20px;
    font-size: 1.2em;
    font-weight: bold;
}

.up-list {
     grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
}

.up-list-item .up-link {
    display: flex;
    align-items: center;
    gap: 15px;
    padding: 15px;
    font-size: 1em;
    font-weight: bold;
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
    border-color: #704545;
}
.video-card.moved {
    background-color: var(--moved-bg);
    border-color: #4a6a90;
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

/* History Display Styles */
.history-row {
    grid-column: 1 / -1;
    background-color: #222;
    padding: 20px;
    margin-top: 10px;
    margin-bottom: 10px;
    border-radius: 8px;
    animation: fadeIn 0.5s;
    border-left: 3px solid var(--link-color);
}
.history-row h3 {
    margin-top: 0;
    font-size: 1.2em;
}
.history-row ul {
    list-style: none;
    padding-left: 0;
}
.history-row li {
    padding: 5px 0;
}
@keyframes fadeIn {
    from { opacity: 0; transform: translateY(-10px); }
    to { opacity: 1; transform: translateY(0); }
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

    // --- Page Specific Logic ---
    const pageId = document.body.id;

    if (pageId === 'page-index') {
        handleGlobalSearch();
    } else if (pageId === 'page-folder') {
        handleFolderPage();
    } else if (pageId === 'page-up-list') {
        handleUpListPage();
    }
});

function handleFolderPage() {
    const videoList = document.querySelector('.video-list');

    // --- Filter Logic ---
    const searchInput = document.getElementById('searchInput');
    const favDateStart = document.getElementById('favDateStart');
    const favDateEnd = document.getElementById('favDateEnd');
    const pubDateStart = document.getElementById('pubDateStart');
    const pubDateEnd = document.getElementById('pubDateEnd');
    const showCurrentOnlyCheckbox = document.getElementById('showCurrentOnly');
    const videoCards = document.querySelectorAll('.video-card');

    function filter() {
        const searchText = searchInput.value.toLowerCase();
        const favStart = favDateStart.value ? new Date(favDateStart.value) : null;
        const favEnd = favDateEnd.value ? new Date(favDateEnd.value) : null;
        const pubStart = pubDateStart.value ? new Date(pubDateStart.value) : null;
        const pubEnd = pubDateEnd.value ? new Date(pubDateEnd.value) : null;
        const showCurrent = showCurrentOnlyCheckbox.checked;

        videoCards.forEach(card => {
            const title = card.dataset.title.toLowerCase();
            const bv = card.dataset.bv.toLowerCase();
            const upName = card.dataset.up.toLowerCase();
            const favTime = new Date(card.dataset.favtime);
            const pubTime = new Date(card.dataset.pubtime);

            const isCurrent = !card.classList.contains('invalid') && !card.classList.contains('moved');
            
            const matchesCurrentOnly = !showCurrent || isCurrent;
            const matchesSearch = title.includes(searchText) || bv.includes(searchText) || upName.includes(searchText);
            const matchesFavDate = (!favStart || favTime >= favStart) && (!favEnd || favTime <= favEnd);
            const matchesPubDate = (!pubStart || pubTime >= pubStart) && (!pubEnd || pubTime <= pubEnd);

            if (matchesSearch && matchesFavDate && matchesPubDate && matchesCurrentOnly) {
                card.classList.remove('hidden');
            } else {
                card.classList.add('hidden');
            }
        });
        
        const historyRow = document.getElementById('history-display');
        if(historyRow && historyRow.dataset.bv) {
            const parentCard = document.querySelector(`.video-card[data-bv="${historyRow.dataset.bv}"]`);
            if (parentCard && parentCard.classList.contains('hidden')) {
                historyRow.remove();
            }
        }
    }

    [searchInput, favDateStart, favDateEnd, pubDateStart, pubDateEnd, showCurrentOnlyCheckbox].forEach(el => {
        el.addEventListener('input', filter);
        el.addEventListener('change', filter);
    });
    
    // --- History Display Logic ---
    if (videoList) {
        videoList.addEventListener('click', (e) => {
            const card = e.target.closest('.video-card');
            
            if (!card || e.target.closest('a')) {
                return;
            }

            const existingHistoryRow = document.getElementById('history-display');
            if (existingHistoryRow) {
                const wasOpenForThisCard = existingHistoryRow.dataset.bv === card.dataset.bv;
                existingHistoryRow.remove();
                if (wasOpenForThisCard) {
                    return; // Toggle off
                }
            }

            const history = JSON.parse(card.dataset.history);
            // Sort all events chronologically
            history.sort((a,b) => new Date(a.time) - new Date(b.time));
            
            let historyHtml = `<h3>'${card.dataset.title}' 的收藏历史</h3><ul>`;
            history.forEach((item, index) => {
                let actionText = '';
                if (item.type === 'add') {
                    // The first 'add' event is a 'collect', subsequent ones are 'move'
                    const isFirstAdd = history.slice(0, index).filter(e => e.type === 'add').length === 0;
                    const action = isFirstAdd ? '收藏于' : '移动至';
                    actionText = `<strong>${action}</strong>《${item.collection}》`;
                } else if (item.type === 'remove') {
                    actionText = `从《${item.collection}》中<strong>移除</strong>`;
                }
                historyHtml += `<li>于 ${item.time} ${actionText}</li>`;
            });
            historyHtml += '</ul>';

            const historyRow = document.createElement('div');
            historyRow.id = 'history-display';
            historyRow.className = 'history-row';
            historyRow.dataset.bv = card.dataset.bv;
            historyRow.innerHTML = historyHtml;

            let insertionPoint = card;
            const cardTop = card.offsetTop;
            const allCards = Array.from(videoList.children).filter(child => !child.classList.contains('history-row'));
            const clickedIndex = allCards.indexOf(card);

            for (let i = clickedIndex + 1; i < allCards.length; i++) {
                if (allCards[i].offsetTop > cardTop) {
                    break; 
                }
                insertionPoint = allCards[i];
            }
            
            insertionPoint.after(historyRow);
            historyRow.scrollIntoView({ behavior: 'smooth', block: 'center' });
        });
    }
}

function handleGlobalSearch() {
    const searchInput = document.getElementById('globalSearchInput');
    const resultsContainer = document.getElementById('global-search-results');
    const indexList = document.getElementById('index-list');
    let videoIndex = null;

    async function loadIndexAndSearch(query) {
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
        search(query);
    }

    function search(query) {
        if (query.length < 1) {
            resultsContainer.style.display = 'none';
            resultsContainer.innerHTML = '';
            indexList.style.display = 'block';
            return;
        }

        const lowerCaseQuery = query.toLowerCase();
        const results = Object.values(videoIndex).filter(video => {
            return video.info.title.toLowerCase().includes(lowerCaseQuery) ||
                   video.bvid.toLowerCase().includes(lowerCaseQuery) ||
                   video.info.up_name.toLowerCase().includes(lowerCaseQuery);
        });
        
        results.sort((a,b) => new Date(b.latest_fav_time) - new Date(a.latest_fav_time));

        indexList.style.display = 'none';
        resultsContainer.style.display = 'grid';
        resultsContainer.innerHTML = '';

        if (results.length === 0) {
            resultsContainer.innerHTML = `<p>没有找到关于“${query}”的视频。</p>`;
            return;
        }

        results.forEach(video => {
            const card = document.createElement('div');
            let status_class = '';
            if (video.info.is_invalid) {
                status_class = 'invalid';
            } else if (video.info.is_unfavorited) {
                 status_class = 'moved';
            }
            card.className = 'video-card ' + status_class;
            card.dataset.history = JSON.stringify(video.history);
            card.dataset.title = video.info.title;
            card.dataset.bv = video.bvid;

            const coverPath = 'html_report/' + video.info.cover_path;
            const upFacePath = 'html_report/' + video.info.up_face_path;

            card.innerHTML = `
                <a class="cover-link" href="https://www.bilibili.com/video/${video.bvid}" target="_blank">
                    <img src="${coverPath}" alt="${video.info.title}" class="cover" loading="lazy">
                </a>
                <div class="info">
                    <h3 class="title"><a href="https://www.bilibili.com/video/${video.bvid}" target="_blank">${video.info.title}</a></h3>
                    <div class="meta">
                         <a href="https://space.bilibili.com/${video.info.up_id}" target="_blank">
                            <img src="${upFacePath}" alt="${video.info.up_name}" class="up-face" loading="lazy">
                        </a>
                        <a href="https://space.bilibili.com/${video.info.up_id}" target="_blank"><span class="up-name">${video.info.up_name}</span></a>
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

    searchInput.addEventListener('keyup', (e) => loadIndexAndSearch(e.target.value));

    const urlParams = new URLSearchParams(window.location.search);
    const upFilter = urlParams.get('up_filter');
    if (upFilter) {
        const decodedUpFilter = decodeURIComponent(upFilter);
        searchInput.value = decodedUpFilter;
        loadIndexAndSearch(decodedUpFilter);
    }
}

function handleUpListPage() {
    const searchInput = document.getElementById('upSearchInput');
    const upItems = document.querySelectorAll('.up-list-item');
    const upList = document.querySelector('.up-list');

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

    upList.addEventListener('click', (e) => {
        const card = e.target.closest('.up-list-item');
        if (!card) return;

        if (e.target.closest('a.up-name-link')) {
            return;
        }

        const upName = card.dataset.upName;
        window.location.href = `../index.html?up_filter=${encodeURIComponent(upName)}`;
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
    <div>
        <label><input type="checkbox" id="showCurrentOnly"> 仅显示当前</label>
    </div>
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
                bvid = video_data.get('BV')
                if not bvid: continue

                video_index[bvid]['bvid'] = bvid
                
                # Add 'add' event
                video_index[bvid]['history'].append({
                    "type": "add",
                    "collection": collection_name,
                    "time": video_data['三个时间']['收藏时间']
                })

                # Add 'remove' event if it exists
                if video_data.get('是否取消了收藏'):
                    video_index[bvid]['history'].append({
                        "type": "remove",
                        "collection": collection_name,
                        "time": video_data['取消收藏时间']
                    })

                # Store video info, favoring the entry that isn't cancelled
                if not video_index[bvid]['info'] or not video_data.get('是否取消了收藏'):
                     video_index[bvid]['info'] = {
                        "title": video_data['视频信息']['标题'],
                        "up_name": video_data['up主']['昵称'],
                        "up_id": video_data['up主']['ID'],
                        "is_invalid": video_data.get('是否失效', False),
                        "is_unfavorited": video_data.get('是否取消了收藏', False),
                        "cover_path": os.path.join('视频封面', collection_name, f"{bvid}.jpg").replace('\\', '/') ,
                        "up_face_path": os.path.join('up头像', f"{video_data['up主']['ID']}.jpg").replace('\\', '/') ,
                    }
        except Exception as e:
            logging.error(f"Failed to process {file_name}: {e}")

    # Determine latest status for each video
    for bvid, data in video_index.items():
        data['history'].sort(key=lambda x: x['time'], reverse=True)
        if data['history']:
            latest_event = data['history'][0]
            if latest_event['type'] == 'add':
                data['latest_collection'] = latest_event['collection']
                data['latest_fav_time'] = latest_event['time']
            else: # If latest event is a removal, find the last 'add' event
                last_add = next((event for event in data['history'] if event['type'] == 'add'), None)
                if last_add:
                    data['latest_collection'] = last_add['collection']
                    data['latest_fav_time'] = last_add['time']
                else: # Should not happen if data is consistent
                    data['latest_collection'] = 'N/A'
                    data['latest_fav_time'] = 'N/A'


    index_path = os.path.join(report_dir, '视频索引.json')
    with open(index_path, 'w', encoding='utf-8') as f:
        json.dump(video_index, f, ensure_ascii=False)
    logging.info(f"Global video index built and saved to {index_path}")
    return video_index


# --- Main View Generation Function ---

def view(RPath, report_dir_name):
    logging.info("---" + "Starting HTML Report Generation" + "---")

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

    video_index = build_video_index(RPath, report_path)
    all_files = [f for f in os.listdir(RPath) if f.endswith('.json')]
    fav_files = sorted([f for f in all_files if f not in ['关注UP列表.json', '视频索引.json']])
    
    # --- Generate UP List Page ---
    up_list_path = os.path.join(RPath, '关注UP列表.json')
    up_list_items = []
    if os.path.exists(up_list_path):
        with open(up_list_path, 'r', encoding='utf-8') as f:
            ups = json.load(f)
        for up in sorted(ups, key=lambda x: x.get('昵称', '')):
            up_face_path = os.path.join('up头像', f"{up['ID']}.jpg").replace('\\', '/')
            up_list_items.append(f'''<li class="up-list-item" data-up-name="{html.escape(up['昵称'])}">
                    <div class="up-link">
                        <img src="{up_face_path}" alt="{html.escape(up['昵称'])}">
                        <a class="up-name-link" href="https://space.bilibili.com/{up['ID']}" target="_blank">{html.escape(up['昵称'])}</a>
                    </div>
                </li>''')
    
    up_list_page_html = HTML_TEMPLATE.format(
        title="关注的UP主列表", header="关注的UP主列表",
        body=UP_LIST_PAGE_BODY_TEMPLATE.format(up_list_items="".join(up_list_items)),
        css_path="assets/style.css", js_path="assets/main.js", page_id="up-list"
    )
    with open(os.path.join(report_path, "关注UP列表.html"), 'w', encoding='utf-8') as f:
        f.write(up_list_page_html)

    # --- Generate Index Page ---
    folder_links = []
    for fav_file in fav_files:
        folder_name = fav_file.rsplit('.', 1)[0]
        page_file_name = f"fav-{html.escape(folder_name)}.html"
        link_path = os.path.join(report_dir_name, page_file_name).replace("\\", "/")
        folder_links.append(f'<li><a href="{link_path}">{html.escape(folder_name)}</a></li>')

    index_body = INDEX_BODY_TEMPLATE.format(folder_links="".join(folder_links), up_list_path=os.path.join(report_dir_name, '关注UP列表.html').replace('\\', '/'))
    index_html = HTML_TEMPLATE.format(
        title="Bilibili 收藏夹报告", header="Bilibili 收藏夹报告", body=index_body,
        css_path=os.path.join(report_dir_name, 'assets/style.css').replace('\\', '/'),
        js_path=os.path.join(report_dir_name, 'assets/main.js').replace('\\', '/'), page_id="index"
    )
    with open(os.path.join(project_root, 'index.html'), 'w', encoding='utf-8') as f:
        f.write(index_html)
    logging.info("Generated index.html")

    # --- Generate Individual Folder Pages ---
    for fav_file in fav_files:
        folder_name = fav_file.rsplit('.', 1)[0]
        
        with open(os.path.join(RPath, fav_file), 'r', encoding='utf-8') as f:
            data = json.load(f)

        video_cards = []
        sorted_videos = sorted(data.values(), key=lambda x: x.get('取消收藏时间') or x['三个时间']['收藏时间'], reverse=True)

        for video in sorted_videos:
            bvid = video['BV']
            video_from_index = video_index.get(bvid, {})
            video_history = video_from_index.get('history', [])
            latest_collection = video_from_index.get('latest_collection', folder_name)

            status_class = ''
            if video.get('是否失效'):
                status_class = 'invalid'
            elif video.get('是否取消了收藏') or latest_collection != folder_name:
                status_class = 'moved'

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
                status_class=status_class
            )
            video_cards.append(card_html)

        folder_body = FOLDER_PAGE_BODY_TEMPLATE.format(video_cards="".join(video_cards))
        folder_html = HTML_TEMPLATE.format(
            title=f"收藏夹: {html.escape(folder_name)}", header=f"收藏夹: {html.escape(folder_name)}",
            body=folder_body, css_path="assets/style.css", js_path="assets/main.js", page_id="folder"
        )
        with open(os.path.join(report_path, f"fav-{html.escape(folder_name)}.html"), 'w', encoding='utf-8') as f:
            f.write(folder_html)
        logging.info(f"Generated page for {folder_name}")

    logging.info("---" + "HTML Report Generation Finished" + "---")
