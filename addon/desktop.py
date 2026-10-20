# Verbindung zum Desktop: Akzentfarbe des Systems, aktuelles Hintergrundbild (auch Live-
# und Diashow-Wallpaper als Standbild) und dessen kräftigste Farbe. Alles ist "best effort":
# klappt etwas nicht, kommt None zurück und die bisherigen Einstellungen bleiben.
import colorsys
import configparser
import glob
import hashlib
import os
import re
import shutil
import subprocess
import sys
from urllib.parse import unquote, urlparse

from aqt.qt import QColor, QImage, Qt

GNOME_ACCENTS = {"blue": "#3584e4", "teal": "#2190a4", "green": "#3a944a", "yellow": "#c88800",
                 "orange": "#ed5b00", "red": "#e62d42", "pink": "#d56199", "purple": "#9141ac", "slate": "#6f8396"}
MAC_ACCENTS = {-1: "#8c8c8c", 0: "#ff5257", 1: "#f7821b", 2: "#ffc600", 3: "#62ba46",
               4: "#007aff", 5: "#a550a7", 6: "#f74f9e"}
IMAGE_EXTS = (".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp", ".avif", ".jxl", ".heic")
VIDEO_EXTS = (".mp4", ".webm", ".mkv", ".mov", ".avi", ".m4v")
MAX_WIDTH = 2560  # größer braucht kein Hintergrund, spart Speicher und Ladezeit


def _run(cmd, timeout=2):
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout).stdout.strip()
    except Exception:
        return ""


def _kde_rgb(value):
    return "#%02x%02x%02x" % tuple(int(x) for x in value.split(",")[:3])


def _is_kde():
    return bool(os.environ.get("KDE_FULL_SESSION")) or "KDE" in os.environ.get("XDG_CURRENT_DESKTOP", "")


def _ini(path):
    cp = configparser.ConfigParser(interpolation=None, strict=False)
    cp.optionxform = str
    try:
        cp.read(path, encoding="utf-8")
    except Exception:
        pass
    return cp


# ---------- Systemakzent ----------

def system_accent():
    try:
        if sys.platform == "win32":
            import winreg
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\DWM") as k:
                abgr = winreg.QueryValueEx(k, "AccentColor")[0]
            return "#%02x%02x%02x" % (abgr & 0xFF, (abgr >> 8) & 0xFF, (abgr >> 16) & 0xFF)
        if sys.platform == "darwin":
            out = _run(["defaults", "read", "-g", "AppleAccentColor"])
            return MAC_ACCENTS.get(int(out) if out.lstrip("-").isdigit() else 4)
        if _is_kde():
            cp = _ini(os.path.expanduser("~/.config/kdeglobals"))
            if cp.has_option("General", "AccentColor"):
                return _kde_rgb(cp.get("General", "AccentColor"))
            if cp.has_option("Colors:Selection", "BackgroundNormal"):
                return _kde_rgb(cp.get("Colors:Selection", "BackgroundNormal"))
        name = _run(["gsettings", "get", "org.gnome.desktop.interface", "accent-color"]).strip("'")
        if name in GNOME_ACCENTS:
            return GNOME_ACCENTS[name]
    except Exception:
        pass
    return None


# ---------- Hintergrundbild finden ----------

def _to_path(value):
    value = value.strip().strip("'\"")
    if value.startswith("file://"):
        value = unquote(urlparse(value).path)
    return os.path.expanduser(value) if value.startswith(("/", "~")) or re.match(r"^[A-Za-z]:\\", value) else None


