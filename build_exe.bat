@echo off
setlocal enabledelayedexpansion
title Build Standalone Executable - FS Media Downloader
cd /d "%~dp0"

echo ========================================================
echo FS Media Downloader - Build & Release Automation
echo ========================================================
echo.

:: Prompt for version bump (P=Patch, m=Minor, M=Major, N=None) with 5-second timeout defaulting to Patch
choice /C PmMjN /CS /T 5 /D P /M "Version bump? [P]atch / [m]inor / [M]ajor / [N]one"
if errorlevel 5 (
    set "BUMP_TYPE=none"
) else if errorlevel 4 (
    set "BUMP_TYPE=major"
) else if errorlevel 3 (
    set "BUMP_TYPE=major"
) else if errorlevel 2 (
    set "BUMP_TYPE=minor"
) else (
    set "BUMP_TYPE=patch"
)

echo.
echo Selected bump type: !BUMP_TYPE!
echo.

set "SUMMARY="
set /p SUMMARY="Release summary note (optional, press Enter to skip): "

echo.
python bump_version.py !BUMP_TYPE! "!SUMMARY!"
if errorlevel 1 (
    echo.
    echo [ERROR] Version bump failed!
    pause
    exit /b 1
)

set /p CURRENT_VER=<current_version.txt
if exist current_version.txt del current_version.txt >nul 2>nul

echo.
echo ========================================================
echo Building FS Media Downloader v!CURRENT_VER! (PyInstaller)...
echo ========================================================
python -m PyInstaller "FS Media Downloader.spec" --noconfirm
if errorlevel 1 (
    echo.
    echo [ERROR] PyInstaller build failed!
    pause
    exit /b 1
)

if not exist "dist\FS Media Downloader.exe" (
    echo.
    echo [ERROR] Expected binary 'dist\FS Media Downloader.exe' was not found!
    pause
    exit /b 1
)

:: Create versioned release copy
copy /y "dist\FS Media Downloader.exe" "dist\FS.Media.Downloader.v!CURRENT_VER!.exe" >nul
if errorlevel 1 (
    echo [WARNING] Could not create versioned copy.
) else (
    echo Created versioned copy: dist\FS.Media.Downloader.v!CURRENT_VER!.exe
)

echo.
echo ========================================================
echo Build complete for v!CURRENT_VER%!
echo - Standalone: dist\FS Media Downloader.exe
echo - Versioned:  dist\FS.Media.Downloader.v!CURRENT_VER!.exe
echo ========================================================
pause
