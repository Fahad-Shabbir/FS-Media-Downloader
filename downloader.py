import os
import sys
import re
import imageio_ffmpeg
import yt_dlp

# Generic URL regex matching any web video / audio link
URL_REGEX = re.compile(r'https?://[^\s<>"]+')

def detect_platform(url):
    """Identify the source platform of a given URL for visual badging."""
    u = url.lower()
    if 'youtube.com' in u or 'youtu.be' in u:
        return 'YouTube'
    elif 'twitter.com' in u or 'x.com' in u:
        return 'X (Twitter)'
    elif 'facebook.com' in u or 'fb.watch' in u or 'fb.com' in u:
        return 'Facebook'
    elif 'instagram.com' in u:
        return 'Instagram'
    elif 'tiktok.com' in u:
        return 'TikTok'
    elif 'reddit.com' in u or 'redd.it' in u:
        return 'Reddit'
    elif 'twitch.tv' in u:
        return 'Twitch'
    elif 'soundcloud.com' in u:
        return 'SoundCloud'
    elif 'vimeo.com' in u:
        return 'Vimeo'
    elif 'pinterest.com' in u or 'pin.it' in u:
        return 'Pinterest'
    elif 'dailymotion.com' in u:
        return 'Dailymotion'
    return 'Online Video'

def get_ffmpeg_path():
    """Locate ffmpeg executable from PyInstaller bundle, imageio-ffmpeg or system path."""
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        bundle_dir = sys._MEIPASS
        bin_dir = os.path.join(bundle_dir, 'imageio_ffmpeg', 'binaries')
        if os.path.isdir(bin_dir):
            for fname in os.listdir(bin_dir):
                if fname.startswith('ffmpeg') and fname.endswith('.exe'):
                    return os.path.join(bin_dir, fname)
        exe_dir = os.path.dirname(sys.executable)
        for check_path in [bundle_dir, exe_dir]:
            f = os.path.join(check_path, 'ffmpeg.exe')
            if os.path.exists(f):
                return f

    try:
        exe = imageio_ffmpeg.get_ffmpeg_exe()
        if exe and os.path.exists(exe):
            return exe
    except Exception:
        pass
    return "ffmpeg"

def get_cookie_file():
    """Check if cookies.txt exists next to executable or script."""
    candidates = [
        os.path.join(os.getcwd(), 'cookies.txt'),
    ]
    if '__file__' in globals():
        candidates.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cookies.txt'))
    if getattr(sys, 'frozen', False):
        exe_dir = os.path.dirname(sys.executable)
        candidates.insert(0, os.path.join(exe_dir, 'cookies.txt'))
        
    for path in candidates:
        if os.path.isfile(path) and os.path.getsize(path) > 0:
            return path
    return None

def format_duration(seconds):
    if not seconds:
        return "Unknown"
    try:
        seconds = int(seconds)
        mins, secs = divmod(seconds, 60)
        hours, mins = divmod(mins, 60)
        if hours > 0:
            return f"{hours}:{mins:02d}:{secs:02d}"
        return f"{mins}:{secs:02d}"
    except Exception:
        return "Unknown"

def is_playlist_url(url):
    """Check if URL points to a playlist or contains a playlist parameter."""
    u = url.lower()
    return "list=" in u or "/playlist" in u or "/sets/" in u

