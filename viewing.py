import os
import json
import logging
import html
from database import get_connection, get_all_collections, get_videos_in_collection, get_video_history, get_all_videos_index, get_all_following_ups, get_stats

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
    --accent-green: #4caf50;
    --accent-orange: #ff9800;
    --accent-red: #f44336;
    --accent-purple: #9c27b0;
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
.controls select {
    padding: 10px;
    border-radius: 5px;
    border: 1px solid var(--input-border);
    background-color: var(--input-bg);
    color: var(--text-color);
    font-size: 1em;
    cursor: pointer;
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

/* Pagination */
.pagination {
    display: flex;
    justify-content: center;
    align-items: center;
    gap: 8px;
    margin: 25px 0;
    flex-wrap: wrap;
}
.pagination button {
    padding: 8px 16px;
    border: 1px solid var(--input-border);
    background-color: var(--card-bg);
    color: var(--text-color);
    border-radius: 5px;
    cursor: pointer;
    font-size: 0.95em;
    transition: background-color 0.2s;
}
.pagination button:hover:not(:disabled) {
    background-color: var(--button-bg);
}
.pagination button:disabled {
    opacity: 0.4;
    cursor: not-allowed;
}
.pagination button.active {
    background-color: var(--button-bg);
    border-color: var(--button-bg);
    font-weight: bold;
}
.pagination .page-info {
    color: #b0b0b0;
    font-size: 0.9em;
}

/* Dashboard */
.dashboard {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
    gap: 15px;
    margin-bottom: 30px;
}
.stat-card {
    background-color: var(--card-bg);
    border-radius: 8px;
    padding: 20px;
    text-align: center;
}
.stat-card .stat-number {
    font-size: 2.2em;
    font-weight: bold;
    margin: 5px 0;
}
.stat-card .stat-label {
    font-size: 0.85em;
    color: #b0b0b0;
}
.stat-card.green .stat-number { color: var(--accent-green); }
.stat-card.blue .stat-number { color: var(--link-color); }
.stat-card.orange .stat-number { color: var(--accent-orange); }
.stat-card.red .stat-number { color: var(--accent-red); }
.stat-card.purple .stat-number { color: var(--accent-purple); }

.charts-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(450px, 1fr));
    gap: 20px;
    margin-bottom: 30px;
}
.chart-container {
    background-color: var(--card-bg);
    border-radius: 8px;
    padding: 20px;
}
.chart-container h3 {
    margin-top: 0;
    color: var(--text-color);
    border-bottom: none;
}
.chart-container canvas {
    max-height: 350px;
}

.recent-list {
    background-color: var(--card-bg);
    border-radius: 8px;
    padding: 20px;
    margin-bottom: 20px;
}
.recent-list h3 {
    margin-top: 0;
    border-bottom: none;
}
.recent-list table {
    width: 100%;
    border-collapse: collapse;
}
.recent-list th, .recent-list td {
    text-align: left;
    padding: 8px 12px;
    border-bottom: 1px solid var(--border-color);
}
.recent-list th {
    color: #b0b0b0;
    font-weight: normal;
    font-size: 0.85em;
}

/* Export button */
.export-btn {
    padding: 10px 18px;
    background-color: var(--accent-green);
    color: white;
    border: none;
    border-radius: 5px;
    cursor: pointer;
    font-size: 0.95em;
    transition: background-color 0.2s;
}
.export-btn:hover {
    background-color: #45a049;
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
    const backToTopButton = document.getElementById('back-to-top');
    if (backToTopButton) {
        window.onscroll = () => {
            backToTopButton.style.display = (document.body.scrollTop > 100 || document.documentElement.scrollTop > 100) ? "block" : "none";
        };
        backToTopButton.onclick = () => {
            document.body.scrollTop = 0;
            document.documentElement.scrollTop = 0;
        };
    }

    const pageId = document.body.id;
    if (pageId === 'page-index') {
        handleGlobalSearch();
        initDashboardCharts();
    } else if (pageId === 'page-folder') {
        handleFolderPage();
    } else if (pageId === 'page-up-list') {
        handleUpListPage();
    }
});

