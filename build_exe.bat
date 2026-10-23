@echo off
title Build Standalone Executable - Universal Media Downloader (Liquid Glass)
cd /d "%~dp0"
echo ========================================================
echo Building Liquid Glass Universal Media Downloader EXE...
echo ========================================================
python -m PyInstaller "Universal Media Downloader.spec" --noconfirm
if errorlevel 1 (
    echo.
    echo Build failed. Press any key to exit...
    pause >nul
    exit /b 1
)
echo.
echo ========================================================
echo Build complete! The executable is ready in the 'dist' folder:
echo dist\Universal Media Downloader.exe
echo ========================================================
pause
