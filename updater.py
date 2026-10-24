import os
import sys
import re
import json
import shutil
import zipfile
import io
import subprocess
import hashlib
import requests

# Single source of truth for the application version
APP_VERSION = "1.0.1"

GITHUB_REPO = "Fahad-Shabbir/FS-Media-Downloader"
PYPI_URL = "https://pypi.org/pypi/yt-dlp/json"


def get_local_appdata_dir():
    """Returns %LOCALAPPDATA%\\FSMediaDownloader (migrates from legacy UniversalMediaDownloader if present)."""
    base = os.environ.get('LOCALAPPDATA', os.path.expanduser('~\\AppData\\Local'))
    new_dir = os.path.join(base, 'FSMediaDownloader')
    old_dir = os.path.join(base, 'UniversalMediaDownloader')

    # One-time migration from old cache directory if it exists
    if os.path.isdir(old_dir) and not os.path.isdir(new_dir):
        try:
            shutil.copytree(old_dir, new_dir)
        except Exception:
            pass

    return new_dir


def get_ytdlp_update_dir():
    """Returns %LOCALAPPDATA%\\FSMediaDownloader\\yt_dlp_update."""
    return os.path.join(get_local_appdata_dir(), 'yt_dlp_update')


def is_ytdlp_custom():
    """Checks if an overridden yt-dlp package exists in the update directory."""
    d = get_ytdlp_update_dir()
    return os.path.isdir(os.path.join(d, 'yt_dlp')) and os.path.isfile(os.path.join(d, 'yt_dlp', '__init__.py'))


def setup_ytdlp_override():
    """
    At app startup, BEFORE importing yt_dlp or downloader:
    Check whether %LOCALAPPDATA%\\FSMediaDownloader\\yt_dlp_update\\yt_dlp exists,
    and if so, insert that folder at sys.path[0] so the updated yt-dlp overrides the bundled one.
    """
    target_dir = get_ytdlp_update_dir()
    init_file = os.path.join(target_dir, 'yt_dlp', '__init__.py')
    if os.path.isfile(init_file):
        if target_dir not in sys.path:
            sys.path.insert(0, target_dir)
        return True
    return False


def is_directory_writable(dir_path):
    """Tests if a directory has write permissions by creating and removing a temp file."""
    if not dir_path or not os.path.isdir(dir_path):
        return False
    test_file = os.path.join(dir_path, f".write_test_{os.getpid()}.tmp")
    try:
        with open(test_file, 'w') as f:
            f.write('write_test')
        os.remove(test_file)
        return True
    except Exception:
        return False


def parse_version(v_str):
    """Parses version strings like '2026.10.21' or 'v1.0.0' for accurate comparison."""
    if not v_str:
        return (0,)
    clean = re.sub(r'^[vV]', '', str(v_str).strip())
    try:
        from packaging import version
        return version.parse(clean)
    except Exception:
        pass

    # Fallback numerical tuple
    tokens = []
    for piece in re.split(r'[-._]', clean):
        try:
            tokens.append(int(piece))
        except ValueError:
            tokens.append(piece)
    return tuple(tokens)


def get_installed_versions():
    """Returns current App version, yt-dlp version, and whether yt-dlp is an override."""
    try:
        import yt_dlp
        ytdlp_ver = getattr(yt_dlp.version, '__version__', 'Unknown')
    except Exception:
        ytdlp_ver = 'Unknown'

    return {
        "app_version": APP_VERSION,
        "ytdlp_version": ytdlp_ver,
        "ytdlp_is_custom": is_ytdlp_custom()
    }