// --- Folder Page: Filter + Sort + Paginate + History ---
function handleFolderPage() {
    const videoList = document.querySelector('.video-list');
    const searchInput = document.getElementById('searchInput');
    const favDateStart = document.getElementById('favDateStart');
    const favDateEnd = document.getElementById('favDateEnd');
    const pubDateStart = document.getElementById('pubDateStart');
    const pubDateEnd = document.getElementById('pubDateEnd');
    const showCurrentOnlyCheckbox = document.getElementById('showCurrentOnly');
    const sortSelect = document.getElementById('sortSelect');
    const allCards = Array.from(document.querySelectorAll('.video-card'));
    const CARDS_PER_PAGE = 50;
    let currentPage = 1;
    let filteredCards = [...allCards];

    function getCardSortValue(card, key) {
        switch(key) {
            case 'fav_desc': return -(new Date(card.dataset.favtime).getTime());
            case 'fav_asc': return new Date(card.dataset.favtime).getTime();
            case 'pub_desc': return -(new Date(card.dataset.pubtime).getTime());
            case 'pub_asc': return new Date(card.dataset.pubtime).getTime();
            case 'play_desc': return -(parseInt(card.dataset.play) || 0);
            case 'collect_desc': return -(parseInt(card.dataset.collect) || 0);
            case 'danmaku_desc': return -(parseInt(card.dataset.danmaku) || 0);
            case 'duration_desc': return -(parseDuration(card.dataset.duration));
            default: return 0;
        }
    }

    function parseDuration(dur) {
        if (!dur) return 0;
        const parts = dur.split(':').map(Number);
        return parts[0] * 3600 + parts[1] * 60 + parts[2];
    }

    function filterAndSort() {
        const searchText = searchInput.value.toLowerCase();
        const favStart = favDateStart.value ? new Date(favDateStart.value) : null;
        const favEnd = favDateEnd.value ? new Date(favDateEnd.value) : null;
        const pubStart = pubDateStart.value ? new Date(pubDateStart.value) : null;
        const pubEnd = pubDateEnd.value ? new Date(pubDateEnd.value) : null;
        const showCurrent = showCurrentOnlyCheckbox.checked;
        const sortKey = sortSelect.value;

        filteredCards = allCards.filter(card => {
            const title = card.dataset.title.toLowerCase();
            const bv = card.dataset.bv.toLowerCase();
            const upName = card.dataset.up.toLowerCase();
            const favTime = new Date(card.dataset.favtime);
            const pubTime = new Date(card.dataset.pubtime);
            const isCurrent = !card.classList.contains('invalid') && !card.classList.contains('moved');

            return (!showCurrent || isCurrent) &&
                   (title.includes(searchText) || bv.includes(searchText) || upName.includes(searchText)) &&
                   (!favStart || favTime >= favStart) && (!favEnd || favTime <= favEnd) &&
                   (!pubStart || pubTime >= pubStart) && (!pubEnd || pubTime <= pubEnd);
        });

        filteredCards.sort((a, b) => getCardSortValue(a, sortKey) - getCardSortValue(b, sortKey));
        currentPage = 1;
        renderPage();
    }

    function renderPage() {
        // Remove history row if any
        const historyRow = document.getElementById('history-display');
        if (historyRow) historyRow.remove();

        const totalPages = Math.max(1, Math.ceil(filteredCards.length / CARDS_PER_PAGE));
        if (currentPage > totalPages) currentPage = totalPages;

        const start = (currentPage - 1) * CARDS_PER_PAGE;
        const end = start + CARDS_PER_PAGE;
        const pageCards = new Set(filteredCards.slice(start, end));

        allCards.forEach(card => {
            card.classList.toggle('hidden', !pageCards.has(card));
        });

        renderPagination(totalPages);
    }

    function renderPagination(totalPages) {
        let pag = document.getElementById('pagination-controls');
        if (!pag) {
            pag = document.createElement('div');
            pag.id = 'pagination-controls';
            pag.className = 'pagination';
            videoList.parentNode.insertBefore(pag, videoList.nextSibling);
        }

        let btns = '';
        btns += `<button onclick="window.__goPage(1)" ${currentPage === 1 ? 'disabled' : ''}>&laquo;</button>`;
        btns += `<button onclick="window.__goPage(${currentPage - 1})" ${currentPage === 1 ? 'disabled' : ''}>&lsaquo;</button>`;

        const maxButtons = 7;
        let startPage = Math.max(1, currentPage - Math.floor(maxButtons / 2));
        let endPage = Math.min(totalPages, startPage + maxButtons - 1);
        if (endPage - startPage < maxButtons - 1) startPage = Math.max(1, endPage - maxButtons + 1);

        for (let i = startPage; i <= endPage; i++) {
            btns += `<button class="${i === currentPage ? 'active' : ''}" onclick="window.__goPage(${i})">${i}</button>`;
        }

        btns += `<button onclick="window.__goPage(${currentPage + 1})" ${currentPage === totalPages ? 'disabled' : ''}>&rsaquo;</button>`;
        btns += `<button onclick="window.__goPage(${totalPages})" ${currentPage === totalPages ? 'disabled' : ''}>&raquo;</button>`;
        btns += `<span class="page-info">${filteredCards.length} 条 / ${totalPages} 页</span>`;
        pag.innerHTML = btns;
    }

    window.__goPage = function(page) {
        currentPage = page;
        renderPage();
        window.scrollTo({ top: videoList.offsetTop - 20, behavior: 'smooth' });
    };

    // Bind events with debounce for text input
    let debounceTimer;
    searchInput.addEventListener('input', () => {
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(filterAndSort, 300);
    });
    [favDateStart, favDateEnd, pubDateStart, pubDateEnd, showCurrentOnlyCheckbox, sortSelect].forEach(el => {
        el.addEventListener('change', filterAndSort);
    });

    // Initial render
    filterAndSort();

    // --- History Display ---
    if (videoList) {
        videoList.addEventListener('click', (e) => {
            const card = e.target.closest('.video-card');
            if (!card || e.target.closest('a')) return;

            const existingHistoryRow = document.getElementById('history-display');
            if (existingHistoryRow) {
                const wasOpenForThisCard = existingHistoryRow.dataset.bv === card.dataset.bv;
                existingHistoryRow.remove();
                if (wasOpenForThisCard) return;
            }

            const history = JSON.parse(card.dataset.history);
            history.sort((a,b) => new Date(a.time) - new Date(b.time));

            let historyHtml = `<h3>'${card.dataset.title}' 的收藏历史</h3><ul>`;
            history.forEach((item, index) => {
                let actionText = '';
                if (item.type === 'add') {
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
            const visibleCards = Array.from(videoList.children).filter(c => !c.classList.contains('history-row') && !c.classList.contains('hidden'));
            const clickedIndex = visibleCards.indexOf(card);

            for (let i = clickedIndex + 1; i < visibleCards.length; i++) {
                if (visibleCards[i].offsetTop > cardTop) break;
                insertionPoint = visibleCards[i];
            }

            insertionPoint.after(historyRow);
            historyRow.scrollIntoView({ behavior: 'smooth', block: 'center' });
        });
    }

    // --- CSV Export Button ---
    const exportBtn = document.getElementById('exportCsvBtn');
    if (exportBtn) {
        exportBtn.addEventListener('click', () => {
            let csv = '\\uFEFF' + 'BV号,标题,UP主,播放量,收藏量,弹幕数,时长,收藏时间,发布时间\\n';
            filteredCards.forEach(card => {
                const row = [
                    card.dataset.bv,
                    '"' + card.dataset.title.replace(/"/g, '""') + '"',
                    '"' + card.dataset.up.replace(/"/g, '""') + '"',
                    card.dataset.play, card.dataset.collect, card.dataset.danmaku,
                    card.dataset.duration, card.dataset.favtime, card.dataset.pubtime
                ].join(',');
                csv += row + '\\n';
            });
            const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
            const link = document.createElement('a');
            link.href = URL.createObjectURL(blob);
            link.download = document.title.replace(/[^a-zA-Z0-9\\u4e00-\\u9fff]/g, '_') + '.csv';
            link.click();
        });
    }
}

// --- Global Search ---
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
            resultsContainer.innerHTML = `<p>没有找到关于"${query}"的视频。</p>`;
            return;
        }
        results.forEach(video => {
            const card = document.createElement('div');
            let status_class = '';
            if (video.info.is_invalid) status_class = 'invalid';
            else if (video.info.is_unfavorited) status_class = 'moved';
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

    let debounceTimer;
    searchInput.addEventListener('keyup', (e) => {
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(() => loadIndexAndSearch(e.target.value), 300);
    });

    const urlParams = new URLSearchParams(window.location.search);
    const upFilter = urlParams.get('up_filter');
    if (upFilter) {
        const decodedUpFilter = decodeURIComponent(upFilter);
        searchInput.value = decodedUpFilter;
        loadIndexAndSearch(decodedUpFilter);
    }
}

// --- UP List Page ---
function handleUpListPage() {
    const searchInput = document.getElementById('upSearchInput');
    const upItems = document.querySelectorAll('.up-list-item');
    const upList = document.querySelector('.up-list');

    let debounceTimer;
    searchInput.addEventListener('keyup', () => {
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(() => {
            const query = searchInput.value.toLowerCase();
            upItems.forEach(item => {
                const upName = item.dataset.upName.toLowerCase();
                item.classList.toggle('hidden', !upName.includes(query));
            });
        }, 300);
    });

    upList.addEventListener('click', (e) => {
        const card = e.target.closest('.up-list-item');
        if (!card) return;
        if (e.target.closest('a.up-name-link')) return;
        const upName = card.dataset.upName;
        window.location.href = `../index.html?up_filter=${encodeURIComponent(upName)}`;
    });
}

// --- Dashboard Charts ---
function initDashboardCharts() {
    const statsEl = document.getElementById('dashboard-stats');
    if (!statsEl) return;

    let stats;
    try {
        stats = JSON.parse(statsEl.textContent);
    } catch(e) {
        console.error("Failed to parse dashboard stats:", e);
        return;
    }

    // Colors
    const palette = ['#4a90e2','#4caf50','#ff9800','#f44336','#9c27b0','#00bcd4','#ff5722','#607d8b','#e91e63','#8bc34a',
                      '#3f51b5','#009688','#ffc107','#795548','#cddc39','#2196f3','#673ab7','#ff4081','#00e676','#d500f9'];

    // Chart.js defaults
    Chart.defaults.color = '#b0b0b0';
    Chart.defaults.borderColor = '#444';

    // Collection bar chart
    const collCtx = document.getElementById('chart-collections');
    if (collCtx && stats.collection_counts) {
        new Chart(collCtx, {
            type: 'bar',
            data: {
                labels: stats.collection_counts.map(c => c.name),
                datasets: [{
                    label: '视频数量',
                    data: stats.collection_counts.map(c => c.count),
                    backgroundColor: palette.slice(0, stats.collection_counts.length),
                    borderRadius: 4,
                }]
            },
            options: {
                indexAxis: stats.collection_counts.length > 10 ? 'y' : 'x',
                responsive: true,
                plugins: { legend: { display: false } },
            }
        });
    }

    // Monthly trend
    const trendCtx = document.getElementById('chart-trend');
    if (trendCtx && stats.monthly_trend) {
        new Chart(trendCtx, {
            type: 'line',
            data: {
                labels: stats.monthly_trend.map(t => t.month),
                datasets: [{
                    label: '新增收藏',
                    data: stats.monthly_trend.map(t => t.count),
                    borderColor: '#4a90e2',
                    backgroundColor: 'rgba(74,144,226,0.1)',
                    fill: true, tension: 0.3,
                }]
            },
            options: { responsive: true, plugins: { legend: { display: false } } }
        });
    }

    // Top UPs
    const upCtx = document.getElementById('chart-top-ups');
    if (upCtx && stats.top_ups) {
        new Chart(upCtx, {
            type: 'bar',
            data: {
                labels: stats.top_ups.map(u => u.name),
                datasets: [{
                    label: '视频数量',
                    data: stats.top_ups.map(u => u.count),
                    backgroundColor: palette.slice(0, stats.top_ups.length),
                    borderRadius: 4,
                }]
            },
            options: {
                indexAxis: 'y',
                responsive: true,
                plugins: { legend: { display: false } },
            }
        });
    }

    // Duration distribution
    const durCtx = document.getElementById('chart-duration');
    if (durCtx && stats.duration_distribution) {
        const labels = Object.keys(stats.duration_distribution);
        new Chart(durCtx, {
            type: 'doughnut',
            data: {
                labels: labels,
                datasets: [{
                    data: labels.map(l => stats.duration_distribution[l]),
                    backgroundColor: palette.slice(0, labels.length),
                }]
            },
            options: { responsive: true }
        });
    }
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
        return ''

    html_parts = ['<h2>数据总览</h2>']

    # Stat cards
    html_parts.append('<div class="dashboard">')
    cards = [
        ('green', stats.get('total_videos', 0), '总视频数'),
        ('blue', stats.get('total_collections', 0), '收藏夹数'),
        ('purple', stats.get('total_ups', 0), '收藏 UP 主数'),
        ('orange', stats.get('following_ups', 0), '关注 UP 主数'),
        ('red', stats.get('invalid_videos', 0), '失效视频数'),
    ]
    for color, number, label in cards:
        html_parts.append(f'<div class="stat-card {color}"><div class="stat-number">{number}</div><div class="stat-label">{label}</div></div>')
    html_parts.append('</div>')

    # Charts
    html_parts.append('<div class="charts-grid">')
    html_parts.append('<div class="chart-container"><h3>📊 各收藏夹视频数量</h3><canvas id="chart-collections"></canvas></div>')
    html_parts.append('<div class="chart-container"><h3>📈 按月收藏趋势</h3><canvas id="chart-trend"></canvas></div>')
    html_parts.append('<div class="chart-container"><h3>🏆 TOP 10 收藏最多的 UP 主</h3><canvas id="chart-top-ups"></canvas></div>')
    html_parts.append('<div class="chart-container"><h3>🎯 视频时长分布</h3><canvas id="chart-duration"></canvas></div>')
    html_parts.append('</div>')

    # Recent invalid videos
    if stats.get('recent_invalid'):
        html_parts.append('<div class="recent-list"><h3>⚠️ 最近失效的视频</h3><table><tr><th>标题</th><th>UP主</th><th>收藏夹</th><th>BV号</th></tr>')
        for v in stats['recent_invalid'][:10]:
            html_parts.append(f'<tr><td>{html_escape(v["title"])}</td><td>{html_escape(v["up_name"])}</td><td>{html_escape(v["collection"])}</td><td><a href="https://www.bilibili.com/video/{v["bv_id"]}" target="_blank">{v["bv_id"]}</a></td></tr>')
        html_parts.append('</table></div>')

    # Recent unfavorited videos
    if stats.get('recent_unfav'):
        html_parts.append('<div class="recent-list"><h3>📤 最近取消收藏的视频</h3><table><tr><th>标题</th><th>UP主</th><th>收藏夹</th><th>取消时间</th></tr>')
        for v in stats['recent_unfav'][:10]:
            html_parts.append(f'<tr><td>{html_escape(v["title"])}</td><td>{html_escape(v["up_name"])}</td><td>{html_escape(v["collection"])}</td><td>{v["unfav_time"]}</td></tr>')
        html_parts.append('</table></div>')

    return '\n'.join(html_parts)


def html_escape(text):
    """安全的 HTML 转义"""
    if text is None:
        return ''
    return html.escape(str(text))


# --- Main View Generation Function ---

def view(db_path, report_dir_name):
    logging.info("---Starting HTML Report Generation---")

    project_root = '.'
    report_path = os.path.join(project_root, report_dir_name)
    assets_path = os.path.join(report_path, 'assets')
    os.makedirs(assets_path, exist_ok=True)

    try:
        with open(os.path.join(assets_path, 'style.css'), 'w', encoding='utf-8') as f:
            f.write(CSS_CONTENT)
        with open(os.path.join(assets_path, 'main.js'), 'w', encoding='utf-8') as f:
            f.write(JS_CONTENT)
        logging.info("Asset files written.")
    except Exception as e:
        logging.error(f"Failed to write asset files: {e}")
        return

    with get_connection(db_path) as conn:
        # Build and save video index for global search
        video_index = get_all_videos_index(conn)
        index_path = os.path.join(report_path, '视频索引.json')
        with open(index_path, 'w', encoding='utf-8') as f:
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
            up_list_items.append(f'''<li class="up-list-item" data-up-name="{html_escape(up['name'])}">
                    <div class="up-link">
                        <img src="{up_face_path}" alt="{html_escape(up['name'])}">
                        <a class="up-name-link" href="https://space.bilibili.com/{up['mid']}" target="_blank">{html_escape(up['name'])}</a>
                    </div>
                </li>''')

        up_list_page_html = HTML_TEMPLATE.format(
            title="关注的UP主列表", header="关注的UP主列表",
            body=UP_LIST_PAGE_BODY_TEMPLATE.format(up_list_items="".join(up_list_items)),
            css_path="assets/style.css", js_path="assets/main.js", page_id="up-list", extra_head=""
        )
        with open(os.path.join(report_path, "关注UP列表.html"), 'w', encoding='utf-8') as f:
            f.write(up_list_page_html)

        # --- Generate Index Page ---
        folder_links = []
        for coll in collections:
            page_file_name = f"fav-{html_escape(coll['name'])}.html"
            link_path = os.path.join(report_dir_name, page_file_name).replace("\\", "/")
            folder_links.append(f'<li><a href="{link_path}">{html_escape(coll["name"])}</a></li>')

        dashboard_html = generate_dashboard_html(stats)
        stats_json = json.dumps(stats, ensure_ascii=False)

        index_body = INDEX_BODY_TEMPLATE.format(
            folder_links="".join(folder_links),
            up_list_path=os.path.join(report_dir_name, '关注UP列表.html').replace('\\', '/'),
            dashboard_html=dashboard_html,
            stats_json=stats_json
        )
        chart_js_cdn = '<script src="https://cdn.jsdelivr.net/npm/chart.js@4"></script>'
        index_html = HTML_TEMPLATE.format(
            title="Bilibili 收藏夹报告", header="Bilibili 收藏夹报告", body=index_body,
            css_path=os.path.join(report_dir_name, 'assets/style.css').replace('\\', '/'),
            js_path=os.path.join(report_dir_name, 'assets/main.js').replace('\\', '/'),
            page_id="index", extra_head=chart_js_cdn
        )
        with open(os.path.join(project_root, 'index.html'), 'w', encoding='utf-8') as f:
            f.write(index_html)
        logging.info("Generated index.html")

        # --- Generate Individual Folder Pages ---
        for coll in collections:
            coll_id = coll['id']
            coll_name = coll['name']

            videos = get_videos_in_collection(conn, coll_id, include_unfav=True)

            video_cards = []
            for video in videos:
                bvid = video['bv_id']
                video_history = get_video_history(conn, bvid)

                # Check latest collection
                latest_coll_row = conn.execute("""
                    SELECT c.name FROM video_collection vc
                    JOIN collections c ON vc.collection_id = c.id
                    WHERE vc.bv_id = ? AND vc.is_active = 1
                    ORDER BY vc.fav_time DESC LIMIT 1
                """, (bvid,)).fetchone()
                latest_collection = latest_coll_row['name'] if latest_coll_row else coll_name

                status_class = ''
                if video['is_invalid']:
                    status_class = 'invalid'
                elif not video['is_active'] or latest_collection != coll_name:
                    status_class = 'moved'

                fav_time = video['fav_time'] or ''
                pub_time = video['publish_time'] or ''

                card_html = VIDEO_CARD_TEMPLATE.format(
                    title_attr=html_escape(video['title']),
                    title_html=html_escape(video['title']),
                    bv=html_escape(bvid),
                    cover_path=f"视频封面/{bvid}.jpg",
                    up_face_path=f"up头像/{video['up_mid']}.jpg",
                    up_name_attr=html_escape(video['up_name']),
                    up_name_html=html_escape(video['up_name']),
                    up_id=video['up_mid'],
                    play=video['play_count'], collect=video['collect_count'], danmaku=video['danmaku_count'],
                    duration=video['duration'] or '',
                    fav_time=fav_time, pub_time=pub_time,
                    fav_time_iso=fav_time.replace(' ', 'T') if fav_time else '',
                    pub_time_iso=pub_time.replace(' ', 'T') if pub_time else '',
                    history_json=html_escape(json.dumps(video_history, ensure_ascii=False)),
                    status_class=status_class
                )
                video_cards.append(card_html)

            folder_body = FOLDER_PAGE_BODY_TEMPLATE.format(video_cards="".join(video_cards))
            folder_html = HTML_TEMPLATE.format(
                title=f"收藏夹: {html_escape(coll_name)}", header=f"收藏夹: {html_escape(coll_name)}",
                body=folder_body, css_path="assets/style.css", js_path="assets/main.js",
                page_id="folder", extra_head=""
            )
            with open(os.path.join(report_path, f"fav-{html_escape(coll_name)}.html"), 'w', encoding='utf-8') as f:
                f.write(folder_html)
            logging.info(f"Generated page for {coll_name}")

    logging.info("---HTML Report Generation Finished---")
