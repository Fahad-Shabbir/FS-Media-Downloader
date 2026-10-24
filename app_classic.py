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
COLOR_CANVAS_BG = ("#F0F3F8", "#0B0E14")
COLOR_GLASS_CARD = ("#FFFFFF", "#161B22")
COLOR_GLASS_BORDER = ("#D8DEE4", "#30363D")
COLOR_GLASS_INPUT = ("#F6F8FA", "#0D1117")
COLOR_GLASS_HOVER = ("#E6EBF1", "#21262D")
COLOR_GLASS_PILL = ("#EFF2F6", "#21262D")
COLOR_SUBTEXT = ("#57606A", "#8B949E")
COLOR_TEXT_PRIMARY = ("#1F2328", "#FFFFFF")
COLOR_ACCENT = "#E50914"
COLOR_ACCENT_HOVER = "#B80710"
COLOR_LIQUID_CYAN = ("#0969DA", "#00D2FF")
COLOR_TURBO_GOLD = ("#B45309", "#FFB300")
COLOR_TURBO_HOVER = ("#92400E", "#FFA000")
COLOR_SUCCESS = ("#1A7F37", "#00E676")
COLOR_SUCCESS_HOVER = ("#14632B", "#00C853")
COLOR_DANGER = ("#CF222E", "#FF1744")
COLOR_DANGER_HOVER = ("#A41B24", "#D50000")

ANSI_ESCAPE = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')

def strip_ansi(text):
    if not text:
        return ""
    return ANSI_ESCAPE.sub('', text).strip()

def apply_liquid_backdrop(window, dark=True):
    try:
        import ctypes
        hwnd = ctypes.windll.user32.GetParent(window.winfo_id())
        if not hwnd:
            hwnd = window.winfo_id()
        dark_mode = ctypes.c_int(1 if dark else 0)
        ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 20, ctypes.byref(dark_mode), ctypes.sizeof(dark_mode))
        backdrop = ctypes.c_int(3)
        res = ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 38, ctypes.byref(backdrop), ctypes.sizeof(backdrop))
        if res != 0:
            mica = ctypes.c_int(1)
            ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 1029, ctypes.byref(mica), ctypes.sizeof(mica))
    except Exception:
        pass

def add_duration_badge(image, duration_str):
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

class FSMediaDownloaderApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("FS Media Downloader - by Fahad Shabbir")
        self.geometry("930x870")
        self.minsize(840, 750)
        self.configure(fg_color=COLOR_CANVAS_BG)
        self.after(150, lambda: apply_liquid_backdrop(self, dark=True))
        self.default_download_dir = str(Path.home() / "Downloads")
        self.active_mode = "single"
        self.single_video_info = None
        self.bulk_info = None
        self.is_single_downloading = False
        self.is_bulk_downloading = False
        self.cancel_event = threading.Event()
        self.bulk_cancel_event = threading.Event()
        self.pause_event = threading.Event()
        self.pause_event.set()
        self.is_paused = False
        self._build_ui()

    def _build_ui(self):
        self.scroll_canvas = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll_canvas.pack(fill="both", expand=True, padx=25, pady=25)
        self.center_box = ctk.CTkFrame(self.scroll_canvas, fg_color="transparent", width=860)
        self.center_box.pack(fill="x", expand=True)
        self._build_header()
        self._build_tabs()
        self._build_single_section()
        self._build_folder_selector()
        self._build_action_buttons()
        self._build_progress_card()
        self._build_footer()

    def _build_header(self):
        header_card = ctk.CTkFrame(self.center_box, fg_color=COLOR_GLASS_CARD, corner_radius=18, border_width=1, border_color=COLOR_GLASS_BORDER)
        header_card.pack(fill="x", pady=(0, 16))
        header_layout = ctk.CTkFrame(header_card, fg_color="transparent")
        header_layout.pack(fill="x", padx=20, pady=16)
        title_row = ctk.CTkFrame(header_layout, fg_color="transparent")
        title_row.pack(side="left")
        play_badge = ctk.CTkButton(title_row, text="▶", font=ctk.CTkFont(size=14, weight="bold"), width=34, height=34, fg_color=COLOR_ACCENT, hover_color=COLOR_ACCENT, corner_radius=10, state="disabled")
        play_badge.pack(side="left", padx=(0, 12))
        title_lbl = ctk.CTkLabel(title_row, text="FS Media Downloader", font=ctk.CTkFont(size=22, weight="bold"), text_color=COLOR_TEXT_PRIMARY)
        title_lbl.pack(side="left")
        creator_badge = ctk.CTkLabel(title_row, text="by Fahad Shabbir", font=ctk.CTkFont(size=11, weight="bold"), text_color="#FF4D4D", fg_color=("#FDE8E8", "#2D1517"), corner_radius=8, padx=8, pady=3)
        creator_badge.pack(side="left", padx=(10, 0))

    def _build_tabs(self):
        pass

    def _build_single_section(self):
        pass

    def _build_folder_selector(self):
        pass

    def _build_action_buttons(self):
        pass

    def _build_progress_card(self):
        pass

    def _build_footer(self):
        footer_frame = ctk.CTkFrame(self.center_box, fg_color="transparent")
        footer_frame.pack(fill="x", pady=(0, 15))
        footer_lbl = ctk.CTkLabel(footer_frame, text="FS Media Downloader  •  Designed & Developed by Fahad Shabbir", font=ctk.CTkFont(size=11), text_color=COLOR_SUBTEXT)
        footer_lbl.pack(anchor="center")

def main():
    app = FSMediaDownloaderApp()
    app.mainloop()

if __name__ == "__main__":
    main()
