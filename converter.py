import subprocess
import sys
import importlib
import re
import os
import shutil
import tkinter as tk
from tkinter import messagebox

# Dependency Installer
REQUIRED_PACKAGES = {
    "customtkinter": "customtkinter",
    "PIL": "pillow",
    "tkinterdnd2": "tkinterdnd2"
}

# Check for FFmpeg
FFMPEG_PATH = "ffmpeg/ffmpeg.exe"

if not shutil.which("ffmpeg") and not os.path.exists(FFMPEG_PATH):
    root = tk.Tk()
    root.withdraw()  # Hide the main tkinter window
    messagebox.showerror(
        "FFmpeg Required",
        "FFmpeg is required to run this application.\n\n"
        "Please install FFmpeg from:\nhttps://ffmpeg.org/download.html\n\n"
        "Alternatively, bundle FFmpeg inside the app as described in the documentation."
    )
    sys.exit("FFmpeg not found. Exiting application.")

# Use bundled FFmpeg if available
if os.path.exists(FFMPEG_PATH):
    ffmpeg_path = FFMPEG_PATH
else:
    ffmpeg_path = "ffmpeg"  # Assume it's in PATH

def install(package):
    subprocess.check_call([
        sys.executable,
        "-m",
        "pip",
        "install",
        package
    ])

# Auto Checker
missing = []

for module, package in REQUIRED_PACKAGES.items():
    try:
        importlib.import_module(module)
    except ImportError:
        missing.append(package)

if missing:
    print("Installing missing dependencies...")
    for package in missing:
        install(package)

# THEN Import
import customtkinter as ctk
from tkinter import filedialog, messagebox
from tkinterdnd2 import DND_FILES, TkinterDnD
from pathlib import Path
from PIL import Image
import subprocess
import threading
import queue
import os
import time

# =========================================================
# APP CONFIG
# =========================================================

APP_NAME = "ConverToe"

APP_WIDTH = 980
APP_HEIGHT = 760

RADIUS = {
    "xl": 28,
    "lg": 22,
    "md": 16,
    "sm": 12
}

SPACING = {
    "page_x": 34,
    "page_top": 26,
    "page_bottom": 20,
    "section": 18,
    "card_pad": 22,
    "card_gap": 16,
    "stack": 12
}

TYPOGRAPHY = {
    "display": ("Segoe UI Variable", 36, "bold"),
    "heading": ("Segoe UI Variable", 18, "bold"),
    "subheading": ("Segoe UI Variable", 14, "normal"),
    "body": ("Segoe UI Variable", 13, "normal"),
    "meta": ("Segoe UI Variable", 12, "normal"),
    "utility": ("Segoe UI Variable", 11, "normal")
}

TOKENS = {
    "dark": {
        "bg": "#101113",
        "panel": "#16181D",
        "panel_raised": "#1B1E24",
        "panel_soft": "#191B20",
        "border": "#2A2E36",
        "border_soft": "#23272E",
        "text": "#F3F4F6",
        "text_muted": "#A1A9B7",
        "text_subtle": "#7E8796",
        "accent": "#7C95D9",
        "accent_hover": "#8BA4E5",
        "accent_soft": "#22304D",
        "success": "#73B26B",
        "danger": "#D97B7B",
        "shadow": "#0A0B0D"
    },
    "light": {
        "bg": "#F4F1EB",
        "panel": "#FCFAF7",
        "panel_raised": "#FFFFFF",
        "panel_soft": "#F0EDE6",
        "border": "#DDD6CB",
        "border_soft": "#E8E1D7",
        "text": "#1A1D23",
        "text_muted": "#626A78",
        "text_subtle": "#8A909B",
        "accent": "#5E73A8",
        "accent_hover": "#6D84B8",
        "accent_soft": "#DDE5F4",
        "success": "#5F8E58",
        "danger": "#B86D6D",
        "shadow": "#D7D1C6"
    }
}

