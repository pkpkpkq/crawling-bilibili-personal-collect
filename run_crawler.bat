@echo off
chcp 65001 >nul
title Bilibili Collection Crawler

echo ========================================
echo   Bilibili Collection Crawler
echo ========================================
echo.

cd /d "%~dp0"

:: Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo [Error] Python not found. Please install Python and add it to PATH.
    exit /b 1
)

echo [Start] Launching headless crawler...
echo.
python main.py

if errorlevel 1 (
    echo.
    echo [Error] Execution failed. Please check the console output.
    exit /b 1
)

echo.
echo [Done] Exited successfully!
exit /b 0
