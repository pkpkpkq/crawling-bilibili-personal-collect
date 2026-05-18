"""Centralized UI string constants for the Bilibili Collect application.

All user-facing Chinese strings are extracted here so that page files
import constants instead of hard-coding text.  No i18n / QTranslator —
single-language constants only.
"""


# ── Window ────────────────────────────────────────────────────────────
WINDOW_TITLE = "Bilibili 收藏管理"

# ── Navigation labels ─────────────────────────────────────────────────
NAV_DATA_OVERVIEW = "数据概览"
NAV_COLLECTION = "收藏夹"
NAV_GLOBAL_SEARCH = "全局搜索"
NAV_FOLLOWING_UP = "关注UP"
NAV_SETTINGS = "设置"
NAV_CRAWL = "爬取"
NAV_DOWNLOADS = "下载"

# ── Page titles ───────────────────────────────────────────────────────
PAGE_TITLE_DATA_OVERVIEW = "数据概览"
PAGE_TITLE_COLLECTION = "收藏夹"
PAGE_TITLE_GLOBAL_SEARCH = "全局搜索"
PAGE_TITLE_FOLLOWING_UP = "关注UP"
PAGE_TITLE_SETTINGS = "设置"
PAGE_TITLE_CRAWL_CENTER = "爬取中心"
PAGE_TITLE_DOWNLOAD_CENTER = "下载中心"

# ── Search / filter placeholders ──────────────────────────────────────
PLACEHOLDER_SEARCH_GENERAL = "搜索 标题/BV号/UP主..."
PLACEHOLDER_SEARCH_UP = "搜索UP主..."

# ── Sort options (collection page) ───────────────────────────────────
SORT_FAV_DESC = "收藏时间 (降序)"
SORT_FAV_ASC = "收藏时间 (升序)"
SORT_PUB_DESC = "发布时间 (降序)"
SORT_PUB_ASC = "发布时间 (升序)"
SORT_PLAY_DESC = "播放量 (降序)"
SORT_COLLECT_DESC = "收藏量 (降序)"
SORT_DANMAKU_DESC = "弹幕数 (降序)"
SORT_DURATION_DESC = "时长 (降序)"

# ── Sort options (search page) ───────────────────────────────────────
SORT_LATEST_FAV_DESC = "最新收藏时间 (降序)"
SORT_LATEST_FAV_ASC = "最新收藏时间 (升序)"
SORT_SEARCH_PLAY_DESC = "播放量 (降序)"
SORT_SEARCH_COLLECT_DESC = "收藏量 (降序)"

# ── Sort options (collection folder list) ────────────────────────────
SORT_FOLDER_NAME = "按名称排序"
SORT_FOLDER_COUNT_DESC = "按视频数量排序 (降序)"
SORT_FOLDER_COUNT_ASC = "按视频数量排序 (升序)"

# ── Crawl status labels ──────────────────────────────────────────────
CRAWL_STATUS_IDLE = "状态: 空闲"
CRAWL_STATUS_RUNNING = "状态: 爬取中..."
CRAWL_STATUS_COMPLETE = "状态: 爬取完成"
CRAWL_STATUS_FAILED = "状态: 爬取失败"
CRAWL_STATUS_CONFIG_ERROR = "状态: 配置加载失败"
CRAWL_STATUS_STOPPING = "状态: 停止请求中..."

# ── Download status labels ───────────────────────────────────────────
DOWNLOAD_STATUS_IDLE = "状态: 空闲"
DOWNLOAD_STATUS_DOWNLOADING = "状态: 下载中..."
DOWNLOAD_STATUS_COMPLETE = "状态: 下载完成"
DOWNLOAD_STATUS_FAILED = "状态: 下载失败"

# ── Crawl stat labels ────────────────────────────────────────────────
CRAWL_STAT_TOTAL = "总视频: 0"
CRAWL_STAT_NEW = "新增: 0"
CRAWL_STAT_INVALID = "失效: 0"
CRAWL_STAT_UNFAV = "取消收藏: 0"
CRAWL_STAT_DURATION = "耗时: 0.00s"

# ── Button labels ────────────────────────────────────────────────────
BTN_START_CRAWL = "开始爬取"
BTN_STOP = "停止"
BTN_CLEAR_LOG = "清空日志"
BTN_START_DOWNLOAD = "开始下载"
BTN_SAVE_SETTINGS = "保存设置"
BTN_GET_QR = "获取登录二维码"
BTN_CANCEL_QR = "取消扫码登录"
BTN_PREV_PAGE = "上一页"
BTN_NEXT_PAGE = "下一页"
BTN_BACK = "返回"
BTN_CLEAR_DATE_FILTER = "清除日期筛选"
BTN_REFRESH_COLLECTIONS = "刷新收藏夹"

# ── Empty-state text ─────────────────────────────────────────────────
EMPTY_NO_DATA = "暂无数据"
EMPTY_NO_HISTORY = "暂无历史记录"
EMPTY_NO_COLLECTIONS = "暂无收藏夹"
EMPTY_NO_VIDEOS = "暂无视频"