def _media_in_dir(path, night):
    """Ordner auflösen: KDE-Wallpaper-Paket (contents/images[_dark]), Wallpaper-Engine-Projekt
    (preview.*) oder einfach das größte Bild darin."""
    dirs = ["contents/images_dark", "contents/images"] if night else ["contents/images", "contents/images_dark"]
    for d in dirs + [""]:
        full = os.path.join(path, d)
        if not os.path.isdir(full):
            continue
        for name in ("preview.jpg", "preview.png", "preview.gif"):
            if os.path.isfile(os.path.join(full, name)):
                return os.path.join(full, name)
        files = [os.path.join(full, f) for f in os.listdir(full) if f.lower().endswith(IMAGE_EXTS + VIDEO_EXTS)]
        if files:
            return max(files, key=os.path.getsize)
    return None


def _resolve(path, night):
    if not path:
        return None
    if os.path.isdir(path):
        return _media_in_dir(path, night)
    if path.lower().endswith(".xml"):  # GNOME-Diashow: erstes Bild nehmen
        try:
            m = re.search(r"<file>\s*([^<]+?)\s*</file>", open(path, encoding="utf-8").read())
            return m.group(1) if m and os.path.isfile(m.group(1)) else None
        except Exception:
            return None
    return path if os.path.isfile(path) else None


def _kde_wallpaper(night):
    cp = _ini(os.path.expanduser("~/.config/plasma-org.kde.plasma.desktop-appletsrc"))
    desktops = []
    for sec in cp.sections():
        m = re.fullmatch(r"Containments\]\[(\d+)", sec)
        if m and cp.has_option(sec, "wallpaperplugin"):
            screen = cp.get(sec, "lastScreen", fallback="99")
            desktops.append((int(screen) if screen.isdigit() else 99, m.group(1), cp.get(sec, "wallpaperplugin")))
    for _screen, cid, plugin in sorted(desktops):
        general = f"Containments][{cid}][Wallpaper][{plugin}][General"
        if not cp.has_section(general):
            continue
        keys = ["Image"] if plugin == "org.kde.image" else list(cp.options(general))
        if plugin == "org.kde.slideshow":
            # Diashow: KDE merkt sich das aktuelle Bild nicht, also das zuletzt geänderte aus den Ordnern
            folders = [_to_path(p) for p in cp.get(general, "SlidePaths", fallback="").split(",")]
            files = [f for d in folders if d and os.path.isdir(d)
                     for f in glob.glob(os.path.join(d, "**", "*"), recursive=True) if f.lower().endswith(IMAGE_EXTS)]
            if files:
                return max(files, key=os.path.getmtime)
            continue
        # Bild-Plugin und Live-Wallpaper (Video, Wallpaper Engine, ...): alle Werte nach Pfaden absuchen
        for key in keys:
            for value in cp.get(general, key, fallback="").split(","):
                found = _resolve(_to_path(value), night)
                if found and found.lower().endswith(IMAGE_EXTS + VIDEO_EXTS):
                    return found
    return None


def wallpaper_path(night=False):
    try:
        if sys.platform == "win32":
            import ctypes
            buf = ctypes.create_unicode_buffer(512)
            ctypes.windll.user32.SystemParametersInfoW(0x73, len(buf), buf, 0)
            return _resolve(buf.value, night)
        if sys.platform == "darwin":
            return _resolve(_run(["osascript", "-e", 'tell application "System Events" to get picture of current desktop']), night)
        if _is_kde():
            found = _kde_wallpaper(night)
            if found:
                return found
        key = "picture-uri-dark" if night else "picture-uri"
        return _resolve(_to_path(_run(["gsettings", "get", "org.gnome.desktop.background", key])), night)
    except Exception:
        return None


def signature(path):
    try:
        st = os.stat(path)
        return f"{path}|{int(st.st_mtime)}|{st.st_size}"
    except (OSError, TypeError):
        return ""


# ---------- Bild aufbereiten ----------

def _video_frame(path, dest):
    """Standbild aus einem Video-Wallpaper (braucht ffmpeg). Live-Wallpaper werden bewusst
    nicht abgespielt: kostet dauerhaft CPU/GPU und lenkt ab."""
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        return False
    _run([ffmpeg, "-y", "-loglevel", "error", "-ss", "1", "-i", path, "-frames:v", "1",
          "-vf", f"scale='min({MAX_WIDTH},iw)':-2", dest], timeout=15)
    return os.path.isfile(dest) and os.path.getsize(dest) > 0


