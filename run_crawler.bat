@echo off
chcp 65001 >nul
title Bilibili 收藏夹爬取工具

echo ========================================
echo   Bilibili 收藏夹爬取工具
echo ========================================
echo.

cd /d "%~dp0"

:: 检查 Python 是否可用
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 Python，请先安装 Python 并将其添加到 PATH。
    exit /b 1
)

:: 检查 config.json 是否存在
if not exist "config.json" (
    echo [提示] 未找到 config.json，正在运行 Cookie 获取工具...
    python getcookie.py
    if errorlevel 1 (
        echo [错误] Cookie 获取失败。
        exit /b 1
    )
)

:: 运行主爬取程序（保留 headless 自动化入口）
echo [开始] 运行爬取程序...
echo.
python main.py

if errorlevel 1 (
    echo.
    echo [错误] 爬取过程中出现错误，请查看 bilibili_crawler.log
    exit /b 1
)

echo.
echo [完成] 爬取成功！
exit /b 0