def extract_video_info(url):
    """
    Extracts video details and sorted list of available resolutions
    from YouTube, X/Twitter, Facebook, Instagram, TikTok, Reddit, etc.
    """
    platform = detect_platform(url)
    
    ydl_opts = {
        'skip_download': True,
        'quiet': True,
        'no_warnings': True,
        'extract_flat': False,
    }
    
    cookie_path = get_cookie_file()
    if cookie_path:
        ydl_opts['cookiefile'] = cookie_path
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        
        if 'entries' in info:
            entries = list(info.get('entries', []))
            if not entries:
                raise ValueError("No video entries found in the provided URL.")
            info = entries[0]

        formats = info.get('formats', [])
        resolution_map = {}
        
        for f in formats:
            height = f.get('height')
            vcodec = f.get('vcodec', 'none')
            # Ensure it has video
            if height and vcodec != 'none':
                fps = f.get('fps') or 30
                
                if height >= 2160:
                    prefix = "4K • "
                elif height >= 1440:
                    prefix = "2K • "
                elif height >= 1080:
                    prefix = "FHD • "
                elif height >= 720:
                    prefix = "HD • "
                else:
                    prefix = ""
                
                label = f"{prefix}{height}p"
                if fps and fps >= 50:
                    label += f" ({int(fps)}fps)"
                
                if height not in resolution_map or (fps and fps > resolution_map[height]['fps']):
                    resolution_map[height] = {
                        'height': height,
                        'fps': fps,
                        'label': label,
                        'format_id': f.get('format_id')
                    }
        
        # Fallback if formats list lacked individual heights but main info has height
        if not resolution_map and info.get('height'):
            h = info['height']
            resolution_map[h] = {
                'height': h,
                'fps': 30,
                'label': f"{h}p (Source)",
                'format_id': 'best'
            }

        sorted_heights = sorted(resolution_map.keys(), reverse=True)
        resolutions = [resolution_map[h] for h in sorted_heights]

        return {
            'id': info.get('id'),
            'platform': platform,
            'title': info.get('title') or f"{platform} Video",
            'channel': info.get('uploader') or info.get('channel') or info.get('creator') or platform,
            'duration': format_duration(info.get('duration')),
            'thumbnail': info.get('thumbnail'),
            'resolutions': resolutions,
            'webpage_url': info.get('webpage_url', url)
        }

def extract_bulk_or_playlist_info(raw_text):
    """
    Analyzes raw text containing a playlist link or multiple URLs across all supported platforms.
    """
    found_urls = URL_REGEX.findall(raw_text)
    if not found_urls:
        raise ValueError("No valid URLs found. Please check your links.")

    # Check if single playlist URL
    if len(found_urls) == 1 and is_playlist_url(found_urls[0]):
        url = found_urls[0]
        platform = detect_platform(url)
        ydl_opts = {
            'extract_flat': 'in_playlist',
            'quiet': True,
            'no_warnings': True,
            'skip_download': True,
        }
        cookie_path = get_cookie_file()
        if cookie_path:
            ydl_opts['cookiefile'] = cookie_path

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            raw_entries = list(info.get('entries', []))
            if not raw_entries:
                raise ValueError("Playlist / Set is empty or unavailable.")

            items = []
            for i, e in enumerate(raw_entries):
                if not e:
                    continue
                v_id = e.get('id')
                v_url = e.get('url')
                if v_url and not v_url.startswith('http'):
                    v_url = f"https://www.youtube.com/watch?v={v_id or v_url}"
                elif not v_url and v_id:
                    v_url = f"https://www.youtube.com/watch?v={v_id}"
                
                if v_url:
                    items.append({
                        'title': e.get('title') or f"{platform} Item {len(items)+1}",
                        'url': v_url,
                        'duration': format_duration(e.get('duration')),
                        'platform': platform
                    })

            return {
                'type': 'playlist',
                'platform': platform,
                'title': info.get('title') or f"{platform} Playlist",
                'count': len(items),
                'items': items
            }

    # Multi-URL bulk list across any platform
    items = []
    seen = set()
    for u in found_urls:
        clean_u = u.split('&list=')[0] if 'watch?v=' in u and '&list=' in u else u
        if clean_u not in seen:
            seen.add(clean_u)
            plat = detect_platform(clean_u)
            items.append({
                'title': f"Item {len(items) + 1} ({plat})",
                'url': clean_u,
                'duration': "Unknown",
                'platform': plat
            })

    return {
        'type': 'bulk',
        'platform': 'Multi-Platform',
        'title': f"Bulk Queue ({len(items)} items)",
        'count': len(items),
        'items': items
    }