def check_ytdlp_update():
    """
    Queries PyPI for the latest yt-dlp version and checks if an update is available.
    """
    current_ver = get_installed_versions()["ytdlp_version"]
    try:
        resp = requests.get(
            PYPI_URL,
            timeout=10,
            headers={'User-Agent': f'FSMediaDownloader/{APP_VERSION}'}
        )
        if resp.status_code != 200:
            return {
                "update_available": False,
                "current": current_ver,
                "latest": current_ver,
                "error": f"PyPI responded with status {resp.status_code}"
            }
        
        data = resp.json()
        latest_ver = data.get('info', {}).get('version', '')
        urls = data.get('urls', [])
        whl_urls = [u for u in urls if u.get('packagetype') == 'bdist_wheel']
        if not whl_urls:
            return {
                "update_available": False,
                "current": current_ver,
                "latest": latest_ver,
                "error": "No .whl package found on PyPI"
            }

        whl_url = whl_urls[0]['url']
        whl_size = whl_urls[0].get('size', 0)
        has_update = parse_version(latest_ver) > parse_version(current_ver)

        return {
            "update_available": has_update,
            "current": current_ver,
            "latest": latest_ver,
            "wheel_url": whl_url,
            "size_mb": round(whl_size / (1024 * 1024), 2) if whl_size else None,
            "error": None
        }
    except requests.exceptions.RequestException:
        return {
            "update_available": False,
            "current": current_ver,
            "latest": current_ver,
            "error": "Unable to connect to PyPI. Please check your internet connection."
        }
    except Exception as e:
        return {
            "update_available": False,
            "current": current_ver,
            "latest": current_ver,
            "error": str(e)
        }


def check_app_update():
    """
    Calls the GitHub Releases API to check for new app versions.
    Extracts standalone exe asset and SHA-256 digest if available.
    """
    url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
    headers = {
        'User-Agent': f'FSMediaDownloader/{APP_VERSION}',
        'Accept': 'application/vnd.github.v3+json'
    }
    try:
        resp = requests.get(url, timeout=10, headers=headers)
        if resp.status_code == 404:
            return {
                "update_available": False,
                "current": APP_VERSION,
                "latest": APP_VERSION,
                "message": "You're up to date.",
                "error": None
            }
        elif resp.status_code == 403:
            return {
                "update_available": False,
                "current": APP_VERSION,
                "latest": APP_VERSION,
                "error": "GitHub API rate limit exceeded. Please try again later."
            }
        elif resp.status_code != 200:
            return {
                "update_available": False,
                "current": APP_VERSION,
                "latest": APP_VERSION,
                "error": f"GitHub returned status {resp.status_code}"
            }

        data = resp.json()
        return _process_release_data(data)
    except requests.exceptions.RequestException:
        return {
            "update_available": False,
            "current": APP_VERSION,
            "latest": APP_VERSION,
            "error": "Unable to connect to GitHub. Please check your internet connection."
        }
    except Exception as e:
        return {
            "update_available": False,
            "current": APP_VERSION,
            "latest": APP_VERSION,
            "error": str(e)
        }


def _process_release_data(data):
    """Processes release JSON data and inspects writable permissions."""
    tag_name = data.get('tag_name', '')
    clean_tag = tag_name.lstrip('vV')
    has_update = parse_version(clean_tag) > parse_version(APP_VERSION)

    assets = data.get('assets', [])
    
    # Prioritize standalone portable .exe (exclude setup/installer if possible)
    exe_asset = None
    portable_candidates = [
        a for a in assets
        if a.get('name', '').lower().endswith('.exe') and 'setup' not in a.get('name', '').lower()
    ]
    if portable_candidates:
        exe_asset = portable_candidates[0]
    else:
        all_exes = [a for a in assets if a.get('name', '').lower().endswith('.exe')]
        if all_exes:
            exe_asset = all_exes[0]

    asset_url = exe_asset.get('browser_download_url') if exe_asset else data.get('html_url')
    asset_name = exe_asset.get('name', f'FS.Media.Downloader.v{clean_tag}.exe') if exe_asset else ''
    asset_size = exe_asset.get('size', 0) if exe_asset else 0

    # Look for SHA256 digest in release body
    body = data.get('body', '') or ''
    expected_sha256 = None
    sha_match = re.search(r'(?:sha256|sha-256|hash)[\s:=]+([a-fA-F0-9]{64})', body, re.IGNORECASE)
    if sha_match:
        expected_sha256 = sha_match.group(1).lower()

    # Check if target executable folder is writable
    is_frozen = getattr(sys, 'frozen', False)
    if is_frozen:
        exe_dir = os.path.dirname(os.path.abspath(sys.executable))
        can_auto_update = is_directory_writable(exe_dir)
    else:
        can_auto_update = True  # Dev mode

    return {
        "update_available": has_update,
        "current": APP_VERSION,
        "latest": clean_tag,
        "tag_name": tag_name,
        "release_name": data.get('name', tag_name),
        "notes": body,
        "asset_url": asset_url,
        "asset_name": asset_name,
        "size_bytes": asset_size,
        "size_mb": round(asset_size / (1024 * 1024), 2) if asset_size else None,
        "expected_sha256": expected_sha256,
        "html_url": data.get('html_url', f"https://github.com/{GITHUB_REPO}/releases/latest"),
        "is_frozen": is_frozen,
        "can_auto_update": can_auto_update,
        "error": None
    }


