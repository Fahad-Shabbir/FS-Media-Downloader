import os
import re
import sys
import threading
from io import BytesIO
from pathlib import Path
import requests
from PIL import Image, ImageDraw, ImageFont
import customtkinter as ctk
from tkinter import filedialog, messagebox

import downloader

# Configure CustomTkinter default appearance
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# ================= DUAL LIQUID GLASS THEME PALETTE =================
# Supports seamless Light and Dark mode via (Light Color, Dark Color) tuples
COLOR_CANVAS_BG = ("#F0F3F8", "#0B0E14")          # Clean ice-white in light, cosmic midnight in dark
COLOR_GLASS_CARD = ("#FFFFFF", "#161B22")         # Pure elevated glass in light, frosted obsidian in dark
COLOR_GLASS_BORDER = ("#D8DEE4", "#30363D")       # Crisp specular border
COLOR_GLASS_INPUT = ("#F6F8FA", "#0D1117")        # Inset glass input field
COLOR_GLASS_HOVER = ("#E6EBF1", "#21262D")        # Frosted glass hover
COLOR_GLASS_PILL = ("#EFF2F6", "#21262D")         # Unselected pill button
COLOR_SUBTEXT = ("#57606A", "#8B949E")            # Muted readable text
COLOR_TEXT_PRIMARY = ("#1F2328", "#FFFFFF")       # Primary text
COLOR_ACCENT = "#E50914"                          # Liquid Crimson
COLOR_ACCENT_HOVER = "#B80710"                    # Darker crimson
COLOR_LIQUID_CYAN = ("#0969DA", "#00D2FF")        # Cyan glow
COLOR_TURBO_GOLD = ("#B45309", "#FFB300")         # Turbo gold
COLOR_TURBO_HOVER = ("#92400E", "#FFA000")
COLOR_SUCCESS = ("#1A7F37", "#00E676")            # Success emerald
COLOR_SUCCESS_HOVER = ("#14632B", "#00C853")
COLOR_DANGER = ("#CF222E", "#FF1744")             # Liquid red
COLOR_DANGER_HOVER = ("#A41B24", "#D50000")

ANSI_ESCAPE = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')

def strip_ansi(text):
    if not text:
        return ""
    return ANSI_ESCAPE.sub('', text).strip()

def apply_liquid_backdrop(window, dark=True):
    """Enables Windows 11 DWM titlebar dark/light mode and native Mica/Acrylic blur effect."""
    try:
        import ctypes
        hwnd = ctypes.windll.user32.GetParent(window.winfo_id())
        if not hwnd:
            hwnd = window.winfo_id()
        # DWMWA_USE_IMMERSIVE_DARK_MODE = 20
        dark_mode = ctypes.c_int(1 if dark else 0)
        ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 20, ctypes.byref(dark_mode), ctypes.sizeof(dark_mode))
        
        # DWMWA_SYSTEMBACKDROP_TYPE = 38 (Windows 11 22H2+): 3 = Mica
        backdrop = ctypes.c_int(3)
        res = ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 38, ctypes.byref(backdrop), ctypes.sizeof(backdrop))
        if res != 0:
            # Windows 11 21H2 fallback (DWMWA_MICA_EFFECT = 1029)
            mica = ctypes.c_int(1)
            ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 1029, ctypes.byref(mica), ctypes.sizeof(mica))
    except Exception:
        pass

def add_duration_badge(image, duration_str):
    """Draw a clean frosted-glass duration timestamp on the bottom-right of thumbnail."""
    if not duration_str or duration_str == "Unknown":
        return image
    
    img = image.copy().convert("RGBA")
    draw = ImageDraw.Draw(img)
    
    try:
        font = ImageFont.truetype("arial.ttf", 13)
    except Exception:
        font = ImageFont.load_default()

    bbox = draw.textbbox((0, 0), duration_str, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    
    pad_x, pad_y = 7, 4
    box_w = text_w + pad_x * 2
    box_h = text_h + pad_y * 2
    
    img_w, img_h = img.size
    x1 = img_w - box_w - 8
    y1 = img_h - box_h - 8
    x2 = img_w - 8
    y2 = img_h - 8
    
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)
    overlay_draw.rounded_rectangle([x1, y1, x2, y2], radius=6, fill=(11, 14, 20, 215), outline=(255, 255, 255, 50), width=1)
    img = Image.alpha_composite(img, overlay)
    
    draw_final = ImageDraw.Draw(img)
    draw_final.text((x1 + pad_x, y1 + pad_y - 1), duration_str, fill=(255, 255, 255, 255), font=font)
    
    return img.convert("RGB")

class YouTubeDownloaderApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Universal Media Downloader - by Fahad Shabbir")
        self.geometry("930x870")
        self.minsize(840, 750)
        self.configure(fg_color=COLOR_CANVAS_BG)

        # Hook into native Windows 11 Mica/Acrylic blur (Dark by default)
        self.after(150, lambda: apply_liquid_backdrop(self, dark=True))

        # Application state
        self.default_download_dir = str(Path.home() / "Downloads")
        self.active_mode = "single"  # "single" or "bulk"

        # Single mode state
        self.single_video_info = None
        self.is_single_analyzing = False
        self.is_single_downloading = False
        self.single_media_type = "video"
        self.single_resolution_height = None
        self.single_audio_format = "MP3"
        self.single_res_buttons = []

        # Bulk / Playlist mode state
        self.bulk_info = None
        self.is_bulk_analyzing = False
        self.is_bulk_downloading = False
        self.bulk_cancel_event = threading.Event()
        self.bulk_media_type = "video"
        self.bulk_quality_option = "1080"
        self.bulk_audio_format = "MP3"
        self.bulk_res_buttons = []

        self._build_ui()

    def _build_ui(self):
        # Top-level scrollable frame with dual mode background
        self.scroll_canvas = ctk.CTkScrollableFrame(self, fg_color=COLOR_CANVAS_BG, corner_radius=0)
        self.scroll_canvas.pack(fill="both", expand=True)

        # Centering layout configuration (Columns 0 & 2 expand, Column 1 holds fixed max-width content)
        self.scroll_canvas.grid_columnconfigure(0, weight=1)
        self.scroll_canvas.grid_columnconfigure(1, weight=0, minsize=860)
        self.scroll_canvas.grid_columnconfigure(2, weight=1)

        # Main Centered Container
        self.center_box = ctk.CTkFrame(self.scroll_canvas, fg_color="transparent", width=860)
        self.center_box.grid(row=0, column=1, sticky="nsew", padx=20, pady=25)

        # Header with branding & liquid glow
        self._build_header()

        # Mode Selector Tabs (Single vs Bulk/Playlist)
        self._build_mode_selector()

        # Container for Single Mode Views
        self.single_container = ctk.CTkFrame(self.center_box, fg_color="transparent")
        self.single_container.pack(fill="x")

        # Container for Bulk Mode Views (Initially Hidden)
        self.bulk_container = ctk.CTkFrame(self.center_box, fg_color="transparent")

        # Populate Single Mode
        self._build_single_mode_views()

        # Populate Bulk Mode
        self._build_bulk_mode_views()

        # Footer
        self._build_footer()

    def _build_header(self):
        header_frame = ctk.CTkFrame(
            self.center_box,
            fg_color=COLOR_GLASS_CARD,
            corner_radius=16,
            border_width=1,
            border_color=COLOR_GLASS_BORDER
        )
        header_frame.pack(fill="x", pady=(0, 16))

        inner_h = ctk.CTkFrame(header_frame, fg_color="transparent")
        inner_h.pack(fill="x", padx=18, pady=16)

        title_row = ctk.CTkFrame(inner_h, fg_color="transparent")
        title_row.pack(fill="x")

        # Liquid Play Logo badge
        play_badge = ctk.CTkButton(
            title_row,
            text="▶",
            width=36,
            height=32,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=COLOR_ACCENT,
            hover_color=COLOR_ACCENT,
            corner_radius=10,
            state="disabled"
        )
        play_badge.pack(side="left", padx=(0, 12))

        title_lbl = ctk.CTkLabel(
            title_row,
            text="Universal Media Downloader",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color=COLOR_TEXT_PRIMARY
        )
        title_lbl.pack(side="left")

        creator_badge = ctk.CTkLabel(
            title_row,
            text="by Fahad Shabbir",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#FF4D4D",
            fg_color=("#FDE8E8", "#2D1517"),
            corner_radius=8,
            padx=10,
            pady=3
        )
        creator_badge.pack(side="left", padx=(12, 0))

        # --- Top Right Control Row: Theme Switcher & Cookie Button ---
        # 1. Theme Toggle Button (Light / Dark)
        current_mode = ctk.get_appearance_mode().lower()
        theme_btn_text = "Light Mode" if current_mode == "dark" else "Dark Mode"
        self.theme_btn = ctk.CTkButton(
            title_row,
            text=theme_btn_text,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color=COLOR_GLASS_PILL,
            hover_color=COLOR_GLASS_HOVER,
            text_color=COLOR_TEXT_PRIMARY,
            border_width=1,
            border_color=COLOR_GLASS_BORDER,
            height=30,
            corner_radius=8,
            command=self.toggle_theme
        )
        self.theme_btn.pack(side="right")

        # 2. Cookie / Anti-Bot Bypass Button
        has_cookies = bool(downloader.get_cookie_file())
        self.cookie_status_btn = ctk.CTkButton(
            title_row,
            text="🍪 Cookies Active" if has_cookies else "🍪 Bypass Bot Check",
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color=("#D1FADF", "#132B20") if has_cookies else COLOR_GLASS_PILL,
            hover_color=("#A6F4C5", "#1C4230") if has_cookies else COLOR_GLASS_HOVER,
            text_color=COLOR_SUCCESS if has_cookies else COLOR_SUBTEXT,
            border_width=1,
            border_color=("#A6F4C5", "#1F4C36") if has_cookies else COLOR_GLASS_BORDER,
            height=30,
            corner_radius=8,
            command=self.import_cookies_file
        )
        self.cookie_status_btn.pack(side="right", padx=(0, 8))

        sub_lbl = ctk.CTkLabel(
            inner_h,
            text="Download HD/4K videos & audio from YouTube, X (Twitter), Facebook, Instagram, TikTok, Reddit & more",
            font=ctk.CTkFont(size=13),
            text_color=COLOR_SUBTEXT
        )
        sub_lbl.pack(anchor="w", padx=(48, 0), pady=(3, 0))

        # Supported platforms frosted pill bar
        platforms_row = ctk.CTkFrame(inner_h, fg_color="transparent")
        platforms_row.pack(fill="x", padx=(48, 0), pady=(8, 0))

        platforms = [
            "YouTube", "X (Twitter)", "Facebook", "Instagram", "TikTok", "Reddit", "Twitch", "SoundCloud"
        ]
        for name in platforms:
            chip = ctk.CTkLabel(
                platforms_row,
                text=name,
                font=ctk.CTkFont(size=11),
                text_color=COLOR_TEXT_PRIMARY,
                fg_color=COLOR_GLASS_INPUT,
                corner_radius=6,
                padx=8,
                pady=2
            )
            chip.pack(side="left", padx=(0, 6))

    def toggle_theme(self):
        """Seamlessly toggle between Light and Dark mode with native Windows DWM adaptation."""
        current = ctk.get_appearance_mode().lower()
        if current == "dark":
            ctk.set_appearance_mode("light")
            self.theme_btn.configure(text="Dark Mode")
            apply_liquid_backdrop(self, dark=False)
        else:
            ctk.set_appearance_mode("dark")
            self.theme_btn.configure(text="Light Mode")
            apply_liquid_backdrop(self, dark=True)

    def _build_mode_selector(self):
        mode_frame = ctk.CTkFrame(self.center_box, fg_color="transparent")
        mode_frame.pack(fill="x", pady=(0, 14))

        self.mode_switch = ctk.CTkSegmentedButton(
            mode_frame,
            values=["Single Video Mode", "Playlist & Bulk Download Mode"],
            selected_color=COLOR_ACCENT,
            selected_hover_color=COLOR_ACCENT_HOVER,
            unselected_color=COLOR_GLASS_CARD,
            unselected_hover_color=COLOR_GLASS_HOVER,
            command=self.on_mode_switched,
            font=ctk.CTkFont(size=13, weight="bold"),
            height=40,
            corner_radius=12
        )
        self.mode_switch.set("Single Video Mode")
        self.mode_switch.pack(fill="x")

    def on_mode_switched(self, mode_name):
        if "Single" in mode_name:
            self.active_mode = "single"
            self.bulk_container.pack_forget()
            self.single_container.pack(fill="x")
        else:
            self.active_mode = "bulk"
            self.single_container.pack_forget()
            self.bulk_container.pack(fill="x")

    # ================= SINGLE VIDEO MODE VIEWS =================

    def _build_single_mode_views(self):
        # 1. URL Input Glass Card
        input_card = ctk.CTkFrame(
            self.single_container,
            fg_color=COLOR_GLASS_CARD,
            corner_radius=16,
            border_width=1,
            border_color=COLOR_GLASS_BORDER
        )
        input_card.pack(fill="x", pady=(0, 14))

        input_title = ctk.CTkLabel(
            input_card,
            text="1. Paste Video Link (YouTube, X, Facebook, Instagram, TikTok, Reddit)",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=COLOR_TEXT_PRIMARY
        )
        input_title.pack(anchor="w", padx=18, pady=(14, 6))

        row = ctk.CTkFrame(input_card, fg_color="transparent")
        row.pack(fill="x", padx=18, pady=(0, 14))

        self.single_url_entry = ctk.CTkEntry(
            row,
            placeholder_text="https://www.youtube.com/... or https://x.com/... or https://instagram.com/...",
            height=44,
            font=ctk.CTkFont(size=13),
            fg_color=COLOR_GLASS_INPUT,
            border_color=COLOR_GLASS_BORDER,
            text_color=COLOR_TEXT_PRIMARY,
            corner_radius=10
        )
        self.single_url_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.single_url_entry.bind("<Return>", lambda event: self.start_single_analyze())

        self.single_paste_btn = ctk.CTkButton(
            row,
            text="Paste",
            width=80,
            height=44,
            fg_color=COLOR_GLASS_PILL,
            hover_color=COLOR_GLASS_HOVER,
            text_color=COLOR_TEXT_PRIMARY,
            border_width=1,
            border_color=COLOR_GLASS_BORDER,
            font=ctk.CTkFont(size=13, weight="bold"),
            corner_radius=10,
            command=self.paste_single_from_clipboard
        )
        self.single_paste_btn.pack(side="left", padx=(0, 8))

        self.single_analyze_btn = ctk.CTkButton(
            row,
            text="Analyze Link",
            width=120,
            height=44,
            fg_color=COLOR_ACCENT,
            hover_color=COLOR_ACCENT_HOVER,
            text_color="#FFFFFF",
            font=ctk.CTkFont(size=13, weight="bold"),
            corner_radius=10,
            command=self.start_single_analyze
        )
        self.single_analyze_btn.pack(side="left")

        self.single_status_lbl = ctk.CTkLabel(
            input_card,
            text="",
            font=ctk.CTkFont(size=12),
            text_color=COLOR_LIQUID_CYAN
        )
        self.single_status_lbl.pack(anchor="w", padx=18, pady=(0, 10))

        # 2. Video Preview Card (Initially Hidden)
        self.single_preview_card = ctk.CTkFrame(
            self.single_container,
            fg_color=COLOR_GLASS_CARD,
            corner_radius=16,
            border_width=1,
            border_color=COLOR_GLASS_BORDER
        )
        inner = ctk.CTkFrame(self.single_preview_card, fg_color="transparent")
        inner.pack(fill="x", padx=18, pady=18)

        self.single_thumb_label = ctk.CTkLabel(
            inner,
            text="",
            width=210,
            height=118,
            fg_color=COLOR_GLASS_INPUT,
            corner_radius=10
        )
        self.single_thumb_label.pack(side="left", padx=(0, 16))

        meta = ctk.CTkFrame(inner, fg_color="transparent")
        meta.pack(side="left", fill="both", expand=True)

        self.single_title_lbl = ctk.CTkLabel(
            meta,
            text="",
            font=ctk.CTkFont(size=14, weight="bold"),
            anchor="w",
            justify="left",
            wraplength=520,
            text_color=COLOR_TEXT_PRIMARY
        )
        self.single_title_lbl.pack(anchor="w", pady=(0, 6))

        self.single_channel_lbl = ctk.CTkLabel(
            meta,
            text="",
            font=ctk.CTkFont(size=13),
            text_color=COLOR_SUBTEXT,
            anchor="w"
        )
        self.single_channel_lbl.pack(anchor="w", pady=(0, 3))

        self.single_duration_lbl = ctk.CTkLabel(
            meta,
            text="",
            font=ctk.CTkFont(size=13),
            text_color=COLOR_SUBTEXT,
            anchor="w"
        )
        self.single_duration_lbl.pack(anchor="w", pady=(0, 6))

        tag_row = ctk.CTkFrame(meta, fg_color="transparent")
        tag_row.pack(anchor="w")

        self.single_platform_badge = ctk.CTkLabel(
            tag_row,
            text="YouTube",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=COLOR_TEXT_PRIMARY,
            fg_color=COLOR_GLASS_INPUT,
            corner_radius=6,
            padx=10,
            pady=3
        )
        self.single_platform_badge.pack(side="left", padx=(0, 8))

        self.single_badge_lbl = ctk.CTkLabel(
            tag_row,
            text="✓ Stream verified",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=COLOR_SUCCESS,
            anchor="w"
        )
        self.single_badge_lbl.pack(side="left")

        # 3. Format & Quality Selection Glass Card (Initially Hidden)
        self.single_options_card = ctk.CTkFrame(
            self.single_container,
            fg_color=COLOR_GLASS_CARD,
            corner_radius=16,
            border_width=1,
            border_color=COLOR_GLASS_BORDER
        )
        top_row = ctk.CTkFrame(self.single_options_card, fg_color="transparent")
        top_row.pack(fill="x", padx=18, pady=(14, 10))

        opt_title = ctk.CTkLabel(
            top_row,
            text="2. Select Format & Quality",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=COLOR_TEXT_PRIMARY
        )
        opt_title.pack(side="left")

        self.single_type_switch = ctk.CTkSegmentedButton(
            top_row,
            values=["Video (MP4)", "Audio (MP3 / WAV)"],
            selected_color=COLOR_ACCENT,
            selected_hover_color=COLOR_ACCENT_HOVER,
            unselected_color=COLOR_GLASS_INPUT,
            unselected_hover_color=COLOR_GLASS_HOVER,
            command=self.on_single_media_type_changed,
            font=ctk.CTkFont(size=12, weight="bold"),
            height=34,
            corner_radius=10
        )
        self.single_type_switch.set("Video (MP4)")
        self.single_type_switch.pack(side="right")

        self.single_video_frame = ctk.CTkFrame(self.single_options_card, fg_color="transparent")
        self.single_video_frame.pack(fill="x", padx=18, pady=(0, 16))

        self.single_res_lbl = ctk.CTkLabel(
            self.single_video_frame,
            text="Choose Available Resolution:",
            font=ctk.CTkFont(size=12),
            text_color=COLOR_SUBTEXT
        )
        self.single_res_lbl.pack(anchor="w", pady=(0, 8))

        self.single_res_grid = ctk.CTkFrame(self.single_video_frame, fg_color="transparent")
        self.single_res_grid.pack(fill="x")

        # Audio Frame
        self.single_audio_frame = ctk.CTkFrame(self.single_options_card, fg_color="transparent")

        self.single_audio_lbl = ctk.CTkLabel(
            self.single_audio_frame,
            text="Choose Audio Quality:",
            font=ctk.CTkFont(size=12),
            text_color=COLOR_SUBTEXT
        )
        self.single_audio_lbl.pack(anchor="w", pady=(0, 8))

        audio_btn_row = ctk.CTkFrame(self.single_audio_frame, fg_color="transparent")
        audio_btn_row.pack(fill="x")

        self.single_mp3_btn = ctk.CTkButton(
            audio_btn_row,
            text="MP3 Audio  •  320 kbps (High Quality)",
            height=44,
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=COLOR_ACCENT,
            hover_color=COLOR_ACCENT_HOVER,
            text_color="#FFFFFF",
            corner_radius=10,
            command=lambda: self.select_single_audio_format("MP3")
        )
        self.single_mp3_btn.pack(side="left", fill="x", expand=True, padx=(0, 8))

        self.single_wav_btn = ctk.CTkButton(
            audio_btn_row,
            text="WAV Audio  •  Lossless 16-bit PCM",
            height=44,
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=COLOR_GLASS_PILL,
            hover_color=COLOR_GLASS_HOVER,
            text_color=COLOR_TEXT_PRIMARY,
            border_width=1,
            border_color=COLOR_GLASS_BORDER,
            corner_radius=10,
            command=lambda: self.select_single_audio_format("WAV")
        )
        self.single_wav_btn.pack(side="left", fill="x", expand=True)

        # 4. Save Destination Glass Card
        dest_card = ctk.CTkFrame(
            self.single_container,
            fg_color=COLOR_GLASS_CARD,
            corner_radius=16,
            border_width=1,
            border_color=COLOR_GLASS_BORDER
        )
        dest_card.pack(fill="x", pady=(0, 14))

        dest_title = ctk.CTkLabel(
            dest_card,
            text="3. Save Destination Folder",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=COLOR_TEXT_PRIMARY
        )
        dest_title.pack(anchor="w", padx=18, pady=(14, 6))

        d_row = ctk.CTkFrame(dest_card, fg_color="transparent")
        d_row.pack(fill="x", padx=18, pady=(0, 14))

        self.single_dest_entry = ctk.CTkEntry(
            d_row,
            height=42,
            font=ctk.CTkFont(size=12),
            fg_color=COLOR_GLASS_INPUT,
            border_color=COLOR_GLASS_BORDER,
            text_color=COLOR_TEXT_PRIMARY,
            corner_radius=10
        )
        self.single_dest_entry.insert(0, self.default_download_dir)
        self.single_dest_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))

        self.single_browse_btn = ctk.CTkButton(
            d_row,
            text="Browse...",
            width=95,
            height=42,
            fg_color=COLOR_GLASS_PILL,
            hover_color=COLOR_GLASS_HOVER,
            text_color=COLOR_TEXT_PRIMARY,
            border_width=1,
            border_color=COLOR_GLASS_BORDER,
            font=ctk.CTkFont(size=12, weight="bold"),
            corner_radius=10,
            command=lambda: self.browse_folder(self.single_dest_entry)
        )
        self.single_browse_btn.pack(side="left")

        # 5. Download & Progress Glass Card
        self.single_action_card = ctk.CTkFrame(
            self.single_container,
            fg_color=COLOR_GLASS_CARD,
            corner_radius=16,
            border_width=1,
            border_color=COLOR_GLASS_BORDER
        )
        self.single_action_card.pack(fill="x", pady=(0, 14))

        a_inner = ctk.CTkFrame(self.single_action_card, fg_color="transparent")
        a_inner.pack(fill="x", padx=18, pady=18)

        # Turbo Speed acceleration switch with glowing amber styling
        turbo_row = ctk.CTkFrame(a_inner, fg_color="transparent")
        turbo_row.pack(fill="x", pady=(0, 12))

        self.single_turbo_switch = ctk.CTkSwitch(
            turbo_row,
            text="⚡ Turbo Acceleration (8x Multi-Threaded Parallel Streams)",
            font=ctk.CTkFont(size=12, weight="bold"),
            progress_color=COLOR_TURBO_GOLD,
            button_color=COLOR_TURBO_GOLD,
            button_hover_color=COLOR_TURBO_HOVER,
            text_color=COLOR_TEXT_PRIMARY
        )
        self.single_turbo_switch.select()
        self.single_turbo_switch.pack(side="left")

        self.single_download_btn = ctk.CTkButton(
            a_inner,
            text="Download Media",
            height=50,
            font=ctk.CTkFont(size=15, weight="bold"),
            fg_color=COLOR_SUCCESS,
            hover_color=COLOR_SUCCESS_HOVER,
            text_color="#FFFFFF",
            corner_radius=12,
            command=self.start_single_download
        )
        self.single_download_btn.pack(fill="x", pady=(0, 12))

        # Liquid Cyan progress bar
        self.single_prog_bar = ctk.CTkProgressBar(
            a_inner,
            height=10,
            corner_radius=5,
            progress_color=COLOR_LIQUID_CYAN,
            fg_color=COLOR_GLASS_INPUT
        )
        self.single_prog_bar.set(0)
        self.single_prog_bar.pack(fill="x", pady=(0, 8))

        self.single_prog_label = ctk.CTkLabel(
            a_inner,
            text="Paste a video link above and click Analyze to begin.",
            font=ctk.CTkFont(size=12),
            text_color=COLOR_SUBTEXT
        )
        self.single_prog_label.pack(anchor="w")

        self.single_completion_actions = ctk.CTkFrame(a_inner, fg_color="transparent")

        self.single_open_folder_btn = ctk.CTkButton(
            self.single_completion_actions,
            text="Open Download Folder",
            height=40,
            fg_color="#1F538D",
            hover_color="#163E69",
            text_color="#FFFFFF",
            font=ctk.CTkFont(size=12, weight="bold"),
            corner_radius=10,
            command=lambda: self.open_folder(self.single_dest_entry.get().strip())
        )
        self.single_open_folder_btn.pack(side="left", padx=(0, 10))

        self.single_reset_btn = ctk.CTkButton(
            self.single_completion_actions,
            text="Download Another Video",
            height=40,
            fg_color=COLOR_GLASS_PILL,
            hover_color=COLOR_GLASS_HOVER,
            text_color=COLOR_TEXT_PRIMARY,
            border_width=1,
            border_color=COLOR_GLASS_BORDER,
            font=ctk.CTkFont(size=12, weight="bold"),
            corner_radius=10,
            command=self.reset_single_ui
        )
        self.single_reset_btn.pack(side="left")

    # ================= BULK & PLAYLIST MODE VIEWS =================

    def _build_bulk_mode_views(self):
        # 1. Bulk Input Glass Card
        input_card = ctk.CTkFrame(
            self.bulk_container,
            fg_color=COLOR_GLASS_CARD,
            corner_radius=16,
            border_width=1,
            border_color=COLOR_GLASS_BORDER
        )
        input_card.pack(fill="x", pady=(0, 14))

        title_lbl = ctk.CTkLabel(
            input_card,
            text="1. Paste Playlist Link OR Multiple Links from Any Supported Site",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=COLOR_TEXT_PRIMARY
        )
        title_lbl.pack(anchor="w", padx=18, pady=(14, 4))

        help_lbl = ctk.CTkLabel(
            input_card,
            text="Supports YouTube playlists, or multiple links from YouTube, X, Facebook, Instagram, TikTok, Reddit, etc. (one per line):",
            font=ctk.CTkFont(size=12),
            text_color=COLOR_SUBTEXT
        )
        help_lbl.pack(anchor="w", padx=18, pady=(0, 8))

        self.bulk_textbox = ctk.CTkTextbox(
            input_card,
            height=110,
            font=ctk.CTkFont(size=12),
            fg_color=COLOR_GLASS_INPUT,
            border_width=1,
            border_color=COLOR_GLASS_BORDER,
            text_color=COLOR_TEXT_PRIMARY,
            corner_radius=10
        )
        self.bulk_textbox.pack(fill="x", padx=18, pady=(0, 10))

        btn_row = ctk.CTkFrame(input_card, fg_color="transparent")
        btn_row.pack(fill="x", padx=18, pady=(0, 14))

        self.bulk_paste_btn = ctk.CTkButton(
            btn_row,
            text="Paste from Clipboard",
            height=40,
            fg_color=COLOR_GLASS_PILL,
            hover_color=COLOR_GLASS_HOVER,
            text_color=COLOR_TEXT_PRIMARY,
            border_width=1,
            border_color=COLOR_GLASS_BORDER,
            font=ctk.CTkFont(size=12, weight="bold"),
            corner_radius=10,
            command=self.paste_bulk_from_clipboard
        )
        self.bulk_paste_btn.pack(side="left", padx=(0, 8))

        self.bulk_clear_btn = ctk.CTkButton(
            btn_row,
            text="Clear",
            width=70,
            height=40,
            fg_color=COLOR_GLASS_INPUT,
            hover_color=COLOR_GLASS_HOVER,
            text_color=COLOR_TEXT_PRIMARY,
            border_width=1,
            border_color=COLOR_GLASS_BORDER,
            font=ctk.CTkFont(size=12),
            corner_radius=10,
            command=lambda: self.bulk_textbox.delete("1.0", "end")
        )
        self.bulk_clear_btn.pack(side="left", padx=(0, 8))

        self.bulk_analyze_btn = ctk.CTkButton(
            btn_row,
            text="Analyze Playlist / Links",
            height=40,
            fg_color=COLOR_ACCENT,
            hover_color=COLOR_ACCENT_HOVER,
            text_color="#FFFFFF",
            font=ctk.CTkFont(size=12, weight="bold"),
            corner_radius=10,
            command=self.start_bulk_analyze
        )
        self.bulk_analyze_btn.pack(side="right")

        self.bulk_status_lbl = ctk.CTkLabel(
            input_card,
            text="",
            font=ctk.CTkFont(size=12),
            text_color=COLOR_LIQUID_CYAN
        )
        self.bulk_status_lbl.pack(anchor="w", padx=18, pady=(0, 10))

        # 2. Queue Summary Card (Hidden initially)
        self.bulk_summary_card = ctk.CTkFrame(
            self.bulk_container,
            fg_color=COLOR_GLASS_CARD,
            corner_radius=16,
            border_width=1,
            border_color=COLOR_GLASS_BORDER
        )
        sum_inner = ctk.CTkFrame(self.bulk_summary_card, fg_color="transparent")
        sum_inner.pack(fill="x", padx=18, pady=18)

        head_row = ctk.CTkFrame(sum_inner, fg_color="transparent")
        head_row.pack(fill="x", pady=(0, 8))

        self.bulk_title_lbl = ctk.CTkLabel(
            head_row,
            text="Playlist / Queue Title",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=COLOR_TEXT_PRIMARY
        )
        self.bulk_title_lbl.pack(side="left")

        self.bulk_count_badge = ctk.CTkLabel(
            head_row,
            text="0 Videos",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#FFFFFF",
            fg_color=COLOR_ACCENT,
            corner_radius=8,
            padx=10,
            pady=3
        )
        self.bulk_count_badge.pack(side="right")

        self.bulk_items_preview = ctk.CTkTextbox(
            sum_inner,
            height=100,
            font=ctk.CTkFont(size=11),
            fg_color=COLOR_GLASS_INPUT,
            border_width=1,
            border_color=COLOR_GLASS_BORDER,
            text_color=COLOR_TEXT_PRIMARY,
            corner_radius=10,
            state="disabled"
        )
        self.bulk_items_preview.pack(fill="x")

        # 3. Bulk Quality Selector Glass Card
        self.bulk_options_card = ctk.CTkFrame(
            self.bulk_container,
            fg_color=COLOR_GLASS_CARD,
            corner_radius=16,
            border_width=1,
            border_color=COLOR_GLASS_BORDER
        )

        b_top_row = ctk.CTkFrame(self.bulk_options_card, fg_color="transparent")
        b_top_row.pack(fill="x", padx=18, pady=(14, 10))

        b_opt_title = ctk.CTkLabel(
            b_top_row,
            text="2. Select Batch Quality & Format",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=COLOR_TEXT_PRIMARY
        )
        b_opt_title.pack(side="left")

        self.bulk_type_switch = ctk.CTkSegmentedButton(
            b_top_row,
            values=["Video (MP4)", "Audio (MP3 / WAV)"],
            selected_color=COLOR_ACCENT,
            selected_hover_color=COLOR_ACCENT_HOVER,
            unselected_color=COLOR_GLASS_INPUT,
            unselected_hover_color=COLOR_GLASS_HOVER,
            command=self.on_bulk_media_type_changed,
            font=ctk.CTkFont(size=12, weight="bold"),
            height=34,
            corner_radius=10
        )
        self.bulk_type_switch.set("Video (MP4)")
        self.bulk_type_switch.pack(side="right")

        # Bulk video resolutions
        self.bulk_video_frame = ctk.CTkFrame(self.bulk_options_card, fg_color="transparent")
        self.bulk_video_frame.pack(fill="x", padx=18, pady=(0, 16))

        bulk_v_lbl = ctk.CTkLabel(
            self.bulk_video_frame,
            text="Target Video Quality:",
            font=ctk.CTkFont(size=12),
            text_color=COLOR_SUBTEXT
        )
        bulk_v_lbl.pack(anchor="w", pady=(0, 8))

        bulk_v_grid = ctk.CTkFrame(self.bulk_video_frame, fg_color="transparent")
        bulk_v_grid.pack(fill="x")

        qualities = [
            ("Best Available (Auto)", "best"),
            ("1080p Full HD", "1080"),
            ("720p HD", "720"),
            ("480p SD", "480")
        ]
        self.bulk_res_buttons = []
        for i, (q_name, q_val) in enumerate(qualities):
            btn = ctk.CTkButton(
                bulk_v_grid,
                text=q_name,
                height=38,
                font=ctk.CTkFont(size=12, weight="bold"),
                fg_color=COLOR_ACCENT if q_val == "1080" else COLOR_GLASS_PILL,
                hover_color=COLOR_ACCENT_HOVER if q_val == "1080" else COLOR_GLASS_HOVER,
                text_color="#FFFFFF" if q_val == "1080" else COLOR_TEXT_PRIMARY,
                border_width=1,
                border_color=COLOR_ACCENT if q_val == "1080" else COLOR_GLASS_BORDER,
                corner_radius=10,
                command=lambda val=q_val: self.select_bulk_resolution(val)
            )
            btn.grid(row=0, column=i, padx=4, sticky="ew")
            bulk_v_grid.grid_columnconfigure(i, weight=1)
            self.bulk_res_buttons.append((btn, q_val))

        # Bulk audio formats
        self.bulk_audio_frame = ctk.CTkFrame(self.bulk_options_card, fg_color="transparent")

        bulk_a_lbl = ctk.CTkLabel(
            self.bulk_audio_frame,
            text="Target Audio Quality:",
            font=ctk.CTkFont(size=12),
            text_color=COLOR_SUBTEXT
        )
        bulk_a_lbl.pack(anchor="w", pady=(0, 8))

        bulk_a_row = ctk.CTkFrame(self.bulk_audio_frame, fg_color="transparent")
        bulk_a_row.pack(fill="x")

        self.bulk_mp3_btn = ctk.CTkButton(
            bulk_a_row,
            text="MP3 Audio  •  320 kbps (High Quality)",
            height=44,
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=COLOR_ACCENT,
            hover_color=COLOR_ACCENT_HOVER,
            text_color="#FFFFFF",
            corner_radius=10,
            command=lambda: self.select_bulk_audio_format("MP3")
        )
        self.bulk_mp3_btn.pack(side="left", fill="x", expand=True, padx=(0, 8))

        self.bulk_wav_btn = ctk.CTkButton(
            bulk_a_row,
            text="WAV Audio  •  Lossless 16-bit PCM",
            height=44,
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=COLOR_GLASS_PILL,
            hover_color=COLOR_GLASS_HOVER,
            text_color=COLOR_TEXT_PRIMARY,
            border_width=1,
            border_color=COLOR_GLASS_BORDER,
            corner_radius=10,
            command=lambda: self.select_bulk_audio_format("WAV")
        )
        self.bulk_wav_btn.pack(side="left", fill="x", expand=True)

        # 4. Bulk Save Destination Glass Card
        b_dest_card = ctk.CTkFrame(
            self.bulk_container,
            fg_color=COLOR_GLASS_CARD,
            corner_radius=16,
            border_width=1,
            border_color=COLOR_GLASS_BORDER
        )
        b_dest_card.pack(fill="x", pady=(0, 14))

        b_dest_title = ctk.CTkLabel(
            b_dest_card,
            text="3. Save Destination Folder",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=COLOR_TEXT_PRIMARY
        )
        b_dest_title.pack(anchor="w", padx=18, pady=(14, 6))

        bd_row = ctk.CTkFrame(b_dest_card, fg_color="transparent")
        bd_row.pack(fill="x", padx=18, pady=(0, 14))

        self.bulk_dest_entry = ctk.CTkEntry(
            bd_row,
            height=42,
            font=ctk.CTkFont(size=12),
            fg_color=COLOR_GLASS_INPUT,
            border_color=COLOR_GLASS_BORDER,
            text_color=COLOR_TEXT_PRIMARY,
            corner_radius=10
        )
        self.bulk_dest_entry.insert(0, self.default_download_dir)
        self.bulk_dest_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))

        self.bulk_browse_btn = ctk.CTkButton(
            bd_row,
            text="Browse...",
            width=95,
            height=42,
            fg_color=COLOR_GLASS_PILL,
            hover_color=COLOR_GLASS_HOVER,
            text_color=COLOR_TEXT_PRIMARY,
            border_width=1,
            border_color=COLOR_GLASS_BORDER,
            font=ctk.CTkFont(size=12, weight="bold"),
            corner_radius=10,
            command=lambda: self.browse_folder(self.bulk_dest_entry)
        )
        self.bulk_browse_btn.pack(side="left")

        # 5. Bulk Download & Dual Progress Glass Card
        self.bulk_action_card = ctk.CTkFrame(
            self.bulk_container,
            fg_color=COLOR_GLASS_CARD,
            corner_radius=16,
            border_width=1,
            border_color=COLOR_GLASS_BORDER
        )
        self.bulk_action_card.pack(fill="x", pady=(0, 14))

        ba_inner = ctk.CTkFrame(self.bulk_action_card, fg_color="transparent")
        ba_inner.pack(fill="x", padx=18, pady=18)

        # Bulk Turbo Speed acceleration switch
        b_turbo_row = ctk.CTkFrame(ba_inner, fg_color="transparent")
        b_turbo_row.pack(fill="x", pady=(0, 12))

        self.bulk_turbo_switch = ctk.CTkSwitch(
            b_turbo_row,
            text="⚡ Turbo Acceleration (8x Multi-Threaded Parallel Streams)",
            font=ctk.CTkFont(size=12, weight="bold"),
            progress_color=COLOR_TURBO_GOLD,
            button_color=COLOR_TURBO_GOLD,
            button_hover_color=COLOR_TURBO_HOVER,
            text_color=COLOR_TEXT_PRIMARY
        )
        self.bulk_turbo_switch.select()
        self.bulk_turbo_switch.pack(side="left")

        action_row = ctk.CTkFrame(ba_inner, fg_color="transparent")
        action_row.pack(fill="x", pady=(0, 12))

        self.bulk_download_btn = ctk.CTkButton(
            action_row,
            text="Start Batch Download",
            height=50,
            font=ctk.CTkFont(size=15, weight="bold"),
            fg_color=COLOR_SUCCESS,
            hover_color=COLOR_SUCCESS_HOVER,
            text_color="#FFFFFF",
            corner_radius=12,
            command=self.start_bulk_download
        )
        self.bulk_download_btn.pack(side="left", fill="x", expand=True, padx=(0, 8))

        self.bulk_cancel_btn = ctk.CTkButton(
            action_row,
            text="Cancel Queue",
            width=120,
            height=50,
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=COLOR_DANGER,
            hover_color=COLOR_DANGER_HOVER,
            text_color="#FFFFFF",
            corner_radius=12,
            state="disabled",
            command=self.cancel_bulk_download
        )
        self.bulk_cancel_btn.pack(side="right")

        # Overall progress
        self.bulk_overall_lbl = ctk.CTkLabel(
            ba_inner,
            text="Overall Batch Progress: 0%",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=COLOR_TEXT_PRIMARY
        )
        self.bulk_overall_lbl.pack(anchor="w", pady=(0, 4))

        self.bulk_overall_bar = ctk.CTkProgressBar(
            ba_inner,
            height=10,
            corner_radius=5,
            progress_color=COLOR_LIQUID_CYAN,
            fg_color=COLOR_GLASS_INPUT
        )
        self.bulk_overall_bar.set(0)
        self.bulk_overall_bar.pack(fill="x", pady=(0, 10))

        # Current Item progress
        self.bulk_item_lbl = ctk.CTkLabel(
            ba_inner,
            text="Active Item: Ready",
            font=ctk.CTkFont(size=12),
            text_color=COLOR_SUBTEXT
        )
        self.bulk_item_lbl.pack(anchor="w", pady=(0, 4))

        self.bulk_item_bar = ctk.CTkProgressBar(
            ba_inner,
            height=7,
            corner_radius=4,
            progress_color="#1F538D",
            fg_color=COLOR_GLASS_INPUT
        )
        self.bulk_item_bar.set(0)
        self.bulk_item_bar.pack(fill="x", pady=(0, 10))

        # Completion actions
        self.bulk_completion_actions = ctk.CTkFrame(ba_inner, fg_color="transparent")

        self.bulk_open_folder_btn = ctk.CTkButton(
            self.bulk_completion_actions,
            text="Open Download Folder",
            height=40,
            fg_color="#1F538D",
            hover_color="#163E69",
            text_color="#FFFFFF",
            font=ctk.CTkFont(size=12, weight="bold"),
            corner_radius=10,
            command=lambda: self.open_folder(self.bulk_dest_entry.get().strip())
        )
        self.bulk_open_folder_btn.pack(side="left", padx=(0, 10))

        self.bulk_reset_btn = ctk.CTkButton(
            self.bulk_completion_actions,
            text="Start New Batch",
            height=40,
            fg_color=COLOR_GLASS_PILL,
            hover_color=COLOR_GLASS_HOVER,
            text_color=COLOR_TEXT_PRIMARY,
            border_width=1,
            border_color=COLOR_GLASS_BORDER,
            font=ctk.CTkFont(size=12, weight="bold"),
            corner_radius=10,
            command=self.reset_bulk_ui
        )
        self.bulk_reset_btn.pack(side="left")

    def _build_footer(self):
        footer_frame = ctk.CTkFrame(self.center_box, fg_color="transparent")
        footer_frame.pack(fill="x", pady=(0, 15))

        footer_lbl = ctk.CTkLabel(
            footer_frame,
            text="Universal Media Downloader  •  Designed & Developed by Fahad Shabbir",
            font=ctk.CTkFont(size=11),
            text_color=COLOR_SUBTEXT
        )
        footer_lbl.pack(anchor="center")

    # ================= COMMON UTILITIES =================

    def browse_folder(self, entry_widget):
        selected = filedialog.askdirectory(initialdir=entry_widget.get().strip() or self.default_download_dir)
        if selected:
            entry_widget.delete(0, "end")
            entry_widget.insert(0, os.path.normpath(selected))

    def open_folder(self, folder_path):
        if os.path.exists(folder_path):
            try:
                os.startfile(folder_path)
            except Exception as e:
                messagebox.showerror("Error", f"Could not open directory:\n{e}")
        else:
            messagebox.showwarning("Not Found", "Destination directory does not exist.")

    def import_cookies_file(self):
        selected = filedialog.askopenfilename(
            title="Select cookies.txt to bypass YouTube bot check",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if selected:
            try:
                import shutil
                target = os.path.join(os.getcwd(), 'cookies.txt')
                shutil.copy(selected, target)
                self.cookie_status_btn.configure(
                    text="🍪 Cookies Active",
                    fg_color=("#D1FADF", "#132B20"),
                    hover_color=("#A6F4C5", "#1C4230"),
                    text_color=COLOR_SUCCESS,
                    border_color=("#A6F4C5", "#1F4C36")
                )
                messagebox.showinfo(
                    "Cookies Imported Successfully",
                    "cookies.txt has been loaded!\n\nYouTube requests will now be authenticated with your account, bypassing the bot check."
                )
            except Exception as e:
                messagebox.showerror("Error", f"Could not import cookies file:\n{e}")

    def show_error_dialog(self, title, err_msg):
        err_lower = err_msg.lower()
        if "confirm you're not a bot" in err_lower or "bot" in err_lower or "429" in err_msg:
            advice = (
                "YouTube Bot Verification Triggered!\n\n"
                "YouTube is temporarily requesting verification for this IP address.\n\n"
                "How to easily fix this:\n"
                "1. If you or your friend are using a VPN or Proxy, turn it OFF.\n"
                "2. If you downloaded multiple videos in a row, wait 2 minutes.\n"
                "3. Or click '🍪 Bypass Bot Check' in the top-right corner to import a cookies.txt file."
            )
            messagebox.showwarning("YouTube Bot Verification", advice)
        else:
            messagebox.showerror(title, f"{err_msg}")

    # ================= SINGLE VIDEO LOGIC =================

    def paste_single_from_clipboard(self):
        try:
            text = self.clipboard_get()
            if text:
                self.single_url_entry.delete(0, "end")
                self.single_url_entry.insert(0, text.strip())
                self.start_single_analyze()
        except Exception:
            pass

    def on_single_media_type_changed(self, value):
        if "Video" in value:
            self.single_media_type = "video"
            self.single_audio_frame.pack_forget()
            self.single_video_frame.pack(fill="x", padx=18, pady=(0, 16))
        else:
            self.single_media_type = "audio"
            self.single_video_frame.pack_forget()
            self.single_audio_frame.pack(fill="x", padx=18, pady=(0, 16))
        self._update_single_download_btn_label()

    def select_single_audio_format(self, fmt):
        self.single_audio_format = fmt
        if fmt == "MP3":
            self.single_mp3_btn.configure(fg_color=COLOR_ACCENT, hover_color=COLOR_ACCENT_HOVER, text_color="#FFFFFF", border_width=0)
            self.single_wav_btn.configure(fg_color=COLOR_GLASS_PILL, hover_color=COLOR_GLASS_HOVER, text_color=COLOR_TEXT_PRIMARY, border_width=1, border_color=COLOR_GLASS_BORDER)
        else:
            self.single_wav_btn.configure(fg_color=COLOR_ACCENT, hover_color=COLOR_ACCENT_HOVER, text_color="#FFFFFF", border_width=0)
            self.single_mp3_btn.configure(fg_color=COLOR_GLASS_PILL, hover_color=COLOR_GLASS_HOVER, text_color=COLOR_TEXT_PRIMARY, border_width=1, border_color=COLOR_GLASS_BORDER)
        self._update_single_download_btn_label()

    def select_single_resolution(self, height):
        self.single_resolution_height = height
        for btn, h in self.single_res_buttons:
            if h == height:
                btn.configure(fg_color=COLOR_ACCENT, hover_color=COLOR_ACCENT_HOVER, text_color="#FFFFFF", border_width=0)
            else:
                btn.configure(fg_color=COLOR_GLASS_PILL, hover_color=COLOR_GLASS_HOVER, text_color=COLOR_TEXT_PRIMARY, border_width=1, border_color=COLOR_GLASS_BORDER)
        self._update_single_download_btn_label()

    def _update_single_download_btn_label(self):
        if self.single_media_type == "video":
            text = f"Download Video (MP4 • {self.single_resolution_height}p)" if self.single_resolution_height else "Download Video (MP4)"
        else:
            text = f"Download Audio ({self.single_audio_format})"
        self.single_download_btn.configure(text=f"⬇ {text}")

    def start_single_analyze(self):
        url = self.single_url_entry.get().strip()
        if not url:
            messagebox.showwarning("Empty Link", "Please enter or paste a valid video URL.")
            return

        if self.is_single_analyzing or self.is_single_downloading:
            return

        # Check if playlist URL
        if downloader.is_playlist_url(url):
            switch = messagebox.askyesno(
                "Playlist Detected",
                "This URL appears to be a Playlist / Set.\n\nWould you like to switch to Playlist / Bulk Download Mode to download all videos?"
            )
            if switch:
                self.mode_switch.set("Playlist & Bulk Download Mode")
                self.on_mode_switched("Playlist & Bulk Download Mode")
                self.bulk_textbox.delete("1.0", "end")
                self.bulk_textbox.insert("1.0", url)
                self.start_bulk_analyze()
                return

        self.is_single_analyzing = True
        self.single_analyze_btn.configure(state="disabled", text="Analyzing...")
        self.single_status_lbl.configure(text="Connecting to media host and inspecting streams...", text_color=COLOR_LIQUID_CYAN)
        self.single_completion_actions.pack_forget()

        threading.Thread(target=self._single_analyze_worker, args=(url,), daemon=True).start()

    def _single_analyze_worker(self, url):
        try:
            info = downloader.extract_video_info(url)
            duration_str = info.get('duration', '')
            thumbnail_image = None
            if info.get('thumbnail'):
                try:
                    resp = requests.get(info['thumbnail'], timeout=10)
                    if resp.status_code == 200:
                        raw_img = Image.open(BytesIO(resp.content)).resize((210, 118), Image.Resampling.LANCZOS)
                        badged_img = add_duration_badge(raw_img, duration_str)
                        thumbnail_image = ctk.CTkImage(light_image=badged_img, dark_image=badged_img, size=(210, 118))
                except Exception:
                    pass

            self.after(0, self._on_single_analyze_success, info, thumbnail_image)
        except Exception as e:
            self.after(0, self._on_single_analyze_error, str(e))

    def _on_single_analyze_success(self, info, thumbnail_image):
        self.is_single_analyzing = False
        self.single_analyze_btn.configure(state="normal", text="Analyze Link")
        self.single_video_info = info

        # Show preview
        self.single_preview_card.pack(fill="x", pady=(0, 14), after=self.single_container.winfo_children()[0])
        self.single_title_lbl.configure(text=info.get('title', 'Unknown Title'))
        self.single_channel_lbl.configure(text=f"Channel: {info.get('channel', 'Unknown')}")
        self.single_duration_lbl.configure(text=f"Duration: {info.get('duration', 'Unknown')}")
        self.single_platform_badge.configure(text=f"Platform: {info.get('platform', 'Online Video')}")

        if thumbnail_image:
            self.single_thumb_label.configure(image=thumbnail_image, text="")
        else:
            self.single_thumb_label.configure(image=None, text="[No Thumbnail]")

        # Render resolution buttons
        for w in self.single_res_grid.winfo_children():
            w.destroy()
        self.single_res_buttons.clear()

        resolutions = info.get('resolutions', [])
        if resolutions:
            cols = 3 if len(resolutions) <= 6 else 4
            for i, r in enumerate(resolutions):
                h = r['height']
                label = r['label']
                row = i // cols
                col = i % cols

                btn = ctk.CTkButton(
                    self.single_res_grid,
                    text=label,
                    height=38,
                    font=ctk.CTkFont(size=12, weight="bold"),
                    fg_color=COLOR_GLASS_PILL,
                    hover_color=COLOR_GLASS_HOVER,
                    text_color=COLOR_TEXT_PRIMARY,
                    border_width=1,
                    border_color=COLOR_GLASS_BORDER,
                    corner_radius=10,
                    command=lambda height=h: self.select_single_resolution(height)
                )
                btn.grid(row=row, column=col, padx=4, pady=4, sticky="ew")
                self.single_res_buttons.append((btn, h))

            for c in range(cols):
                self.single_res_grid.grid_columnconfigure(c, weight=1)

            self.select_single_resolution(resolutions[0]['height'])

        self.single_options_card.pack(fill="x", pady=(0, 14), after=self.single_preview_card)
        self.single_status_lbl.configure(text="✓ Link analyzed successfully! Choose your preferred quality below.", text_color=COLOR_SUCCESS)
        self.single_prog_label.configure(text="Ready to download", text_color=COLOR_SUBTEXT)
        self._update_single_download_btn_label()

    def _on_single_analyze_error(self, err_msg):
        self.is_single_analyzing = False
        self.single_analyze_btn.configure(state="normal", text="Analyze Link")
        self.single_status_lbl.configure(text=f"Error: {err_msg}", text_color="#E53935")
        self.show_error_dialog("Error Analyzing URL", err_msg)

    def start_single_download(self):
        if not self.single_video_info:
            messagebox.showinfo("Analyze First", "Please paste a link and click 'Analyze Link' first.")
            return

        dest_dir = self.single_dest_entry.get().strip()
        if not dest_dir or not os.path.exists(dest_dir):
            try:
                os.makedirs(dest_dir, exist_ok=True)
            except Exception as e:
                messagebox.showerror("Invalid Folder", f"Cannot access download folder:\n{e}")
                return

        if self.is_single_downloading:
            return

        self.is_single_downloading = True
        self.single_download_btn.configure(state="disabled", text="Downloading Media...")
        self.single_completion_actions.pack_forget()
        self.single_prog_bar.set(0)
        self.single_prog_label.configure(text="Starting download and preparing streams...", text_color=COLOR_LIQUID_CYAN)

        media_type = self.single_media_type
        quality_option = self.single_resolution_height or 1080 if media_type == "video" else self.single_audio_format
        url = self.single_video_info['webpage_url']
        is_turbo = self.single_turbo_switch.get() == 1
        threads = 8 if is_turbo else 1

        threading.Thread(
            target=self._single_download_worker,
            args=(url, media_type, quality_option, dest_dir, threads),
            daemon=True
        ).start()

    def _single_progress_hook(self, d):
        status = d.get('status')
        if status == 'downloading':
            percent_str = strip_ansi(d.get('_percent_str', '0%'))
            speed_str = strip_ansi(d.get('_speed_str', 'N/A'))
            eta_str = strip_ansi(d.get('_eta_str', 'N/A'))

            try:
                percent_clean = percent_str.replace('%', '').strip()
                progress_fraction = float(percent_clean) / 100.0
            except Exception:
                progress_fraction = 0.0

            is_turbo = self.single_turbo_switch.get() == 1
            prefix = "⚡ Turbo 8x: " if is_turbo else "Downloading: "
            text_display = f"{prefix}{percent_str}   •   Speed: {speed_str}   •   ETA: {eta_str}"
            self.after(0, self._update_single_progress_ui, progress_fraction, text_display)
        elif status == 'finished':
            self.after(0, self._update_single_progress_ui, 1.0, "Merging and transcoding with FFmpeg...")

    def _update_single_progress_ui(self, fraction, text_display):
        self.single_prog_bar.set(fraction)
        self.single_prog_label.configure(text=text_display, text_color=COLOR_LIQUID_CYAN)

    def _single_download_worker(self, url, media_type, quality_option, dest_dir, threads=8):
        try:
            downloader.download_media(
                url=url,
                media_type=media_type,
                quality_option=quality_option,
                output_path=dest_dir,
                progress_hook=self._single_progress_hook,
                turbo_threads=threads
            )
            self.after(0, self._on_single_download_complete, dest_dir)
        except Exception as e:
            self.after(0, self._on_single_download_error, str(e))

    def _on_single_download_complete(self, dest_dir):
        self.is_single_downloading = False
        self._update_single_download_btn_label()
        self.single_download_btn.configure(state="normal")
        self.single_prog_bar.set(1.0)
        self.single_prog_label.configure(text=f"✓ Completed! File saved to: {dest_dir}", text_color=COLOR_SUCCESS)
        self.single_completion_actions.pack(fill="x", pady=(12, 0))

    def _on_single_download_error(self, err_msg):
        self.is_single_downloading = False
        self._update_single_download_btn_label()
        self.single_download_btn.configure(state="normal")
        self.single_prog_label.configure(text=f"Download failed: {err_msg}", text_color="#E53935")
        self.show_error_dialog("Download Error", err_msg)

    def reset_single_ui(self):
        self.single_url_entry.delete(0, "end")
        self.single_preview_card.pack_forget()
        self.single_options_card.pack_forget()
        self.single_completion_actions.pack_forget()
        self.single_prog_bar.set(0)
        self.single_prog_label.configure(text="Ready to download", text_color=COLOR_SUBTEXT)
        self.single_status_lbl.configure(text="")
        self.single_video_info = None
        self.single_resolution_height = None
        self.single_download_btn.configure(text="Download Media")

    # ================= BULK & PLAYLIST LOGIC =================

    def paste_bulk_from_clipboard(self):
        try:
            text = self.clipboard_get()
            if text:
                self.bulk_textbox.delete("1.0", "end")
                self.bulk_textbox.insert("1.0", text.strip())
                self.start_bulk_analyze()
        except Exception:
            pass

    def on_bulk_media_type_changed(self, value):
        if "Video" in value:
            self.bulk_media_type = "video"
            self.bulk_audio_frame.pack_forget()
            self.bulk_video_frame.pack(fill="x", padx=18, pady=(0, 16))
        else:
            self.bulk_media_type = "audio"
            self.bulk_video_frame.pack_forget()
            self.bulk_audio_frame.pack(fill="x", padx=18, pady=(0, 16))
        self._update_bulk_download_btn_label()

    def select_bulk_resolution(self, q_val):
        self.bulk_quality_option = q_val
        for btn, val in self.bulk_res_buttons:
            if val == q_val:
                btn.configure(fg_color=COLOR_ACCENT, hover_color=COLOR_ACCENT_HOVER, text_color="#FFFFFF", border_width=0)
            else:
                btn.configure(fg_color=COLOR_GLASS_PILL, hover_color=COLOR_GLASS_HOVER, text_color=COLOR_TEXT_PRIMARY, border_width=1, border_color=COLOR_GLASS_BORDER)
        self._update_bulk_download_btn_label()

    def select_bulk_audio_format(self, fmt):
        self.bulk_audio_format = fmt
        if fmt == "MP3":
            self.bulk_mp3_btn.configure(fg_color=COLOR_ACCENT, hover_color=COLOR_ACCENT_HOVER, text_color="#FFFFFF", border_width=0)
            self.bulk_wav_btn.configure(fg_color=COLOR_GLASS_PILL, hover_color=COLOR_GLASS_HOVER, text_color=COLOR_TEXT_PRIMARY, border_width=1, border_color=COLOR_GLASS_BORDER)
        else:
            self.bulk_wav_btn.configure(fg_color=COLOR_ACCENT, hover_color=COLOR_ACCENT_HOVER, text_color="#FFFFFF", border_width=0)
            self.bulk_mp3_btn.configure(fg_color=COLOR_GLASS_PILL, hover_color=COLOR_GLASS_HOVER, text_color=COLOR_TEXT_PRIMARY, border_width=1, border_color=COLOR_GLASS_BORDER)
        self._update_bulk_download_btn_label()

    def _update_bulk_download_btn_label(self):
        count = len(self.bulk_info['items']) if self.bulk_info else 0
        if self.bulk_media_type == "video":
            qual_str = "Auto" if self.bulk_quality_option == "best" else f"{self.bulk_quality_option}p"
            label = f"Start Batch Download ({count} Videos • MP4 {qual_str})"
        else:
            label = f"Start Batch Download ({count} Audio Tracks • {self.bulk_audio_format})"
        self.bulk_download_btn.configure(text=f"⬇ {label}")

    def start_bulk_analyze(self):
        raw_text = self.bulk_textbox.get("1.0", "end").strip()
        if not raw_text:
            messagebox.showwarning("Empty Input", "Please paste a playlist URL or list of video URLs.")
            return

        if self.is_bulk_analyzing or self.is_bulk_downloading:
            return

        self.is_bulk_analyzing = True
        self.bulk_analyze_btn.configure(state="disabled", text="Analyzing...")
        self.bulk_status_lbl.configure(text="Analyzing playlist / batch URLs...", text_color=COLOR_LIQUID_CYAN)
        self.bulk_completion_actions.pack_forget()

        threading.Thread(target=self._bulk_analyze_worker, args=(raw_text,), daemon=True).start()

    def _bulk_analyze_worker(self, raw_text):
        try:
            info = downloader.extract_bulk_or_playlist_info(raw_text)
            self.after(0, self._on_bulk_analyze_success, info)
        except Exception as e:
            self.after(0, self._on_bulk_analyze_error, str(e))

    def _on_bulk_analyze_success(self, info):
        self.is_bulk_analyzing = False
        self.bulk_analyze_btn.configure(state="normal", text="Analyze Playlist / Links")
        self.bulk_info = info

        # Show Queue summary card
        self.bulk_summary_card.pack(fill="x", pady=(0, 14), after=self.bulk_container.winfo_children()[0])
        self.bulk_title_lbl.configure(text=info.get('title', 'Media Queue'))
        count = info.get('count', 0)
        self.bulk_count_badge.configure(text=f"{count} Items")

        # Fill text preview
        preview_lines = []
        for i, item in enumerate(info.get('items', [])):
            dur = f" [{item['duration']}]" if item.get('duration') and item['duration'] != "Unknown" else ""
            preview_lines.append(f"{i+1}. {item['title']}{dur}")
        
        self.bulk_items_preview.configure(state="normal")
        self.bulk_items_preview.delete("1.0", "end")
        self.bulk_items_preview.insert("1.0", "\n".join(preview_lines))
        self.bulk_items_preview.configure(state="disabled")

        # Show options card
        self.bulk_options_card.pack(fill="x", pady=(0, 14), after=self.bulk_summary_card)

        self.bulk_status_lbl.configure(text=f"✓ Successfully identified {count} items for download!", text_color=COLOR_SUCCESS)
        self._update_bulk_download_btn_label()

    def _on_bulk_analyze_error(self, err_msg):
        self.is_bulk_analyzing = False
        self.bulk_analyze_btn.configure(state="normal", text="Analyze Playlist / Links")
        self.bulk_status_lbl.configure(text=f"Error: {err_msg}", text_color="#E53935")
        self.show_error_dialog("Error Analyzing Batch", err_msg)

    def start_bulk_download(self):
        if not self.bulk_info or not self.bulk_info.get('items'):
            messagebox.showinfo("Analyze First", "Please paste links and click 'Analyze' first.")
            return

        dest_dir = self.bulk_dest_entry.get().strip()
        if not dest_dir or not os.path.exists(dest_dir):
            try:
                os.makedirs(dest_dir, exist_ok=True)
            except Exception as e:
                messagebox.showerror("Invalid Folder", f"Cannot access download folder:\n{e}")
                return

        if self.is_bulk_downloading:
            return

        self.is_bulk_downloading = True
        self.bulk_cancel_event.clear()
        self.bulk_download_btn.configure(state="disabled", text="Batch Downloading...")
        self.bulk_cancel_btn.configure(state="normal")
        self.bulk_completion_actions.pack_forget()

        self.bulk_overall_bar.set(0)
        self.bulk_item_bar.set(0)

        media_type = self.bulk_media_type
        quality_option = self.bulk_quality_option if media_type == "video" else self.bulk_audio_format
        items = self.bulk_info['items']
        is_turbo = self.bulk_turbo_switch.get() == 1
        threads = 8 if is_turbo else 1

        threading.Thread(
            target=self._bulk_download_worker,
            args=(items, media_type, quality_option, dest_dir, threads),
            daemon=True
        ).start()

    def cancel_bulk_download(self):
        if self.is_bulk_downloading:
            self.bulk_cancel_event.set()
            self.bulk_cancel_btn.configure(state="disabled", text="Cancelling...")
            self.bulk_item_lbl.configure(text="Cancelling download after current file...", text_color="#E53935")

    def _bulk_overall_hook(self, current, total, title, status):
        fraction = current / total if total > 0 else 0.0
        if status == "finished":
            text = f"Batch Complete: {current} of {total} processed"
        elif status == "cancelled":
            text = f"Batch Cancelled at item {current} of {total}"
        else:
            text = f"Overall Progress: Item {current} of {total} ({int(fraction*100)}%)"

        self.after(0, self._update_bulk_overall_ui, fraction, text, title)

    def _update_bulk_overall_ui(self, fraction, overall_text, current_title):
        self.bulk_overall_bar.set(fraction)
        self.bulk_overall_lbl.configure(text=overall_text)
        self.bulk_item_lbl.configure(text=f"Active Item: {current_title}", text_color=COLOR_TEXT_PRIMARY)
        self.bulk_item_bar.set(0)

    def _bulk_item_hook(self, d):
        status = d.get('status')
        if status == 'downloading':
            percent_str = strip_ansi(d.get('_percent_str', '0%'))
            speed_str = strip_ansi(d.get('_speed_str', 'N/A'))
            eta_str = strip_ansi(d.get('_eta_str', 'N/A'))

            try:
                percent_clean = percent_str.replace('%', '').strip()
                progress_fraction = float(percent_clean) / 100.0
            except Exception:
                progress_fraction = 0.0

            is_turbo = self.bulk_turbo_switch.get() == 1
            prefix = "⚡ Turbo 8x: " if is_turbo else "Downloading: "
            text_display = f"{prefix}{percent_str}   •   Speed: {speed_str}   •   ETA: {eta_str}"
            self.after(0, self._update_bulk_item_ui, progress_fraction, text_display)
        elif status == 'finished':
            self.after(0, self._update_bulk_item_ui, 1.0, "Transcoding & finalizing with FFmpeg...")

    def _update_bulk_item_ui(self, fraction, text_display):
        self.bulk_item_bar.set(fraction)
        self.bulk_item_lbl.configure(text=text_display, text_color=COLOR_LIQUID_CYAN)

    def _bulk_download_worker(self, items, media_type, quality_option, dest_dir, threads=8):
        res = downloader.download_bulk_queue(
            items=items,
            media_type=media_type,
            quality_option=quality_option,
            output_path=dest_dir,
            overall_hook=self._bulk_overall_hook,
            item_hook=self._bulk_item_hook,
            cancel_event=self.bulk_cancel_event,
            turbo_threads=threads
        )
        self.after(0, self._on_bulk_download_complete, res, dest_dir)

    def _on_bulk_download_complete(self, result, dest_dir):
        self.is_bulk_downloading = False
        self._update_bulk_download_btn_label()
        self.bulk_download_btn.configure(state="normal")
        self.bulk_cancel_btn.configure(state="disabled", text="Cancel Queue")

        successful = result.get('successful', 0)
        total = result.get('total', 0)
        failed = result.get('failed', [])

        if self.bulk_cancel_event.is_set():
            status_text = f"Queue stopped. {successful} of {total} items downloaded."
            self.bulk_overall_lbl.configure(text=status_text, text_color="#FFA000")
        elif failed:
            status_text = f"Batch finished: {successful}/{total} downloaded ({len(failed)} failed)."
            self.bulk_overall_lbl.configure(text=status_text, text_color="#FFA000")
        else:
            status_text = f"✓ All {successful} items downloaded successfully!"
            self.bulk_overall_lbl.configure(text=status_text, text_color=COLOR_SUCCESS)

        self.bulk_completion_actions.pack(fill="x", pady=(12, 0))

    def reset_bulk_ui(self):
        self.bulk_textbox.delete("1.0", "end")
        self.bulk_summary_card.pack_forget()
        self.bulk_options_card.pack_forget()
        self.bulk_completion_actions.pack_forget()
        self.bulk_overall_bar.set(0)
        self.bulk_item_bar.set(0)
        self.bulk_overall_lbl.configure(text="Overall Batch Progress: 0%")
        self.bulk_item_lbl.configure(text="Active Item: Ready", text_color=COLOR_SUBTEXT)
        self.bulk_status_lbl.configure(text="")
        self.bulk_info = None
        self._update_bulk_download_btn_label()

def main():
    if "--classic" not in sys.argv:
        try:
            import app_glass
            app_glass.main()
            return
        except Exception as e:
            print(f"Liquid Glass engine encountered an issue ({e}). Launching classic interface...")
    app = YouTubeDownloaderApp()
    app.mainloop()

if __name__ == "__main__":
    main()
