@echo off
setlocal
title Build Windows Installer - FS Media Downloader
cd /d "%~dp0"

echo ========================================================
echo Step 1/2: Building Standalone Executable (PyInstaller)...
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
    echo [ERROR] Expected output 'dist\FS Media Downloader.exe' was not found!
    pause
    exit /b 1
)

echo.
echo ========================================================
echo Step 2/2: Compiling Windows Installer (Inno Setup 6)...
echo ========================================================

set "ISCC="
if exist "%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe" (
    set "ISCC=%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe"
    goto :RunCompiler
)
if exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" (
    set "ISCC=C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
    goto :RunCompiler
)
if exist "C:\Program Files\Inno Setup 6\ISCC.exe" (
    set "ISCC=C:\Program Files\Inno Setup 6\ISCC.exe"
    goto :RunCompiler
)

where ISCC.exe >nul 2>nul
if %errorlevel% equ 0 (
    set "ISCC=ISCC.exe"
    goto :RunCompiler
)

echo.
echo [ERROR] Inno Setup 6 compiler (ISCC.exe) was not found!
echo Please install Inno Setup 6 using: winget install JRSoftware.InnoSetup
pause
exit /b 1

:RunCompiler
echo Using Inno Setup compiler: "%ISCC%"
"%ISCC%" "installer.iss"
if errorlevel 1 (
    echo.
    echo [ERROR] Inno Setup installer compilation failed!
    pause
    exit /b 1
)

echo.
echo ========================================================
echo Build complete!
echo Standalone EXE: dist\FS Media Downloader.exe
echo Installer Setup: installer_output\FS_Media_Downloader_Setup_v1.0.0.exe
echo ========================================================
pause