def perform_ytdlp_update(progress_cb=None):
    """
    Downloads the latest yt-dlp wheel (.whl) from PyPI and extracts it to
    %LOCALAPPDATA%\\FSMediaDownloader\\yt_dlp_update\\.
    """
    check_info = check_ytdlp_update()
    if check_info.get('error'):
        return {"error": check_info['error']}

    whl_url = check_info.get('wheel_url')
    if not whl_url:
        return {"error": "Could not locate yt-dlp wheel package."}

    latest_ver = check_info.get('latest')

    try:
        if progress_cb:
            progress_cb(10, "Connecting to PyPI...")

        resp = requests.get(whl_url, stream=True, timeout=30, headers={'User-Agent': f'FSMediaDownloader/{APP_VERSION}'})
        resp.raise_for_status()
        total_len = int(resp.headers.get('content-length', 0))

        buffer = bytearray()
        downloaded = 0
        for chunk in resp.iter_content(chunk_size=65536):
            if chunk:
                buffer.extend(chunk)
                downloaded += len(chunk)
                if total_len > 0 and progress_cb:
                    pct = 10 + int((downloaded / total_len) * 70)
                    down_mb = downloaded / (1024 * 1024)
                    tot_mb = total_len / (1024 * 1024)
                    progress_cb(pct, f"Downloading yt-dlp ({down_mb:.1f} / {tot_mb:.1f} MB)...")

        if progress_cb:
            progress_cb(85, "Extracting updated yt-dlp engine...")

        target_dir = get_ytdlp_update_dir()
        temp_dir = target_dir + "_temp"

        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir, ignore_errors=True)
        os.makedirs(temp_dir, exist_ok=True)

        with zipfile.ZipFile(io.BytesIO(buffer)) as z:
            z.extractall(temp_dir)

        # Integrity verification
        if not os.path.isfile(os.path.join(temp_dir, 'yt_dlp', '__init__.py')):
            return {"error": "Downloaded wheel is invalid (missing yt_dlp module)."}

        # Replace target directory
        if os.path.exists(target_dir):
            try:
                shutil.rmtree(target_dir)
            except Exception:
                for root, _, files in os.walk(temp_dir):
                    rel = os.path.relpath(root, temp_dir)
                    dest_sub = os.path.join(target_dir, rel)
                    os.makedirs(dest_sub, exist_ok=True)
                    for f in files:
                        try:
                            shutil.copy2(os.path.join(root, f), os.path.join(dest_sub, f))
                        except Exception:
                            pass
                shutil.rmtree(temp_dir, ignore_errors=True)
                if progress_cb:
                    progress_cb(100, f"Updated to v{latest_ver}")
                return {"success": True, "version": latest_ver}

        shutil.move(temp_dir, target_dir)

        if progress_cb:
            progress_cb(100, f"Updated to v{latest_ver}")

        return {"success": True, "version": latest_ver}
    except Exception as e:
        return {"error": str(e)}


