import os
import sys
import re
import json
import shutil
import zipfile
import io
import subprocess
import requests

# Single source of truth for the application version
APP_VERSION = "1.0.0"

GITHUB_REPO = "Fahad-Shabbir/Universal-Media-Downloader"
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
    """
    url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
    headers = {
        'User-Agent': f'FSMediaDownloader/{APP_VERSION}',
        'Accept': 'application/vnd.github.v3+json'
    }
    try:
        resp = requests.get(url, timeout=10, headers=headers)
        if resp.status_code == 404:
            # No releases published yet on GitHub repo
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
        tag_name = data.get('tag_name', '')
        clean_tag = tag_name.lstrip('vV')
        has_update = parse_version(clean_tag) > parse_version(APP_VERSION)

        assets = data.get('assets', [])
        exe_asset = None
        for a in assets:
            if a.get('name', '').lower().endswith('.exe'):
                exe_asset = a
                break

        asset_url = exe_asset.get('browser_download_url') if exe_asset else data.get('html_url')
        asset_name = exe_asset.get('name', f'FS.Media.Downloader.v{clean_tag}.exe') if exe_asset else ''
        asset_size = exe_asset.get('size', 0) if exe_asset else 0

        return {
            "update_available": has_update,
            "current": APP_VERSION,
            "latest": clean_tag,
            "tag_name": tag_name,
            "release_name": data.get('name', tag_name),
            "notes": data.get('body', ''),
            "asset_url": asset_url,
            "asset_name": asset_name,
            "size_mb": round(asset_size / (1024 * 1024), 2) if asset_size else None,
            "html_url": data.get('html_url', ''),
            "error": None
        }
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
                # If some files are momentarily locked, copy over them
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

def download_app_asset(asset_url, asset_name="", progress_cb=None):
    """
    Downloads the GitHub .exe release asset to the user's Downloads folder.
    """
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
            # PyInstaller exe
            exe_path = sys.executable
            subprocess.Popen([exe_path] + sys.argv[1:], creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == 'win32' else 0)
        else:
            # Python script
            subprocess.Popen([sys.executable] + sys.argv)
    except Exception as e:
        print(f"Error restarting app: {e}")
    os._exit(0)
