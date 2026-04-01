# Bilibili 收藏夹爬取与展示工具

爬取你的 Bilibili 收藏夹数据，生成可离线浏览的 HTML 报告，支持全局搜索、数据统计仪表盘、视频下载等功能。
原项目：[crawling-bilibili-personal-collect](https://github.com/cangkongman/crawling-bilibili-personal-collect)

> **AI 声明**：本仓库由 AI 辅助生成并经人工审核。

## 功能特性

- 📦 **收藏夹爬取**：并发爬取所有收藏夹，支持增量更新（跳过无变化的收藏夹）
- 📊 **数据统计仪表盘**：收藏趋势、TOP UP 主、时长分布、失效/取消收藏视频一目了然
- 🔍 **全局搜索**：按标题、BV 号、UP 主跨所有收藏夹搜索
- 📄 **分页 & 排序**：每页 50 条，支持按收藏时间、播放量、收藏量等 8 种排序
- 📥 **CSV 导出**：Python 端全量导出 + 页面内按筛选结果导出
- 🎬 **视频下载**：基于 yt-dlp 的交互式下载，支持整个收藏夹批量下载
- 🗄️ **SQLite 存储**：单文件数据库，查询高效，自动从旧 JSON 格式迁移
- ⏰ **定时运行**：提供 BAT 脚本和 Windows 计划任务教程

## 快速开始

### 1. 克隆项目

```bash
git clone https://github.com/pkpkpkq/crawling-bilibili-personal-collect.git
cd crawling-bilibili-personal-collect
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 获取 Cookie

```bash
python getcookie.py
```

支持扫码登录（推荐）或手动输入 Cookie，会自动生成 `config.json`。

### 4. 运行爬取

```bash
python main.py
```

首次运行会自动初始化 SQLite 数据库。如果存在旧的 JSON 数据，会自动迁移。

### 5. 查看报告

```bash
python server.py
```

浏览器打开 `http://localhost:8001` 即可查看报告。

## 项目结构

```
├── main.py             # 爬取主程序
├── database.py         # SQLite 数据库层
├── viewing.py          # HTML 报告生成
├── getcookie.py        # Cookie 获取工具
├── server.py           # 本地 HTTP 服务器
├── downloader.py       # 视频下载模块（需要 yt-dlp）
├── run_crawler.bat     # 一键运行脚本
├── config.json         # 配置文件（含 Cookie 和可调参数）
├── 定时任务教程.md      # Windows 计划任务设置指南
├── bilibili_data.db    # SQLite 数据库（运行后生成）
├── html_report/        # 生成的 HTML 报告
│   ├── assets/         # CSS + JS
│   ├── 视频封面/       # 视频封面图片
│   ├── up头像/         # UP 主头像
│   └── fav-*.html      # 各收藏夹页面
└── index.html          # 报告入口页
```

## 配置说明

`config.json` 中的 `settings` 字段可自定义：

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `max_workers_crawl` | 3 | 并发爬取收藏夹的线程数 |
| `max_workers_image` | 10 | 并发下载图片的线程数 |
| `page_delay` | 0.3 | 翻页请求间隔（秒） |
| `image_retry` | 3 | 图片下载失败重试次数 |
| `backup_keep_count` | 5 | 保留的旧数据备份数量 |
| `enable_incremental` | true | 启用增量爬取 |
| `csv_export` | true | 爬取完成后自动导出 CSV |

## 视频下载

```bash
pip install yt-dlp    # 首次需安装
python downloader.py
```

支持选择收藏夹批量下载或输入 BV 号单独下载，可选画质（best/1080p/720p/480p）。

## 注意事项

- Cookie 过期后请重新运行 `getcookie.py`
- 爬取日志保存在 `bilibili_crawler.log`
- `config.json` 包含敏感 Cookie 信息，请勿公开分享
