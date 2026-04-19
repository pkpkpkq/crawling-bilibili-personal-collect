@echo off
chcp 65001 >nul
title Bilibili 收藏夹爬取工具（桌面版）

echo ========================================
echo   Bilibili 收藏夹爬取工具（桌面版）
echo ========================================
echo.

cd /d "%~dp0"

:: 检查 Python 是否可用
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 Python，请先安装 Python 并将其添加到 PATH。
    exit /b 1
)

:: 启动桌面应用
echo [开始] 启动桌面应用...
echo.
python desktop.py

if errorlevel 1 (
    echo.
    echo [错误] 桌面应用启动失败，请查看控制台输出。
    exit /b 1
)

echo.
echo [完成] 桌面应用已退出！
exit /b 0
