# Eigene Designs des Nutzers: gespeicherte Looks samt Bildern, getrennt von den
# eingebauten Theme-Paketen. Liegen in user_files/designs/<id>/ und bleiben bei Updates erhalten.
# Austausch als .deckorator-Datei (ZIP mit design.json und Bildern).
import json
import os
import re
import shutil
import time
import zipfile

from . import desktop, theme

DESIGN_DIR = os.path.join(os.path.dirname(__file__), "user_files", "designs")
USER_DIR = os.path.join(os.path.dirname(__file__), "user_files")

# Einstellungen, die zu einem Look gehören (nicht: Bereiche, Leistung, Schrift, eigenes CSS …)
LOOK_KEYS = ("accent", "bg_light", "bg_dark", "background", "bg_intensity", "art", "glass", "blur",
             "glass_opacity", "radius", "button_shape", "shadow", "toolbar_style", "window_style",
             "banner", "banner_height", "banner_area", "review_background", "heatmap_style")
IMAGE_SLOTS = {"bg_image": "wallpaper", "bg_image_dark": "wallpaper_dark", "banner_image": "banner"}
MAX_FILE = 15 * 1024 * 1024  # Schutz beim Import: keine riesigen Dateien


def _slug(name):
    s = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")[:40] or "design"
    return f"{s}-{int(time.time())}"


def list_designs():
    """[(id, design-dict, Ordner)] neueste zuerst."""
    out = []
    if not os.path.isdir(DESIGN_DIR):
        return out
    for did in os.listdir(DESIGN_DIR):
        folder = os.path.join(DESIGN_DIR, did)
        try:
            with open(os.path.join(folder, "design.json"), encoding="utf-8") as f:
                data = json.load(f)
            out.append((did, data, folder))
        except (OSError, ValueError):
            continue
    return sorted(out, key=lambda x: x[1].get("created", 0), reverse=True)


def _thumb(src, folder):
    from aqt.qt import QImage, Qt
    img = QImage(src)
    if not img.isNull():
        img.scaled(320, 180, Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                   Qt.TransformationMode.SmoothTransformation).copy(0, 0, 320, 180).save(
            os.path.join(folder, "thumb.jpg"), "JPG", 82)


def save_design(name, cfg):
    """Aktuellen Look mit seinen Bildern als eigenes Design ablegen."""
    did = _slug(name)
    folder = os.path.join(DESIGN_DIR, did)
    os.makedirs(folder, exist_ok=True)
    data = {"name": name, "created": int(time.time()), "settings": {k: cfg[k] for k in LOOK_KEYS if k in cfg},
            "images": {}}
    for key, slot in IMAGE_SLOTS.items():
        src = cfg.get(key) and os.path.join(USER_DIR, cfg[key])
        if src and os.path.isfile(src):
            dest = f"{slot}.jpg"
            shutil.copyfile(src, os.path.join(folder, dest))
            data["images"][key] = dest
    first = data["images"].get("bg_image") or data["images"].get("banner_image")
    if first:
        _thumb(os.path.join(folder, first), folder)
    with open(os.path.join(folder, "design.json"), "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    return did


def design_from_image(path, name, cfg):
    """Wallpaper hochladen -> kompletter Look: Akzent aus der kräftigsten Farbe, Hintergrund-
    farben leicht in der Grundstimmung des Bildes getönt, Bild als Hintergrund."""
    name_img = desktop.prepare_image(path, USER_DIR, "background")
    if not name_img:
        return None
    img_path = os.path.join(USER_DIR, name_img)
    accent = desktop.dominant_color(img_path) or cfg["accent"]
    mood = desktop.average_color(img_path) or accent
    look = dict(cfg)
    look.update(accent=accent, bg_image=name_img, background="image", bg_intensity=60,
                bg_dark=theme._mix("#121214", mood, .10), bg_light=theme._mix("#f7f7f8", mood, .06),
                bg_image_dark="", accent_source="manual", preset="", pack="")
    did = save_design(name, look)
    look["design"] = did
    return look


def apply_design(did, cfg):
    """Design auf die Konfiguration anwenden; Bilder werden nach user_files kopiert."""
    folder = os.path.join(DESIGN_DIR, did)
    with open(os.path.join(folder, "design.json"), encoding="utf-8") as f:
        data = json.load(f)
    look = dict(cfg)
    look.update({k: v for k, v in data.get("settings", {}).items() if k in LOOK_KEYS})
    for key in IMAGE_SLOTS:
        look[key] = ""
    for key, fname in data.get("images", {}).items():
        if key in IMAGE_SLOTS and os.path.isfile(os.path.join(folder, fname)):
            look[key] = desktop.prepare_image(os.path.join(folder, fname), USER_DIR, IMAGE_SLOTS[key].replace("wallpaper", "background")) or ""
    from . import windows
    if "window_style" in data.get("settings", {}):
        look["window_styles"] = {k: data["settings"]["window_style"] for k in windows.WINDOW_KINDS}
    look.update(design=did, pack="", preset="", accent_source="manual")
    return look


def delete_design(did):
    folder = os.path.join(DESIGN_DIR, did)
    if os.path.dirname(os.path.abspath(folder)) == os.path.abspath(DESIGN_DIR):
        shutil.rmtree(folder, ignore_errors=True)


def export_design(did, path):
    folder = os.path.join(DESIGN_DIR, did)
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        for fname in os.listdir(folder):
            z.write(os.path.join(folder, fname), fname)


def import_design(path):
    """Nur design.json und JPG/PNG-Bilder flach übernehmen; keine Pfade, keine fremden Dateien."""
    with zipfile.ZipFile(path) as z:
        names = [n for n in z.namelist() if "/" not in n and "\\" not in n and not n.startswith(".")]
        if "design.json" not in names:
            raise ValueError("design.json fehlt")
        data = json.loads(z.read("design.json").decode("utf-8"))
        if not isinstance(data, dict) or not isinstance(data.get("settings"), dict):
            raise ValueError("ungültiges Design")
        did = _slug(str(data.get("name", "Import")))
        folder = os.path.join(DESIGN_DIR, did)
        os.makedirs(folder, exist_ok=True)
        allowed = {v for v in data.get("images", {}).values()} | {"thumb.jpg"}
        for n in names:
            info = z.getinfo(n)
            if n in allowed and n.lower().endswith((".jpg", ".jpeg", ".png")) and info.file_size <= MAX_FILE:
                with open(os.path.join(folder, n), "wb") as f:
                    f.write(z.read(n))
        data["settings"] = {k: v for k, v in data["settings"].items() if k in LOOK_KEYS}
        data["images"] = {k: v for k, v in data.get("images", {}).items()
                          if k in IMAGE_SLOTS and os.path.isfile(os.path.join(folder, v))}
        data["created"] = int(time.time())
        with open(os.path.join(folder, "design.json"), "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    return did