# ── Chart / list section titles ──────────────────────────────────────
CHART_COLLECTION_DISTRIBUTION = "收藏夹视频分布"
CHART_DURATION_DISTRIBUTION = "时长分布"
CHART_MONTHLY_TREND = "月度趋势"
LIST_TOP_UPS = "收藏最多UP主"
LIST_RECENT_INVALID = "近期失效视频"
LIST_RECENT_UNFAV = "近期取消收藏"

# ── Summary card titles ──────────────────────────────────────────────
SUMMARY_TOTAL_VIDEOS = "视频总数"
SUMMARY_TOTAL_COLLECTIONS = "收藏夹数"
SUMMARY_TOTAL_UPS = "UP主数"
SUMMARY_FOLLOWING_UPS = "关注UP"
SUMMARY_INVALID_VIDEOS = "失效视频"

# ── Filter / control labels ──────────────────────────────────────────
LABEL_FILTER_SORT = "筛选与排序"
LABEL_SEARCH = "搜索:"
LABEL_SORT = "排序:"
LABEL_CURRENT_ONLY = "仅显示当前有效视频"
LABEL_FAV_TIME = "收藏时间:"
LABEL_PUB_TIME = "发布时间:"
LABEL_MANUAL_COOKIE = "手动设置 Cookie:"
LABEL_QR_LOGIN = "扫码登录:"
LABEL_DATE_SEP = "-"

# ── Settings form labels ─────────────────────────────────────────────
SETTINGS_CRAWL_CONCURRENCY = "爬取并发数:"
SETTINGS_IMAGE_CONCURRENCY = "图片下载并发数:"
SETTINGS_PAGE_DELAY = "翻页延迟 (秒):"
SETTINGS_IMAGE_RETRY = "图片重试次数:"
SETTINGS_BACKUP_KEEP = "备份保留数:"
SETTINGS_INCREMENTAL_SYNC = "启用增量同步"

# ── Download labels ──────────────────────────────────────────────────
DL_MODE_LABEL = "下载模式:"
DL_QUALITY_LABEL = "画质:"
DL_OUTPUT_LABEL = "输出目录:"
DL_BV_LABEL = "BV 号:"
DL_COLLECTION_LABEL = "收藏夹:"
DL_USE_COOKIE = "使用 config.json 中的 Cookie（推荐）"

# ── Download mode options ────────────────────────────────────────────
DL_MODE_SINGLE = "下载单个视频（BV）"
DL_MODE_COLLECTION = "下载整个收藏夹"

# ── QR login status ──────────────────────────────────────────────────
QR_STATUS_READY = "就绪"
QR_STATUS_INITIALIZING = "正在初始化扫码登录..."
QR_STATUS_CANCELLING = "正在取消扫码登录..."
QR_STATUS_LOADING = "正在加载二维码..."
QR_CLICK_TO_GENERATE = "点击「获取登录二维码」生成二维码"

# ── Pagination format ────────────────────────────────────────────────
PAGINATION_FORMAT = "第 {current} 页 / 共 {total_pages} 页 ({total_items} 个视频)"

# ── Date picker special text ─────────────────────────────────────────
DATE_UNSELECTED = "未选择"

# ── History section ──────────────────────────────────────────────────
HISTORY_TITLE = "操作历史"
HISTORY_ACTION_ADD = "添加"
HISTORY_ACTION_REMOVE = "移除"
HISTORY_COLLECTION_LABEL = "收藏夹"

# ── Collection page ──────────────────────────────────────────────────
COLLECTION_DETAIL_TITLE = "收藏夹: {title}"
COLLECTION_VIDEO_COUNT = "{name} ({count} 个视频)"
COLLECTION_VIDEO_COUNT_ONLY = "{count} 个视频"
COLLECTION_CARD_META_LINE1 = "UP: {up_name} • 收藏: {fav_time} • 发布: {publish_time}"
COLLECTION_CARD_META_LINE2 = "播放: {play_count} • 收藏: {collect_count} • 弹幕: {danmaku_count} • 时长: {duration}"
COLLECTION_CARD_BADGE_INVALID = "已失效"
COLLECTION_CARD_BADGE_UNFAVORITED = "取消收藏"

# ── Search page ──────────────────────────────────────────────────────
SEARCH_SUBTITLE_FORMAT = "BV号: {bv_id}\nUP主: {up_name}\n最新收藏夹: {collection}\n最新收藏时间: {fav_time}"
SEARCH_UP_LINK_FORMAT = "UP主页: {up_name}"

# ── UP list page ─────────────────────────────────────────────────────
UP_CARD_LINK_TEXT = "查看主页"

# ── Download page helper strings ──────────────────────────────────────
DL_COLLECTIONS_AVAILABLE = "可下载收藏夹: {count}"
DL_BV_PLACEHOLDER = "例如 BV1xx411c7mD（也可不带 BV 前缀）"
DL_OUTPUT_PLACEHOLDER = "下载目录（默认 downloads）"
DL_CRAWL_LOG_PLACEHOLDER = "爬取日志会显示在这里..."
DL_DOWNLOAD_LOG_PLACEHOLDER = "下载任务日志会显示在这里..."
DL_COOKIE_PLACEHOLDER = "在此粘贴你的 SESSDATA 和 DedeUserID Cookie 字符串..."