VIDEO_EXTENSIONS = {
    ".mp4",
    ".mov",
    ".mkv",
    ".avi",
    ".webm",
    ".flv"
}

IMAGE_EXTENSIONS = {
    ".png",
    ".jpg",
    ".jpeg",
    ".webp",
    ".bmp",
    ".tiff"
}

VIDEO_OUTPUTS = [
    "mp3",
    "wav",
    "flac",
    "aac"
]

IMAGE_OUTPUTS = [
    "png",
    "jpeg",
    "webp",
    "pdf"
]

# =========================================================
# THEME
# =========================================================

ctk.set_appearance_mode("system")
ctk.set_default_color_theme("blue")

COLORS = {
    key: (TOKENS["light"][key], TOKENS["dark"][key])
    for key in TOKENS["dark"]
}

# =========================================================
# HELPERS
# =========================================================

def format_size(size):
    for unit in ["B", "KB", "MB", "GB"]:
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"


def is_video(path):
    return Path(path).suffix.lower() in VIDEO_EXTENSIONS


def is_image(path):
    return Path(path).suffix.lower() in IMAGE_EXTENSIONS


def get_media_type(path):

    if is_video(path):
        return "video"

    if is_image(path):
        return "image"

    return None


def ffmpeg_exists():

    try:

        subprocess.run(
            ["ffmpeg", "-version"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        return True

    except FileNotFoundError:

        return False


# =========================================================
# MAIN APP
# =========================================================

class ConverToe(TkinterDnD.Tk):

    def __init__(self):

        super().__init__()

        self.title(APP_NAME)
        self.geometry(f"{APP_WIDTH}x{APP_HEIGHT}")
        self.minsize(APP_WIDTH, APP_HEIGHT)

        self.configure(bg=self.resolve_color("bg"))

        self.file_path = None
        self.output_dir = None
        self.media_type = None
        self.appearance_choice = "System"

        self.ui_queue = queue.Queue()

        self.setup_ui()

        self.after(50, self.process_ui_queue)

    def resolve_color(self, key):

        mode = ctk.get_appearance_mode()

        index = 1 if mode == "Dark" else 0

        return COLORS[key][index]

    def set_appearance(self, choice):

        self.appearance_choice = choice

        mapped = {
            "Auto": "System",
            "Light": "Light",
            "Dark": "Dark"
        }.get(choice, "System")

        ctk.set_appearance_mode(mapped)

        self.configure(bg=self.resolve_color("bg"))

        self.status(f"Appearance set to {choice.lower()}")

    # =====================================================
    # UI
    # =====================================================

    def setup_ui(self):

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.main_container = ctk.CTkFrame(
            self,
            fg_color=COLORS["bg"]
        )

        self.main_container.grid(
            row=0,
            column=0,
            sticky="nsew"
        )

        self.main_container.grid_rowconfigure(0, weight=1)
        self.main_container.grid_rowconfigure(1, weight=0)
        self.main_container.grid_columnconfigure(0, weight=1)

        self.content = ctk.CTkScrollableFrame(
            self.main_container,
            fg_color=COLORS["bg"],
            scrollbar_button_color=COLORS["accent"],
            scrollbar_button_hover_color=COLORS["accent_hover"]
        )

        self.content.grid(
            row=0,
            column=0,
            sticky="nsew"
        )

        self.content.grid_columnconfigure(0, weight=1)

        # =================================================
        # HEADER
        # =================================================

        self.header = ctk.CTkFrame(
            self.content,
            fg_color="transparent"
        )

        self.header.pack(
            fill="x",
            padx=SPACING["page_x"],
            pady=(SPACING["page_top"], 18)
        )

        self.header.grid_columnconfigure(0, weight=1)
        self.header.grid_columnconfigure(1, weight=0)

        self.hero = ctk.CTkFrame(
            self.header,
            fg_color="transparent"
        )

        self.hero.grid(row=0, column=0, sticky="w")

        self.app_chip = ctk.CTkLabel(
            self.hero,
            text="DESKTOP CONVERTER",
            text_color=COLORS["text_subtle"],
            font=ctk.CTkFont(family=TYPOGRAPHY["utility"][0], size=10, weight="bold")
        )

        self.app_chip.pack(anchor="w", pady=(0, 8))

        self.title_label = ctk.CTkLabel(
            self.hero,
            text="ConverToe.",
            font=ctk.CTkFont(
                family=TYPOGRAPHY["display"][0],
                size=TYPOGRAPHY["display"][1],
                weight="bold"
            ),
            text_color=COLORS["text"]
        )

        self.title_label.pack(anchor="w")

        self.subtitle_label = ctk.CTkLabel(
            self.hero,
            text="A calm, precise media conversion workspace.",
            font=ctk.CTkFont(
                family=TYPOGRAPHY["subheading"][0],
                size=TYPOGRAPHY["subheading"][1]
            ),
            text_color=COLORS["text_muted"]
        )

        self.subtitle_label.pack(
            anchor="w",
            pady=(10, 0)
        )

        self.mode_shell = ctk.CTkFrame(
            self.header,
            fg_color=COLORS["panel_soft"],
            border_width=1,
            border_color=COLORS["border_soft"],
            corner_radius=18
        )

        self.mode_shell.grid(row=0, column=1, sticky="e")

        self.mode_chip = ctk.CTkLabel(
            self.mode_shell,
            text="Appearance",
            text_color=COLORS["text_subtle"],
            font=ctk.CTkFont(family=TYPOGRAPHY["utility"][0], size=10, weight="bold")
        )

        self.mode_chip.pack(anchor="w", padx=14, pady=(10, 6))

        self.mode_toggle = ctk.CTkSegmentedButton(
            self.mode_shell,
            values=["Auto", "Light", "Dark"],
            command=self.set_appearance,
            fg_color=COLORS["panel"],
            selected_color=COLORS["accent"],
            selected_hover_color=COLORS["accent_hover"],
            unselected_color=COLORS["panel_soft"],
            unselected_hover_color=COLORS["panel_raised"],
            text_color=COLORS["text"],
            font=ctk.CTkFont(family=TYPOGRAPHY["meta"][0], size=TYPOGRAPHY["meta"][1])
        )

        self.mode_toggle.pack(fill="x", padx=14, pady=(0, 12))
        self.mode_toggle.set("Auto")

        self.mode_toggle.configure(
            border_width=0
        )

        # =================================================
        # DROP ZONE
        # =================================================

        self.drop_zone = ctk.CTkFrame(
            self.content,
            fg_color=COLORS["panel"],
            border_width=1,
            border_color=COLORS["border_soft"],
            corner_radius=RADIUS["xl"],
            height=252
        )

        self.drop_zone.pack(
            fill="x",
            padx=SPACING["page_x"],
            pady=(0, SPACING["section"])
        )

        self.drop_zone.pack_propagate(False)

        self.drop_zone.drop_target_register(DND_FILES)

        self.drop_zone.dnd_bind(
            "<<Drop>>",
            self.handle_drop
        )

        self.drop_zone.bind(
            "<Enter>",
            lambda e: self.drop_zone.configure(
                border_color=COLORS["accent"]
            )
        )

        self.drop_zone.bind(
            "<Leave>",
            lambda e: self.drop_zone.configure(
                border_color=COLORS["border"]
            )
        )

        self.drop_content = ctk.CTkFrame(
            self.drop_zone,
            fg_color="transparent"
        )

        self.drop_content.pack(expand=True)

        self.drop_icon = ctk.CTkLabel(
            self.drop_content,
            text="◌",
            font=ctk.CTkFont(size=56, weight="bold"),
            text_color=COLORS["accent"]
        )

        self.drop_icon.pack(pady=(0, 10))

        self.drop_title = ctk.CTkLabel(
            self.drop_content,
            text="Drag & Drop Media",
            font=ctk.CTkFont(family=TYPOGRAPHY["heading"][0], size=26, weight="bold")
        )

        self.drop_title.pack()

        self.drop_subtitle = ctk.CTkLabel(
            self.drop_content,
            text="Drop a video or image, or browse for a file.",
            text_color=COLORS["text_muted"],
            font=ctk.CTkFont(family=TYPOGRAPHY["body"][0], size=TYPOGRAPHY["body"][1])
        )

        self.drop_subtitle.pack(pady=(6, 18))

        self.browse_btn = ctk.CTkButton(
            self.drop_content,
            text="Browse Files",
            command=self.select_file,
            height=42,
            width=182,
            corner_radius=15,
            font=ctk.CTkFont(family=TYPOGRAPHY["body"][0], size=14, weight="bold"),
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            text_color=COLORS["text"]
        )

        self.browse_btn.pack()

        # =================================================
        # INFO CARD
        # =================================================

        self.info_card = ctk.CTkFrame(
            self.content,
            fg_color=COLORS["panel"],
            corner_radius=RADIUS["lg"],
            border_width=1,
            border_color=COLORS["border_soft"]
        )

        self.info_card.pack(
            fill="x",
            padx=SPACING["page_x"],
            pady=(0, SPACING["section"])
        )

        self.file_name = self.create_info_row(
            "File",
            "No file selected"
        )

        self.file_size = self.create_info_row(
            "Size",
            "-"
        )

        self.file_type = self.create_info_row(
            "Type",
            "-"
        )

        # =================================================
        # SETTINGS PANEL
        # =================================================

        self.settings_card = ctk.CTkFrame(
            self.content,
            fg_color=COLORS["panel"],
            corner_radius=RADIUS["lg"],
            border_width=1,
            border_color=COLORS["border_soft"]
        )

        self.settings_card.pack(
            fill="x",
            padx=SPACING["page_x"],
            pady=(0, SPACING["section"])
        )

        self.settings_inner = ctk.CTkFrame(
            self.settings_card,
            fg_color="transparent"
        )

        self.settings_inner.pack(
            fill="x",
            padx=SPACING["card_pad"],
            pady=SPACING["card_pad"]
        )

        # FORMAT

        self.format_label = ctk.CTkLabel(
            self.settings_inner,
            text="Output Format",
            font=ctk.CTkFont(family=TYPOGRAPHY["heading"][0], size=14, weight="bold")
        )

        self.format_label.pack(anchor="w")

        self.format_var = ctk.StringVar(value="mp3")

        self.format_menu = ctk.CTkOptionMenu(
            self.settings_inner,
            variable=self.format_var,
            values=VIDEO_OUTPUTS,
            height=42,
            corner_radius=14,
            font=ctk.CTkFont(family=TYPOGRAPHY["body"][0], size=13),
            dropdown_font=ctk.CTkFont(family=TYPOGRAPHY["body"][0], size=13),
            fg_color=COLORS["panel_soft"],
            button_color=COLORS["accent"],
            button_hover_color=COLORS["accent_hover"],
            text_color=COLORS["text"]
        )

        self.format_menu.pack(
            fill="x",
            pady=(10, 20)
        )

        # OUTPUT FOLDER

        self.output_btn = ctk.CTkButton(
            self.settings_inner,
            text="Choose Output Folder",
            command=self.select_output_dir,
            height=42,
            corner_radius=14,
            font=ctk.CTkFont(family=TYPOGRAPHY["body"][0], size=13, weight="bold"),
            fg_color=COLORS["panel_soft"],
            hover_color=COLORS["panel_raised"],
            text_color=COLORS["text"]
        )

        self.output_btn.pack(fill="x")

        self.output_label = ctk.CTkLabel(
            self.settings_inner,
            text="Default: Same folder as source",
            text_color=COLORS["text_muted"],
            font=ctk.CTkFont(family=TYPOGRAPHY["meta"][0], size=TYPOGRAPHY["meta"][1])
        )

        self.output_label.pack(
            anchor="w",
            pady=(8, 0)
        )

        # =================================================
        # PROGRESS CARD
        # =================================================

        self.progress_card = ctk.CTkFrame(
            self.content,
            fg_color=COLORS["panel"],
            corner_radius=RADIUS["lg"],
            border_width=1,
            border_color=COLORS["border_soft"]
        )

        self.progress_card.pack(
            fill="x",
            padx=SPACING["page_x"],
            pady=(0, SPACING["page_bottom"])
        )

        self.progress_inner = ctk.CTkFrame(
            self.progress_card,
            fg_color="transparent"
        )

        self.progress_inner.pack(fill="x", padx=24, pady=24)

        self.progress_bar = ctk.CTkProgressBar(
            self.progress_inner,
            height=12,
            corner_radius=8,
            fg_color=COLORS["panel_soft"],
            progress_color=COLORS["accent"]
        )

        self.progress_bar.pack(fill="x")

        self.progress_bar.set(0)

        self.status_label = ctk.CTkLabel(
            self.progress_inner,
            text="Ready",
            text_color=COLORS["text_muted"],
            font=ctk.CTkFont(family=TYPOGRAPHY["meta"][0], size=TYPOGRAPHY["meta"][1])
        )

        self.status_label.pack(
            anchor="w",
            pady=(12, 0)
        )

        # percentage label for progress
        self.progress_percent = ctk.CTkLabel(
            self.progress_inner,
            text="0%",
            text_color=COLORS["text_muted"],
            font=ctk.CTkFont(family=TYPOGRAPHY["utility"][0], size=TYPOGRAPHY["utility"][1])
        )

        self.progress_percent.pack(anchor="e", pady=(6, 0))

        # =================================================
        # ACTION BAR
        # =================================================

        self.footer = ctk.CTkFrame(
            self.main_container,
            fg_color=COLORS["panel"],
            border_width=1,
            border_color=COLORS["border_soft"],
            corner_radius=RADIUS["lg"]
        )

        self.footer.grid(
            row=1,
            column=0,
            sticky="ew",
            padx=SPACING["page_x"],
            pady=(0, 18)
        )

        self.footer.grid_columnconfigure(0, weight=1)

        self.footer_inner = ctk.CTkFrame(
            self.footer,
            fg_color="transparent"
        )

        self.footer_inner.pack(fill="x", padx=20, pady=16)

        self.action_hint = ctk.CTkLabel(
            self.footer_inner,
            text="Load a file to unlock conversion.",
            text_color=COLORS["text_muted"],
            font=ctk.CTkFont(family=TYPOGRAPHY["utility"][0], size=TYPOGRAPHY["utility"][1])
        )

        self.action_hint.pack(anchor="w", pady=(0, 10))

        self.convert_btn = ctk.CTkButton(
            self.footer_inner,
            text="Convert Media",
            command=self.start_conversion,
            height=50,
            corner_radius=16,
            font=ctk.CTkFont(family=TYPOGRAPHY["heading"][0], size=16, weight="bold"),
            state="disabled",
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            text_color=COLORS["text"]
        )

        self.convert_btn.pack(fill="x")

        # best-effort: older CTK versions may not support some options
        try:
            self.convert_btn.configure(
                border_width=2,
                border_color=COLORS["border"]
            )
        except Exception:
            pass

    # =====================================================
    # INFO ROW
    # =====================================================

    def create_info_row(self, title, value):

        row = ctk.CTkFrame(
            self.info_card,
            fg_color="transparent"
        )

        row.pack(
            fill="x",
            padx=24,
            pady=10
        )

        label = ctk.CTkLabel(
            row,
            text=title,
            width=88,
            anchor="w",
            text_color=COLORS["text_muted"],
            font=ctk.CTkFont(family=TYPOGRAPHY["utility"][0], size=TYPOGRAPHY["utility"][1], weight="bold")
        )

        label.pack(side="left")

        value_label = ctk.CTkLabel(
            row,
            text=value,
            anchor="w",
            font=ctk.CTkFont(family=TYPOGRAPHY["body"][0], size=14, weight="bold")
        )

        value_label.pack(side="left")

        return value_label

    # =====================================================
    # FILE SELECTION
    # =====================================================

    def select_file(self):

        filetypes = [
            (
                "Media Files",
                "*.mp4 *.mov *.avi *.mkv *.webm *.png *.jpg *.jpeg *.webp"
            ),
            ("All Files", "*.*")
        ]

        path = filedialog.askopenfilename(
            filetypes=filetypes
        )

        if path:
            self.load_file(path)

    def handle_drop(self, event):

        path = event.data.strip("{}")

        if os.path.isfile(path):
            self.load_file(path)

    def load_file(self, path):

        media_type = get_media_type(path)

        if not media_type:

            messagebox.showerror(
                "Unsupported File",
                "Unsupported media format."
            )

            return

        self.file_path = path
        self.media_type = media_type

        file = Path(path)

        self.file_name.configure(
            text=file.name
        )

        self.file_size.configure(
            text=format_size(file.stat().st_size)
        )

        self.file_type.configure(
            text=media_type.upper()
        )

        self.update_output_formats()

        self.convert_btn.configure(
            state="normal"
        )

        self.action_hint.configure(
            text=f"Ready to convert {media_type}. Choose output format and folder, then start."
        )

        self.status(
            "Media loaded successfully"
        )

    # =====================================================
    # FORMAT MANAGEMENT
    # =====================================================

    def update_output_formats(self):

        if self.media_type == "video":

            self.format_menu.configure(
                values=VIDEO_OUTPUTS
            )

            self.format_var.set("mp3")

        else:

            self.format_menu.configure(
                values=IMAGE_OUTPUTS
            )

            self.format_var.set("png")

    # =====================================================
    # OUTPUT DIRECTORY
    # =====================================================

    def select_output_dir(self):

        folder = filedialog.askdirectory()

        if folder:

            self.output_dir = folder

            self.output_label.configure(
                text=folder
            )

    # =====================================================
    # CONVERSION
    # =====================================================

    def start_conversion(self):

        if not self.file_path:
            return

        if not ffmpeg_exists():

            messagebox.showerror(
                "FFmpeg Missing",
                "FFmpeg is not installed or not added to PATH."
            )

            return

        self.convert_btn.configure(
            state="disabled"
        )

        self.action_hint.configure(
            text="Conversion in progress. The button will re-enable when finished."
        )

        self.progress_bar.set(0)
        try:
            self.progress_percent.configure(text="0%")
        except Exception:
            pass

        thread = threading.Thread(
            target=self.convert_worker,
            daemon=True
        )

        thread.start()

    def convert_worker(self):

        try:

            self.queue_ui(
                lambda: self.status("Converting...")
            )

            source = Path(self.file_path)

            ext = self.format_var.get()

            output_dir = (
                Path(self.output_dir)
                if self.output_dir
                else source.parent
            )

            output_path = output_dir / f"{source.stem}.{ext}"

            if self.media_type == "video":

                self.convert_video(
                    source,
                    output_path,
                    ext
                )

            else:

                self.convert_image(
                    source,
                    output_path,
                    ext
                )

            # conversion functions update progress themselves

        except Exception as e:

            self.queue_ui(
                lambda: self.status(
                    f"Error • {str(e)}"
                )
            )

        finally:

            self.queue_ui(
                lambda: self.convert_btn.configure(
                    state="normal"
                )
            )

            self.queue_ui(
                lambda: self.action_hint.configure(
                    text="Ready for another conversion."
                )
            )

    # =====================================================
    # VIDEO CONVERSION
    # =====================================================

    def convert_video(self, source, output_path, ext):

        codec_args = []

        if ext == "mp3":

            codec_args = [
                "-vn",
                "-acodec",
                "libmp3lame"
            ]

        elif ext == "wav":

            codec_args = [
                "-vn"
            ]

        elif ext == "flac":

            codec_args = [
                "-vn",
                "-acodec",
                "flac"
            ]

        elif ext == "aac":

            output_path = output_path.with_suffix(".m4a")

            codec_args = [
                "-vn",
                "-c:a",
                "aac",
                "-b:a",
                "192k"
            ]

        # determine ffmpeg/ffprobe executables
        ffmpeg_exec = ffmpeg_path if ffmpeg_path else "ffmpeg"
        ffprobe_exec = None

        bundled_probe = os.path.join(os.path.dirname(FFMPEG_PATH), "ffprobe.exe")
        if os.path.exists(bundled_probe):
            ffprobe_exec = bundled_probe
        elif shutil.which("ffprobe"):
            ffprobe_exec = "ffprobe"

        def probe_duration(src):
            if not ffprobe_exec:
                return None
            try:
                res = subprocess.run(
                    [ffprobe_exec, "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", str(src)],
                    capture_output=True,
                    text=True
                )
                return float(res.stdout.strip())
            except Exception:
                return None

        duration = probe_duration(source)

        command = [
            ffmpeg_exec,
            "-y",
            "-i",
            str(source),
            *codec_args,
            str(output_path)
        ]

        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )

        time_re = re.compile(r"time=(\d+):(\d+):(\d+\.?\d*)")

        for line in process.stderr:
            # attempt to parse ffmpeg time progress
            m = time_re.search(line)
            if m and duration:
                h, mm, ss = m.groups()
                seconds = int(h) * 3600 + int(mm) * 60 + float(ss)
                frac = max(0.0, min(seconds / duration, 1.0))

                def _update(p=frac, s=seconds):
                    try:
                        self.progress_bar.set(p)
                        self.progress_percent.configure(text=f"{int(p*100)}%")
                        self.status(f"Converting... {int(p*100)}%")
                    except Exception:
                        pass

                self.queue_ui(_update)

            else:
                # if no duration available, do a gentle step so user sees activity
                self.queue_ui(lambda: self.progress_bar.set(min(self.progress_bar.get() + 0.005, 0.98)))

        process.wait()

        # finalize UI
        self.queue_ui(lambda: self.progress_bar.set(1.0))
        self.queue_ui(lambda: self.progress_percent.configure(text="100%"))
        self.queue_ui(lambda: self.status(f"Finished • {output_path.name}"))

    # =====================================================
    # IMAGE CONVERSION
    # =====================================================

    def convert_image(self, source, output_path, ext):

        img = Image.open(source)

        if ext == "pdf":

            rgb = img.convert("RGB")

            rgb.save(
                output_path,
                "PDF",
                resolution=300.0
            )

        else:

            if ext in ["jpeg", "jpg"]:

                if img.mode in ("RGBA", "P"):

                    img = img.convert("RGB")

            img.save(output_path)

        # update UI for images (quick completion)
        self.queue_ui(lambda: self.progress_bar.set(1.0))
        self.queue_ui(lambda: self.progress_percent.configure(text="100%"))
        self.queue_ui(lambda: self.status(f"Finished • {output_path.name}"))

    # =====================================================
    # THREAD SAFE UI
    # =====================================================

    def queue_ui(self, callback):

        self.ui_queue.put(callback)

    def process_ui_queue(self):

        while not self.ui_queue.empty():

            callback = self.ui_queue.get()

            callback()

        self.after(
            50,
            self.process_ui_queue
        )

    # =====================================================
    # STATUS
    # =====================================================

    def status(self, text):

        status_color = COLORS["text_muted"]

        lowered = text.lower()

        if "error" in lowered or "missing" in lowered or "unsupported" in lowered:
            status_color = COLORS["danger"]
        elif "finished" in lowered or "loaded" in lowered:
            status_color = COLORS["success"]
        elif "converting" in lowered:
            status_color = COLORS["accent"]

        self.status_label.configure(
            text=text,
            text_color=status_color
        )


# =========================================================
# START APP
# =========================================================

if __name__ == "__main__":

    app = ConverToe()

    app.mainloop()