def download_and_verify_app_update(asset_url, asset_name="", expected_size=None, expected_sha256=None, progress_cb=None):
    """
    Downloads the GitHub .exe release asset to a temp folder, reporting progress and
    verifying both size and SHA-256 digest (if provided).
    """
    temp_dir = os.path.join(os.environ.get('TEMP', os.path.expanduser('~\\AppData\\Local\\Temp')), 'FSMediaDownloaderUpdate')
    try:
        os.makedirs(temp_dir, exist_ok=True)
    except Exception as e:
        return {"error": f"Failed to create temp directory: {e}"}

    if not asset_name:
        asset_name = "FS_Media_Downloader_new.exe"
    
    clean_name = re.sub(r'[^\w\.-]', '_', asset_name)
    target_path = os.path.join(temp_dir, f"update_{os.getpid()}_{clean_name}")

    try:
        if progress_cb:
            progress_cb(5, "Connecting to download server...")

        # If asset_url is a local file (for testing)
        if os.path.isfile(asset_url):
            if progress_cb:
                progress_cb(50, "Staging local test package...")
            shutil.copy2(asset_url, target_path)
            total_len = os.path.getsize(target_path)
            hasher = hashlib.sha256()
            with open(target_path, 'rb') as f:
                while chunk := f.read(131072):
                    hasher.update(chunk)
            actual_sha = hasher.hexdigest().lower()
            if progress_cb:
                progress_cb(100, "Package verified!")
            return {"success": True, "file_path": target_path, "sha256": actual_sha}

        headers = {'User-Agent': f'FSMediaDownloader/{APP_VERSION}'}
        resp = requests.get(asset_url, stream=True, timeout=60, headers=headers)
        resp.raise_for_status()

        content_length = int(resp.headers.get('content-length', 0))
        target_size = expected_size or content_length

        downloaded = 0
        hasher = hashlib.sha256()

        with open(target_path, 'wb') as f:
            for chunk in resp.iter_content(chunk_size=131072):
                if chunk:
                    f.write(chunk)
                    hasher.update(chunk)
                    downloaded += len(chunk)
                    if progress_cb:
                        pct = int((downloaded / target_size) * 90) if target_size > 0 else 50
                        pct = min(pct, 95)
                        down_mb = downloaded / (1024 * 1024)
                        tot_mb = target_size / (1024 * 1024) if target_size > 0 else down_mb
                        progress_cb(pct, f"Downloading update ({down_mb:.1f} / {tot_mb:.1f} MB)...")

        # Size Verification
        if target_size > 0 and downloaded < (target_size * 0.95):  # allow small compression variance if dynamic
            raise ValueError(f"Downloaded file incomplete ({downloaded} / {target_size} bytes)")

        # SHA-256 Verification (if provided)
        actual_sha = hasher.hexdigest().lower()
        if expected_sha256 and expected_sha256.lower() != actual_sha:
            try:
                os.remove(target_path)
            except Exception:
                pass
            raise ValueError(f"SHA-256 digest mismatch! Expected {expected_sha256}, got {actual_sha}")

        if progress_cb:
            progress_cb(100, "Update downloaded and verified!")

        return {
            "success": True,
            "file_path": target_path,
            "sha256": actual_sha,
            "size_bytes": downloaded
        }
    except Exception as e:
        return {"error": str(e)}


