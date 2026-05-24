# Bilibili 收藏夹爬取与展示工具

爬取你的 Bilibili 收藏夹数据，提供 PySide6 桌面应用进行浏览与管理，支持全局搜索、数据统计仪表盘、视频下载等功能。
基于[crawling-bilibili-personal-collect](https://github.com/cangkongman/crawling-bilibili-personal-collect)开发

> **AI 声明**：本仓库由 AI 辅助生成

## 功能特性

- **收藏夹爬取**：并发爬取所有收藏夹，支持增量更新（跳过无变化的收藏夹）
- **数据统计仪表盘**：收藏趋势、TOP UP 主、时长分布、失效/取消收藏视频一目了然
- **全局搜索**：按标题、BV 号、UP 主跨所有收藏夹搜索
- **分页 & 排序**：每页 50 条，支持按收藏时间、播放量、收藏量等 8 种排序
- **视频下载**：基于 yt-dlp 的交互式下载，支持整个收藏夹批量下载
- **SQLite 存储**：单文件数据库，查询高效，自动从旧 JSON 格式迁移
- **定时运行**：提供 BAT 脚本和 Windows 计划任务教程

## 环境要求

- **Python**：>= 3.10（推荐使用 Python 3.12）
- **操作系统**：Windows、Linux、macOS
- **外部依赖**：`yt-dlp` 需要可执行文件在系统 PATH 中，或在首次下载视频时自动安装

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

> 若需开发调试，安装开发依赖：
> ```bash
> pip install -r requirements-dev.txt
> ```

### 3. 启动桌面应用

```bash
python desktop.py
```

桌面应用是当前官方交互入口，用于查看数据、管理收藏夹和下载任务。

### 4. 运行爬取（可选，命令行/自动化）

```bash
python main.py
```

`main.py` 保持为无界面的 headless 自动化入口，首次运行会自动初始化 SQLite 数据库。如果存在旧的 JSON 数据，会自动迁移。

## 项目结构

```text
├── desktop.py          # PySide6 桌面应用入口
├── main.py             # 无界面 headless 自动化入口
├── database.py         # SQLite 数据库兼容性导出土层
├── run_crawler.bat     # 一键运行脚本（headless 爬取）
├── config.json         # 配置文件（含 Cookie 和可调参数）
├── bilibili_data.db    # SQLite 数据库（运行后生成）
├── requirements.txt    # 运行时依赖
├── requirements-dev.txt # 开发依赖
├── 定时任务教程.md      # Windows 计划任务设置指南
├── app/
│   ├── services/        # 业务服务层（爬取、下载、认证、配置等）
│   ├── repositories/    # 数据访问层（SQLite 操作封装）
│   ├── ui/              # PySide6 桌面 UI（页面、组件、主题）
│   ├── models/          # 数据模型与代理层
│   ├── workers/         # 长时间运行任务的 Qt Worker
│   └── theme.py         # 主题与样式定义
└── tests/               # pytest 测试套件
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

## 注意事项

- Cookie 过期后请在桌面应用中重新配置（设置页支持二维码扫码登录）
- 爬取日志保存在 `bilibili_crawler.log`
- `config.json` 包含敏感 Cookie 信息，请勿公开分享
- `yt-dlp` 下载视频时需确保可执行文件在 PATH 中，或允许程序自动安装
