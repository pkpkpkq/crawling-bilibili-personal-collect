function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

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
            resultsContainer.innerHTML = `<p>没有找到关于"${escapeHtml(query)}"的视频。</p>`;
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

            const coverPath = video.info.cover_path;
            const upFacePath = video.info.up_face_path;

            card.innerHTML = `
                <a class="cover-link" href="https://www.bilibili.com/video/${encodeURIComponent(video.bvid)}" target="_blank">
                    <img src="${coverPath}" alt="${escapeHtml(video.info.title)}" class="cover" loading="lazy">
                </a>
                <div class="info">
                    <h3 class="title"><a href="https://www.bilibili.com/video/${encodeURIComponent(video.bvid)}" target="_blank">${escapeHtml(video.info.title)}</a></h3>
                    <div class="meta">
                         <a href="https://space.bilibili.com/${encodeURIComponent(video.info.up_id)}" target="_blank">
                            <img src="${upFacePath}" alt="${escapeHtml(video.info.up_name)}" class="up-face" loading="lazy">
                        </a>
                        <a href="https://space.bilibili.com/${encodeURIComponent(video.info.up_id)}" target="_blank"><span class="up-name">${escapeHtml(video.info.up_name)}</span></a>
                    </div>
                    <div class="timestamps">
                        <p>最新收藏于: ${escapeHtml(video.latest_fav_time)}</p>
                        <p>位于: 《${escapeHtml(video.latest_collection)}》</p>
                        <p class="bv-id">${escapeHtml(video.bvid)}</p>
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