def download_media(url, media_type, quality_option, output_path, progress_hook=None, turbo_threads=8, cancel_event=None, pause_event=None):
    """
    Downloads media across any supported site:
    - media_type: 'video' or 'audio'
    - quality_option: height int (e.g. 1080), 'best', or 'MP3'/'WAV' for audio
    - turbo_threads: number of parallel fragment download threads (default 8x)
    - cancel_event: threading.Event to abort download
    - pause_event: threading.Event to pause/resume download
    """
    import time
    ffmpeg_exe = get_ffmpeg_path()
    outtmpl = os.path.join(output_path, '%(title)s.%(ext)s')
    
    ydl_opts = {
        'outtmpl': outtmpl,
        'ffmpeg_location': ffmpeg_exe,
        'quiet': True,
        'no_warnings': True,
        'restrictfilenames': False,
        'windowsfilenames': True,
    }

    # Multi-threaded turbo speed acceleration
    if turbo_threads and turbo_threads > 1:
        ydl_opts.update({
            'concurrent_fragment_downloads': turbo_threads,
            'http_chunk_size': 10485760,  # 10 MB chunk size to prevent throttling
            'buffersize': 16384,          # 16 KB socket buffer
        })

    def internal_hook(d):
        if cancel_event and cancel_event.is_set():
            raise yt_dlp.utils.DownloadCancelled("Download cancelled by user")
        if pause_event:
            while not pause_event.is_set():
                if cancel_event and cancel_event.is_set():
                    raise yt_dlp.utils.DownloadCancelled("Download cancelled by user")
                time.sleep(0.15)
        if progress_hook:
            progress_hook(d)

    ydl_opts['progress_hooks'] = [internal_hook]

    cookie_path = get_cookie_file()
    if cookie_path:
        ydl_opts['cookiefile'] = cookie_path

    if media_type == 'audio':
        if str(quality_option).upper() == 'WAV':
            ydl_opts.update({
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'wav',
                }],
            })
        else:  # Default MP3
            ydl_opts.update({
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '320',
                }],
            })
    else:
        # Video MP4 (Universal format selector)
        if quality_option == "best" or not str(quality_option).isdigit():
            ydl_opts.update({
                'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio/best[ext=mp4]/best',
                'merge_output_format': 'mp4',
            })
        else:
            height = int(quality_option)
            ydl_opts.update({
                'format': f'bestvideo[height<={height}][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height<={height}]+bestaudio/best[height<={height}]/best',
                'merge_output_format': 'mp4',
            })

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        return {"success": True}
    except (yt_dlp.utils.DownloadCancelled, Exception) as e:
        if cancel_event and cancel_event.is_set():
            return {"cancelled": True}
        raise e

def download_bulk_queue(items, media_type, quality_option, output_path, overall_hook=None, item_hook=None, cancel_event=None, pause_event=None, turbo_threads=8):
    """
    Sequentially downloads a batch of items from any mix of platforms with optional Turbo acceleration.
    """
    total = len(items)
    successful = 0
    failed = []

    for idx, item in enumerate(items):
        if cancel_event and cancel_event.is_set():
            if overall_hook:
                overall_hook(idx, total, "Download Cancelled by User", "cancelled")
            break

        title = item.get('title', f"Video {idx+1}")
        url = item.get('url')

        if overall_hook:
            overall_hook(idx + 1, total, title, "downloading")

        try:
            res = download_media(
                url=url,
                media_type=media_type,
                quality_option=quality_option,
                output_path=output_path,
                progress_hook=item_hook,
                turbo_threads=turbo_threads,
                cancel_event=cancel_event,
                pause_event=pause_event
            )
            if res and res.get('cancelled'):
                if overall_hook:
                    overall_hook(idx, total, "Download Cancelled by User", "cancelled")
                break
            successful += 1
        except Exception as e:
            if cancel_event and cancel_event.is_set():
                if overall_hook:
                    overall_hook(idx, total, "Download Cancelled by User", "cancelled")
                break
            failed.append((title, str(e)))

    if overall_hook and not (cancel_event and cancel_event.is_set()):
        overall_hook(total, total, f"Completed: {successful}/{total} successful", "finished")

    return {
        'total': total,
        'successful': successful,
        'failed': failed,
        'cancelled': bool(cancel_event and cancel_event.is_set())
    }