def apply_portable_update(new_exe_path):
    """
    Relaunches the app through a helper batch script that waits for the app process to exit,
    backs up current exe as 'FS Media Downloader.old', swaps in the new exe, launches it,
    and cleans up. If replacement fails, it restores the backup and shows an error.
    """
    if not getattr(sys, 'frozen', False):
        return {
            "error": "Running in development mode (from source). Standalone replacement skipped.",
            "dev_mode": True,
            "file_path": new_exe_path
        }

    current_exe = os.path.abspath(sys.executable)
    exe_dir = os.path.dirname(current_exe)

    if not is_directory_writable(exe_dir):
        return {
            "error": "The application folder is read-only or lacks administrative permissions. Please download the release manually.",
            "read_only": True
        }

    if not os.path.isfile(new_exe_path):
        return {"error": f"Downloaded update file not found at {new_exe_path}"}

    pid = os.getpid()
    temp_dir = os.environ.get('TEMP', os.path.expanduser('~\\AppData\\Local\\Temp'))
    bat_path = os.path.join(temp_dir, f"fs_update_worker_{pid}.bat")

    # Helper batch script that runs independently after this process exits
    bat_content = f"""@echo off
setlocal
set "PID={pid}"
set "NEW_EXE={new_exe_path}"
set "TARGET_EXE={current_exe}"
set "OLD_EXE={current_exe}.old"

:: 1. Wait for the app process to terminate
:WaitLoop
ping 127.0.0.1 -n 2 >nul
tasklist /fi "PID eq %PID%" 2>nul | findstr /i "%PID%" >nul
if %errorlevel% equ 0 goto :WaitLoop

:: 2. Safety pause for OS file lock release
ping 127.0.0.1 -n 2 >nul

:: 3. Clean old backup if it was left from previous update
if exist "%OLD_EXE%" del /f /q "%OLD_EXE%" >nul 2>nul

:: 4. Rename current running exe to .old
move /y "%TARGET_EXE%" "%OLD_EXE%" >nul 2>nul
if errorlevel 1 goto :RestoreAndFail

:: 5. Move new executable into place
move /y "%NEW_EXE%" "%TARGET_EXE%" >nul 2>nul
if errorlevel 1 goto :RestoreAndFail

:: 6. Launch the updated application
start "" "%TARGET_EXE%"

:: 7. Wait briefly and delete old backup once new exe is running
ping 127.0.0.1 -n 4 >nul
if exist "%OLD_EXE%" del /f /q "%OLD_EXE%" >nul 2>nul
goto :CleanSelf

:RestoreAndFail
if not exist "%TARGET_EXE%" (
    if exist "%OLD_EXE%" move /y "%OLD_EXE%" "%TARGET_EXE%" >nul 2>nul
)
powershell -Command "[System.Reflection.Assembly]::LoadWithPartialName('System.Windows.Forms') | Out-Null; [System.Windows.Forms.MessageBox]::Show('Update failed: Unable to replace the executable file. Antivirus or file lock may have blocked replacement. The original version was restored.', 'FS Media Downloader - Update Error', 0, 16)" >nul 2>nul
if exist "%TARGET_EXE%" start "" "%TARGET_EXE%"

:CleanSelf
(goto) 2>nul & del /f /q "%~f0"
"""

    try:
        with open(bat_path, "w", encoding="utf-8") as f:
            f.write(bat_content)

        # Launch detached batch script (CREATE_NO_WINDOW | CREATE_NEW_PROCESS_GROUP)
        flags = 0x08000000 | 0x00000200
        subprocess.Popen(["cmd.exe", "/c", bat_path], creationflags=flags)

        # Terminate current app immediately so the helper can perform the replacement
        os._exit(0)
    except Exception as e:
        return {"error": f"Failed to execute update helper: {e}"}


def download_app_asset(asset_url, asset_name="", progress_cb=None):
    """Fallback manual download into user's Downloads folder."""
    dest_dir = os.path.join(os.path.expanduser("~"), "Downloads")
    if not os.path.isdir(dest_dir):
        dest_dir = os.getcwd()

    if not asset_name:
        asset_name = "FS Media Downloader.exe"

    base, ext = os.path.splitext(asset_name)
    target_path = os.path.join(dest_dir, asset_name)
    counter = 1
    while os.path.exists(target_path):
        target_path = os.path.join(dest_dir, f"{base} ({counter}){ext}")
        counter += 1

    try:
        if progress_cb:
            progress_cb(5, "Connecting to GitHub...")

        resp = requests.get(asset_url, stream=True, timeout=60, headers={'User-Agent': f'FSMediaDownloader/{APP_VERSION}'})
        resp.raise_for_status()
        total_len = int(resp.headers.get('content-length', 0))

        downloaded = 0
        with open(target_path, 'wb') as f:
            for chunk in resp.iter_content(chunk_size=131072):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_len > 0 and progress_cb:
                        pct = int((downloaded / total_len) * 100)
                        down_mb = downloaded / (1024 * 1024)
                        tot_mb = total_len / (1024 * 1024)
                        progress_cb(pct, f"Downloading v{asset_name} ({down_mb:.1f} / {tot_mb:.1f} MB)...")

        if progress_cb:
            progress_cb(100, "Download complete!")

        return {"success": True, "file_path": target_path}
    except Exception as e:
        return {"error": str(e)}


def open_file_location(path):
    """Selects and reveals the file in Windows File Explorer."""
    try:
        if os.path.isfile(path):
            subprocess.Popen(f'explorer /select,"{os.path.abspath(path)}"')
            return True
        elif os.path.isdir(path):
            os.startfile(path)
            return True
    except Exception as e:
        print(f"Error opening explorer location: {e}")
    return False


def restart_app():
    """Relaunches the current application and cleanly terminates the old process."""
    try:
        if getattr(sys, 'frozen', False):
            exe_path = sys.executable
            subprocess.Popen([exe_path] + sys.argv[1:], creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == 'win32' else 0)
        else:
            subprocess.Popen([sys.executable] + sys.argv)
    except Exception as e:
        print(f"Error restarting app: {e}")
    os._exit(0)
