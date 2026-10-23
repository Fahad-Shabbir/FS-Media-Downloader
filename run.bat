@echo off
title Universal Media Downloader - by Fahad Shabbir
cd /d "%~dp0"

:: Check if standalone EXE exists in dist folder
if exist "dist\Universal Media Downloader.exe" (
    start "" "dist\Universal Media Downloader.exe"
    exit /b
)
if exist "dist\YouTube Media Downloader.exe" (
    start "" "dist\YouTube Media Downloader.exe"
    exit /b
)

:: Otherwise check if python is installed
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo ========================================================
    echo Python is not installed on this system.
    echo.
    echo Please use the pre-built standalone executable:
    echo "dist\Universal Media Downloader.exe"
    echo ========================================================
    echo.
    pause
    exit /b 1
)

python app.py
if errorlevel 1 (
    echo.
    echo An error occurred. Press any key to exit...
    pause >nul
)
