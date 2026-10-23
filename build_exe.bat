@echo off
title Build Standalone Executable - FS Media Downloader (Liquid Glass)
cd /d "%~dp0"
echo ========================================================
echo Building Liquid Glass FS Media Downloader EXE...
echo ========================================================
python -m PyInstaller "FS Media Downloader.spec" --noconfirm
if errorlevel 1 (
    echo.
    echo Build failed. Press any key to exit...
    pause >nul
    exit /b 1
)
echo.
echo ========================================================
echo Build complete! The executable is ready in the 'dist' folder:
echo dist\FS Media Downloader.exe
echo ========================================================
pause
