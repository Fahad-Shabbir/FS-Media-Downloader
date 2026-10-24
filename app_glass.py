import os
import sys

# Ensure yt-dlp update override is registered before downloader / yt_dlp
import updater
updater.setup_ytdlp_override()

import shutil
import threading
import json
import webview
import downloader

class DownloaderApi:
    def __init__(self):
        self.window = None
        self.cancel_event = threading.Event()
        self.pause_event = threading.Event()
        self.pause_event.set()

    def set_window(self, window):
        self.window = window

    def pause_download(self):
        """Pauses the active fragment download."""
        self.pause_event.clear()
        return {"paused": True}

    def resume_download(self):
        """Resumes the paused download."""
        self.pause_event.set()
        return {"resumed": True}

    def cancel_download(self):
        """Aborts and cancels the current download immediately."""
        self.cancel_event.set()
        self.pause_event.set() # Unblock if paused so thread can exit immediately
        return {"cancelled": True}

    def get_default_download_dir(self):
        """Returns the system Downloads folder or current working directory."""
        downloads = os.path.join(os.path.expanduser("~"), "Downloads")
        if os.path.isdir(downloads):
            return downloads
        return os.getcwd()

    def select_directory(self):
        """Opens a native Windows folder selector."""
        if not self.window:
            return ""
        try:
            result = self.window.create_file_dialog(webview.FOLDER_DIALOG)
            if result and len(result) > 0:
                return result[0]
        except Exception as e:
            print(f"Error opening folder dialog: {e}")
        return ""

    def open_directory(self, path):
        """Opens the specified directory in Windows File Explorer."""
        if not path or not os.path.exists(path):
            path = self.get_default_download_dir()
        try:
            os.startfile(path)
            return True
        except Exception as e:
            print(f"Error opening explorer: {e}")
            return False

    def check_cookies(self):
        """Checks if a valid cookies.txt file is present."""
        return downloader.get_cookie_file() is not None

    def import_cookies(self):
        """Prompts user to select cookies.txt and copies it to the app folder."""
        if not self.window:
            return {"error": "Window not initialized"}
        try:
            result = self.window.create_file_dialog(
                webview.OPEN_DIALOG,
                file_types=('Text files (*.txt)', 'All files (*.*)')
            )
            if not result or len(result) == 0:
                return {"error": "No file chosen"}
            
            src = result[0]
            dest = os.path.join(os.getcwd(), 'cookies.txt')
            shutil.copyfile(src, dest)
            return {"success": True, "path": dest}
        except Exception as e:
            return {"error": str(e)}

    def get_clipboard_text(self):
        """Safely gets text from clipboard using tkinter."""
        try:
            import tkinter as tk
            root = tk.Tk()
            root.withdraw()
            text = root.clipboard_get()
            root.destroy()
            return text
        except Exception:
            return ""

    def analyze_url(self, url):
        """Analyzes a single media link across YouTube, Twitter, FB, IG, etc."""
        if not url or not url.strip():
            return {"error": "URL cannot be empty"}
        try:
            info = downloader.extract_video_info(url.strip())
            return info
        except Exception as e:
            return {"error": str(e)}

    def analyze_bulk(self, raw_text):
        """Analyzes a playlist link or multiple URLs."""
        if not raw_text or not raw_text.strip():
            return {"error": "No text provided"}
        try:
            info = downloader.extract_bulk_or_playlist_info(raw_text.strip())
            return info
        except Exception as e:
            return {"error": str(e)}

    def download_single(self, url, media_type, quality, output_dir, is_turbo):
        """Downloads a single video or audio file with progress callbacks."""
        if not output_dir or not os.path.isdir(output_dir):
            output_dir = self.get_default_download_dir()

        threads = 8 if is_turbo else 1
        self.cancel_event.clear()
        self.pause_event.set()

        def progress_hook(d):
            if not self.window:
                return
            status = d.get('status')
            if status == 'downloading':
                downloaded = d.get('downloaded_bytes', 0)
                total = d.get('total_bytes') or d.get('total_bytes_estimate') or 0
                
                percent = 0
                if total > 0:
                    percent = (downloaded / total) * 100
                elif '_percent_str' in d:
                    try:
                        clean_p = d['_percent_str'].replace('%', '').strip()
                        percent = float(clean_p)
                    except Exception:
                        percent = 0

                speed_str = d.get('_speed_str', '-- MB/s')
                eta_str = d.get('_eta_str', '--')
                
                down_mb = f"{downloaded / (1024 * 1024):.1f} MB"
                total_mb = f"{total / (1024 * 1024):.1f} MB" if total > 0 else "Unknown"

                js_code = (
                    f"window.update_progress({percent:.1f}, "
                    f"{json.dumps(speed_str)}, "
                    f"{json.dumps(eta_str)}, "
                    f"{json.dumps(down_mb)}, "
                    f"{json.dumps(total_mb)}, "
                    f"'Downloading...');"
                )
                try:
                    self.window.evaluate_js(js_code)
                except Exception:
                    pass
            elif status == 'finished':
                try:
                    self.window.evaluate_js("window.update_progress(100, '', '', '', '', 'Processing & Finalizing...');")
                except Exception:
                    pass

        try:
            res = downloader.download_media(
                url=url,
                media_type=media_type,
                quality_option=quality,
                output_path=output_dir,
                progress_hook=progress_hook,
                turbo_threads=threads,
                cancel_event=self.cancel_event,
                pause_event=self.pause_event
            )
            if res and res.get('cancelled'):
                return {"cancelled": True}
            return {"success": True}
        except Exception as e:
            if self.cancel_event.is_set():
                return {"cancelled": True}
            return {"error": str(e)}

    def download_bulk(self, items, media_type, quality, output_dir, is_turbo):
        """Downloads a list of queued videos/audio items with overall & item status."""
        if not output_dir or not os.path.isdir(output_dir):
            output_dir = self.get_default_download_dir()

        threads = 8 if is_turbo else 1
        self.cancel_event.clear()
        self.pause_event.set()

        def overall_hook(idx, total, title, status):
            if not self.window:
                return
            js = f"window.update_bulk_progress({idx}, {total}, {json.dumps(title)}, {json.dumps(status)});"
            try:
                self.window.evaluate_js(js)
            except Exception:
                pass

        def item_hook(d):
            if not self.window:
                return
            status = d.get('status')
            if status == 'downloading':
                downloaded = d.get('downloaded_bytes', 0)
                total = d.get('total_bytes') or d.get('total_bytes_estimate') or 0
                percent = (downloaded / total * 100) if total > 0 else 0
                speed_str = d.get('_speed_str', '')
                eta_str = d.get('_eta_str', '')
                down_mb = f"{downloaded / (1024 * 1024):.1f} MB"
                total_mb = f"{total / (1024 * 1024):.1f} MB" if total > 0 else ""
                
                js = (
                    f"window.update_progress({percent:.1f}, "
                    f"{json.dumps(speed_str)}, "
                    f"{json.dumps(eta_str)}, "
                    f"{json.dumps(down_mb)}, "
                    f"{json.dumps(total_mb)}, null);"
                )
                try:
                    self.window.evaluate_js(js)
                except Exception:
                    pass

        try:
            result = downloader.download_bulk_queue(
                items=items,
                media_type=media_type,
                quality_option=quality,
                output_path=output_dir,
                overall_hook=overall_hook,
                item_hook=item_hook,
                cancel_event=self.cancel_event,
                pause_event=self.pause_event,
                turbo_threads=threads
            )
            return result
        except Exception as e:
            if self.cancel_event.is_set():
                return {"cancelled": True}
            return {"error": str(e)}

    # ================= UPDATE & SYSTEM METHODS =================
    def get_versions(self):
        """Returns installed app version, yt-dlp version, and override state."""
        return updater.get_installed_versions()

    def check_updates(self):
        """Checks for both yt-dlp (PyPI) and app (GitHub) updates asynchronously."""
        ytdlp_res = updater.check_ytdlp_update()
        app_res = updater.check_app_update()
        return {
            "ytdlp": ytdlp_res,
            "app": app_res
        }

    def update_ytdlp(self):
        """Downloads the latest yt-dlp wheel from PyPI and extracts it to %LOCALAPPDATA%."""
        def progress_cb(pct, status):
            if not self.window:
                return
            js = f"if (window.update_ytdlp_progress) {{ window.update_ytdlp_progress({pct}, {json.dumps(status)}); }}"
            try:
                self.window.evaluate_js(js)
            except Exception:
                pass

        return updater.perform_ytdlp_update(progress_cb=progress_cb)

    def download_app_update(self, asset_url, asset_name="", expected_size=0, expected_sha256=""):
        """Downloads and verifies the new app .exe release asset into a temp staging location."""
        def progress_cb(pct, status):
            if not self.window:
                return
            js = f"if (window.update_app_progress) {{ window.update_app_progress({pct}, {json.dumps(status)}); }}"
            try:
                self.window.evaluate_js(js)
            except Exception:
                pass

        return updater.download_and_verify_app_update(
            asset_url=asset_url,
            asset_name=asset_name,
            expected_size=expected_size if expected_size else None,
            expected_sha256=expected_sha256 if expected_sha256 else None,
            progress_cb=progress_cb
        )

    def apply_app_update(self, new_exe_path):
        """Swaps the running executable with the new version and relaunches."""
        return updater.apply_portable_update(new_exe_path)

    def open_url(self, url):
        """Opens a web URL in the user's default browser."""
        import webbrowser
        try:
            webbrowser.open(url)
            return True
        except Exception:
            return False

    def restart_app(self):
        """Restarts the application to load new updates."""
        def _do_restart():
            import time
            time.sleep(0.3)
            updater.restart_app()

        threading.Thread(target=_do_restart, daemon=True).start()
        return {"restarting": True}


def get_html_path():
    """Find index.html in dev environment or PyInstaller bundled environment."""
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        base_dir = sys._MEIPASS
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_dir, "gui_liquid", "index.html")


def main():
    api = DownloaderApi()
    html_file = get_html_path()
    
    if not os.path.exists(html_file):
        print(f"Error: Could not locate frontend file: {html_file}")
        sys.exit(1)

    window = webview.create_window(
        title=f"FS Media Downloader v{updater.APP_VERSION} - Liquid Glass Edition by Fahad Shabbir",
        url=html_file,
        js_api=api,
        width=1040,
        height=800,
        min_size=(880, 620),
        background_color='#090d16',
        text_select=True,
    )
    api.set_window(window)
    
    storage_dir = os.path.join(updater.get_local_appdata_dir(), "webview_cache")
    try:
        os.makedirs(storage_dir, exist_ok=True)
    except Exception:
        storage_dir = None

    icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app_icon.ico")
    if not os.path.exists(icon_path):
        icon_path = None

    webview.start(
        debug=False,
        private_mode=False,
        storage_path=storage_dir,
        icon=icon_path
    )


if __name__ == '__main__':
    main()