def prepare_image(src, folder, basename):
    """Kopie als JPEG (höchstens MAX_WIDTH breit) in folder ablegen. GIFs werden so zum
    Standbild, Videos zu einem Einzelbild. Gibt den Dateinamen oder None zurück."""
    os.makedirs(folder, exist_ok=True)
    for old in glob.glob(os.path.join(folder, basename + ".*")):
        os.remove(old)
    dest = os.path.join(folder, basename + ".jpg")
    if src.lower().endswith(VIDEO_EXTS):
        return os.path.basename(dest) if _video_frame(src, dest) else None
    img = QImage(src)
    if img.isNull():
        return None
    if img.width() > MAX_WIDTH:
        img = img.scaledToWidth(MAX_WIDTH, Qt.TransformationMode.SmoothTransformation)
    if img.hasAlphaChannel():
        img = img.convertToFormat(QImage.Format.Format_RGB32)
    return os.path.basename(dest) if img.save(dest, "JPG", 90) else None


def dominant_color(path):
    """Kräftigste Farbe des Bildes: Farbtöne nach Sättigung x Helligkeit gewichtet, der stärkste
    Farbton gewinnt. Ergebnis wird auf eine gut lesbare Akzent-Helligkeit gebracht."""
    img = QImage(path)
    if img.isNull():
        return None
    img = img.scaled(64, 64, Qt.AspectRatioMode.IgnoreAspectRatio, Qt.TransformationMode.FastTransformation)
    bins = [[0.0, 0.0, 0.0, 0.0] for _ in range(24)]  # Gewicht, r, g, b
    for y in range(img.height()):
        for x in range(img.width()):
            c = img.pixelColor(x, y)
            r, g, b = c.redF(), c.greenF(), c.blueF()
            h, s, v = colorsys.rgb_to_hsv(r, g, b)
            if s < .25 or v < .18:
                continue
            w = s * s * v
            bucket = bins[int(h * 24) % 24]
            bucket[0] += w
            bucket[1] += r * w
            bucket[2] += g * w
            bucket[3] += b * w
    best = max(bins, key=lambda b: b[0])
    if best[0] < 1.0:  # praktisch farbloses Bild
        return None
    r, g, b = (best[i] / best[0] for i in (1, 2, 3))
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    r, g, b = colorsys.hls_to_rgb(h, min(max(l, .48), .62), max(s, .55))
    return QColor.fromRgbF(r, g, b).name()


# ---------- Abgleich beim Start ----------

def sync(cfg, folder, night=False):
    """Bringt Akzentfarbe und Desktop-Hintergrund auf den aktuellen Stand. Gibt die geänderten
    Konfigurationswerte zurück (leer = nichts zu tun). Das Wallpaper wird nur neu verarbeitet,
    wenn sich Pfad, Größe oder Änderungszeit geändert haben."""
    changes = {}
    source = cfg.get("accent_source", "manual")
    if source == "system":
        accent = system_accent()
        if accent and accent != cfg["accent"]:
            changes["accent"] = accent
    needs_wall = source == "wallpaper" or cfg.get("background") == "desktop"
    if not needs_wall:
        return changes
    path = wallpaper_path(night)
    sig = signature(path)
    if not sig or sig == cfg.get("desktop_sig"):
        return changes
    name = prepare_image(path, folder, "desktop")
    if not name:
        return changes
    changes["desktop_sig"] = sig
    changes["desktop_image"] = name
    if source == "wallpaper":
        accent = dominant_color(os.path.join(folder, name))
        if accent:
            changes["accent"] = accent
    return changes


def cache_key(sig):
    return hashlib.md5(sig.encode()).hexdigest()[:8] if sig else "0"
