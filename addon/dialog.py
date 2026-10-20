# Einstellungsfenster mit Live-Vorschau. Änderungen werden erst mit
# "Übernehmen"/"Speichern" gespeichert und auf Ankis Hauptfenster angewendet.
import json
import os
import shutil

from anki.lang import current_lang
from aqt import mw
from aqt.qt import *
from aqt.theme import theme_manager
from aqt.utils import getFile, getSaveFile, showWarning, tooltip

from . import desktop, theme, ui
from .preview import ThemePreview
from .ui import ColorButton, Section, Toggle

ADDON_DIR = os.path.dirname(__file__)
USER_DIR = os.path.join(ADDON_DIR, "user_files")

STRINGS = {
    "title": ("Deckorator – Theme-Einstellungen", "Deckorator – Theme settings"),
    "page_look": ("Aussehen", "Appearance"), "page_shape": ("Form", "Shape"),
    "page_text": ("Schrift", "Text"), "page_study": ("Lernen", "Studying"),
    "page_addons": ("Add-ons", "Add-ons"), "page_advanced": ("Erweitert", "Advanced"),
    "presets": ("Vorlagen", "Presets"), "colors": ("Farben", "Colors"), "background": ("Hintergrund", "Background"),
    "accent": ("Akzentfarbe", "Accent color"),
    "bg_light": ("Hell", "Light"), "bg_dark": ("Dunkel", "Dark"),
    "bg_style": ("Stil", "Style"), "bg_intensity": ("Intensität", "Intensity"),
    "bg_image": ("Bild", "Image"), "choose": ("Auswählen…", "Choose…"),
    "remove": ("Entfernen", "Remove"), "none": ("Keins", "None"),
    "style_solid": ("Einfarbig", "Solid"), "style_spotlight": ("Spotlight: Licht von oben", "Spotlight: light from above"),
    "style_dots": ("Punktraster", "Dot grid"), "style_grid": ("Linienraster", "Line grid"),
    "style_grain": ("Körnung", "Grain"), "style_waves": ("Wellen", "Waves"), "style_image": ("Eigenes Bild", "Custom image"),
    "style_desktop": ("Desktop-Hintergrund (folgt deinem Wallpaper)", "Desktop wallpaper (follows yours)"),
    "desktop_hint": ("Aktuell: {name}. Wird bei jedem Start von Anki neu abgeglichen. Live- und Video-Wallpaper "
                     "erscheinen als Standbild.",
                     "Currently: {name}. Re-synced every time Anki starts. Live and video wallpapers "
                     "show up as a still image."),
    "performance": ("Leistung", "Performance"), "perf_mode": ("Effekte", "Effects"),
    "perf_auto": ("Automatisch an die Hardware anpassen", "Adapt to the hardware automatically"),
    "perf_full": ("Alle Effekte", "All effects"),
    "perf_light": ("Sparsam: ohne Unschärfe, leichte Schatten", "Light: no blur, softer shadows"),
    "hw_detected": ("Erkannt: {facts}. {verdict}", "Detected: {facts}. {verdict}"),
    "hw_threads": ("{n} CPU-Threads", "{n} CPU threads"), "hw_ram": ("{n} GB RAM", "{n} GB RAM"),
    "hw_battery": ("läuft auf Akku", "running on battery"), "hw_software": ("Software-Rendering", "software rendering"),
    "hw_weak": ("Automatisch wird der sparsame Modus genutzt.", "Automatic mode uses the light setting."),
    "hw_strong": ("Automatisch bleiben alle Effekte an.", "Automatic mode keeps all effects on."),
    "no_wallpaper": ("Der Desktop-Hintergrund wurde nicht gefunden.", "Couldn't find the desktop wallpaper."),
    "accent_source": ("Quelle", "Source"),
    "src_manual": ("Selbst wählen", "Pick myself"), "src_system": ("Akzentfarbe des Systems", "System accent color"),
    "src_wallpaper": ("Aus dem Desktop-Hintergrund", "From the desktop wallpaper"),
    "src_hint": ("Wird bei jedem Start von Anki neu gelesen. Ändert sich dein Hintergrund, zieht die Farbe mit.",
                 "Re-read every time Anki starts. If your wallpaper changes, the color follows."),
    "src_found": ("Erkannt: {color} ({where})", "Detected: {color} ({where})"),
    "src_failed": ("Nichts gefunden, die bisherige Farbe bleibt.", "Nothing found, keeping the current color."),
    "src_system_where": ("System", "system"),
    "redetect": ("Erneut erkennen", "Detect again"),
    "glass_title": ("Glas", "Glass"),
    "glass_hint": ("Die Unschärfe sieht man nur, wenn hinter den Flächen ein Muster oder Bild liegt, "
                   "z.B. bei Punktraster, Wellen oder Desktop-Hintergrund.",
                   "Blur is only visible when a pattern or image sits behind the panels, "
                   "e.g. with dot grid, waves or desktop wallpaper."),
    "glass": ("Durchscheinende Flächen mit Unschärfe", "Translucent panels with blur"),
    "blur": ("Unschärfe", "Blur"), "opacity": ("Deckkraft", "Opacity"),
    "shapes": ("Formen", "Shapes"),
    "radius": ("Eckenradius", "Corner radius"), "buttons": ("Buttons", "Buttons"),
    "btn_pill": ("Pille", "Pill"), "btn_rounded": ("Abgerundet", "Rounded"), "btn_square": ("Eckig", "Square"),
    "shadow": ("Schatten", "Shadows"), "shadow_levels": (("Aus", "Leicht", "Mittel", "Stark"), ("Off", "Light", "Medium", "Strong")),
    "bars": ("Leisten", "Bars"),
    "toolbar": ("Obere Leiste", "Top bar"), "tb_floating": ("Schwebende Kapsel", "Floating capsule"),
    "tb_flat": ("Flach", "Flat"), "compact": ("Kompakte Abstände", "Compact spacing"),
    "font": ("Schriftart", "Font"), "font_default": ("Anki-Standardschrift verwenden", "Use Anki's default font"),
    "font_scale": ("Größe", "Size"),
    "font_hint": ("Gilt für Deckliste, Übersicht und Leisten. Karten behalten die Schrift ihres Notiztyps.",
                  "Applies to the deck list, overview and bars. Cards keep their note type's font."),
    "display": ("Anzeige", "Display"),
    "badges": ("Zähler als farbige Badges", "Counts as colored badges"),
    "highlight_today": ("„Heute gelernt“ auf der Startseite hervorheben", "Highlight “studied today” on the home screen"),
    "help": ("Hilfe & Feedback", "Help & feedback"),
    "help_hint": ("Kopiert einen Bericht über Anki-Version, System, erkannte Hardware und die letzten Fehler. "
                  "Nichts wird automatisch gesendet; du entscheidest, wo du ihn einfügst.",
                  "Copies a report with Anki version, system, detected hardware and recent errors. "
                  "Nothing is sent automatically; you decide where to paste it."),
    "copy_diag": ("Diagnosebericht kopieren", "Copy diagnostic report"),
    "diag_copied": ("Bericht in die Zwischenablage kopiert", "Report copied to the clipboard"),
    "answers": ("Antwort-Buttons nach Bewertung einfärben", "Tint answer buttons by rating"),
    "animations": ("Animationen", "Animations"),
    "motion": ("Bewegung", "Motion"),
    "motion_hint": ("Wenn in Anki „Bewegung reduzieren“ an ist, bleiben Animationen ohnehin aus.",
                    "If Anki's “Reduce motion” is on, animations stay off anyway."),
    "areas": ("Anwenden auf", "Apply to"),
    "area_main": ("Deckliste, Übersicht und Leisten", "Deck list, overview and bars"),
    "area_review_bar": ("Untere Leiste beim Lernen", "Bottom bar while studying"),
    "area_other": ("Farben auch in anderen Fenstern (Editor, Kartenvorschau)", "Colors in other windows too (editor, card preview)"),
    "review_bg": ("Hintergrund beim Lernen", "Background while studying"),
    "rb_calm": ("Ruhig: Theme-Farbe, keine Effekte", "Calm: theme color, no effects"),
    "rb_full": ("Wie auf der Startseite", "Same as the home screen"),
    "rb_note": ("Vom Notiztyp (Theme hält sich raus)", "From the note type (theme stays out)"),
    "rb_hint": ("Beim Lernen steht die Karte im Mittelpunkt. „Ruhig“ übernimmt die Farbe deines Themes, "
                "verzichtet aber auf Farbflecken und Bild, damit nichts ablenkt.",
                "While studying, the card comes first. “Calm” keeps your theme's color but drops "
                "blobs and images so nothing distracts you."),
    "heatmap": ("Review Heatmap", "Review Heatmap"),
    "hm_theme": ("Komplett anpassen: Karte, runde Zellen, Akzentfarbe", "Fully restyle: card, rounded cells, accent color"),
    "hm_colors": ("Nur Farben anpassen, Form bleibt original", "Colors only, keep the original shape"),
    "hm_original": ("Nicht verändern (Original)", "Leave untouched (original)"),
    "hm_hint": ("Du entscheidest, ob Deckorator die Heatmap umgestaltet. „Nicht verändern“ lässt sie exakt so, "
                "wie das Heatmap-Add-on sie zeichnet.",
                "You decide whether Deckorator restyles the heatmap. “Leave untouched” keeps it exactly "
                "as the heatmap add-on draws it."),
    "hm_missing": ("Review Heatmap ist nicht installiert oder deaktiviert. Die Einstellung greift, sobald es aktiv ist.",
                   "Review Heatmap is not installed or disabled. The setting applies once it's active."),
    "hm_style": ("Darstellung", "Style"),
    "custom_css": ("Eigenes CSS", "Custom CSS"),
    "custom_css_hint": ("Wird zuletzt angehängt und überschreibt damit alles andere.",
                        "Appended last, so it overrides everything else."),
    "share": ("Teilen", "Share"),
    "share_hint": ("Speichert alle Einstellungen außer dem Hintergrundbild als JSON-Datei.",
                   "Saves all settings except the background image as a JSON file."),
    "export": ("Exportieren…", "Export…"), "import": ("Importieren…", "Import…"),
    "reset": ("Auf Standard zurücksetzen", "Reset to defaults"),
    "cancel": ("Abbrechen", "Cancel"), "apply": ("Übernehmen", "Apply"), "save": ("Speichern", "Save"),
    "light": ("Hell", "Light"), "dark": ("Dunkel", "Dark"),
    "view_home": ("Startseite", "Home"), "view_study": ("Lernen", "Study"),
    "other_card": ("Andere Karte", "Another card"), "image_card": ("Karte mit Bild", "Card with image"),
    "answer_side": ("Antwort zeigen", "Show answer"),
    "no_image": ("In deiner Sammlung gibt es keine Karte mit Bild.", "Your collection has no card with an image."),
    "no_cards": ("Beispielkarte, deine Sammlung ist noch leer", "Sample card, your collection is empty"),
    "no_decks": ("Öffne einmal die Stapelübersicht, dann erscheinen hier deine Stapel.",
                 "Open the deck list once and your decks will show up here."),
    "demo_q": ("Wie heißt die Hauptstadt von Österreich?", "What is the capital of Austria?"),
    "demo_a": ("Wien", "Vienna"),
    "saved": ("Theme gespeichert", "Theme saved"), "import_err": ("Datei konnte nicht gelesen werden:", "Could not read file:"),
    "preset_names": ({"rose": "Rosé", "ocean": "Ozean", "forest": "Wald", "lavender": "Lavendel", "amber": "Bernstein",
                      "coral": "Koralle", "teal": "Petrol", "graphite": "Graphit"},
                     {"rose": "Rosé", "ocean": "Ocean", "forest": "Forest", "lavender": "Lavender", "amber": "Amber",
                      "coral": "Coral", "teal": "Teal", "graphite": "Graphite"}),
}

PAGES = ("look", "shape", "text", "study", "addons", "advanced")
# Werte, die an diesen Rechner gebunden sind und beim Teilen nicht mitwandern
PRIVATE_KEYS = ("bg_image", "desktop_image", "desktop_sig")


def t(key):
    de, en = STRINGS[key]
    return de if current_lang.startswith("de") else en


HEATMAP_ID = "1771074083"  # Review Heatmap auf AnkiWeb


def diagnostics(api, cfg):
    """Text für Fehlerberichte. Keine Pfade außer Dateinamen, keine Karteninhalte."""
    import platform

    from anki.buildinfo import version as anki_version
    from aqt.qt import QT_VERSION_STR
    from . import log

    try:
        from PyQt6.QtWebEngineCore import qWebEngineChromiumVersion
        chromium = qWebEngineChromiumVersion()
    except Exception:
        chromium = "?"
    hw = api.hardware()
    wall = desktop.wallpaper_path(theme_manager.night_mode)
    lines = [
        f"Deckorator {api.VERSION} | Anki {anki_version} | Qt {QT_VERSION_STR} | Chromium {chromium}",
        f"OS: {platform.platform()} | Desktop: {os.environ.get('XDG_CURRENT_DESKTOP', '-')} "
        f"| Session: {os.environ.get('XDG_SESSION_TYPE', '-')} | Night mode: {theme_manager.night_mode}",
        f"Hardware: {hw['threads']} threads, {hw['ram'] and round(hw['ram'])} GB RAM, battery={hw['battery']}, "
        f"software={hw['software']} -> weak={hw['weak']} | performance={cfg['performance']} "
        f"-> light={api.effective(cfg)['_light']}",
        f"Desktop: system accent={desktop.system_accent()} | wallpaper={os.path.basename(wall) if wall else None} "
        f"| ffmpeg={'yes' if shutil.which('ffmpeg') else 'no'} | heatmap={heatmap_active()}",
        "Config: " + json.dumps({k: v for k, v in cfg.items() if k not in PRIVATE_KEYS + ("custom_css",)},
                                ensure_ascii=False),
        f"Custom CSS: {len(cfg['custom_css'])} chars",
        "Errors:" + ("".join("\n  " + e for e in log.ENTRIES) or " none"),
    ]
    return "\n".join(lines)


def heatmap_active():
    am = mw.addonManager
    return any((d == HEATMAP_ID or "heatmap" in (am.addonName(d) or "").lower()) and am.isEnabled(d)
               for d in am.allAddons())


class ThemeDialog(QDialog):
    def __init__(self, api):
        super().__init__(mw)
        self.setObjectName("ctDialog")
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self.api = api
        self.defaults = api.defaults()
        self.cfg = api.load_config()
        self._loading = False
        self._styled_accent = None
        self.setWindowTitle(t("title"))
        self.resize(1240, 780)

        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.setInterval(120)
        self._timer.timeout.connect(self._render_preview)

        self._build()
        self._load_into_widgets()
        self._restyle()
        self._render_preview()

    # ---------- Aufbau ----------

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 12)
        root.setSpacing(12)
        split = QSplitter(Qt.Orientation.Horizontal)
        split.setChildrenCollapsible(False)
        root.addWidget(split, 1)

        # links: Navigation + Seiten
        left = QWidget()
        lh = QHBoxLayout(left)
        lh.setContentsMargins(0, 0, 0, 0)
        lh.setSpacing(12)
        self.nav = QListWidget()
        self.nav.setObjectName("ctNav")
        self.nav.setFixedWidth(150)
        self.nav.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.pages = QStackedWidget()
        builders = {"look": self._page_look, "shape": self._page_shape, "text": self._page_text,
                    "study": self._page_study, "addons": self._page_addons, "advanced": self._page_advanced}
        for key in PAGES:
            self.nav.addItem(t("page_" + key))
            self.pages.addWidget(self._page(t("page_" + key), builders[key]()))
        self.nav.currentRowChanged.connect(self.pages.setCurrentIndex)
        self.nav.setCurrentRow(0)
        lh.addWidget(self.nav)
        lh.addWidget(self.pages, 1)
        left.setMinimumWidth(560)
        split.addWidget(left)

        # rechts: Vorschau in einer Karte
        frame = QFrame()
        frame.setObjectName("ctPreviewFrame")
        fl = QVBoxLayout(frame)
        fl.setContentsMargins(12, 12, 12, 12)
        self.preview = ThemePreview(t, self.api)
        fl.addWidget(self.preview)
        split.addWidget(frame)
        split.setSizes([660, 600])

        # unten: Aktionen
        bar = QHBoxLayout()
        b_reset = QPushButton(t("reset"))
        b_reset.setObjectName("ctGhost")
        b_reset.clicked.connect(self._reset)
        bar.addWidget(b_reset)
        bar.addStretch()
        b_cancel = QPushButton(t("cancel"))
        b_cancel.clicked.connect(self.reject)
        b_apply = QPushButton(t("apply"))
        b_apply.clicked.connect(self._apply)
        b_save = QPushButton(t("save"))
        b_save.setObjectName("ctPrimary")
        b_save.setDefault(True)
        b_save.clicked.connect(self._ok)
        for b in (b_cancel, b_apply, b_save):
            bar.addWidget(b)
        root.addLayout(bar)

    def _page(self, title, sections):
        page = QWidget()
        page.setObjectName("ctPage")
        v = QVBoxLayout(page)
        v.setContentsMargins(0, 0, 6, 0)
        v.setSpacing(12)
        lbl = QLabel(title)
        lbl.setObjectName("ctPageTitle")
        v.addWidget(lbl)
        for s in sections:
            v.addWidget(s)
        v.addStretch()
        sa = QScrollArea()
        sa.setWidgetResizable(True)
        sa.setFrameShape(QFrame.Shape.NoFrame)
        sa.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        sa.setWidget(page)
        return sa

    def _slider(self, lo, hi, suffix=""):
        box = QWidget()
        lay = QHBoxLayout(box)
        lay.setContentsMargins(0, 0, 0, 0)
        s = QSlider(Qt.Orientation.Horizontal)
        s.setRange(lo, hi)
        val = QLabel()
        val.setObjectName("ctHint")
        val.setMinimumWidth(46)
        val.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        s.valueChanged.connect(lambda v: val.setText(f"{v}{suffix}"))
        s.valueChanged.connect(self._changed)
        lay.addWidget(s, 1)
        lay.addWidget(val)
        box.slider = s
        return box

    def _combo(self, items):
        c = QComboBox()
        # nicht auf den längsten Eintrag aufblähen, sonst wird die Spalte breiter als sichtbar
        c.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
        c.setMinimumContentsLength(8)
        c.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        ui.modern_popup(c)
        for key, label in items:
            c.addItem(label, key)
        c.currentIndexChanged.connect(self._changed)
        return c

    def _toggle(self, text):
        c = Toggle(text)
        c.toggled.connect(self._changed)
        return c

    def _page_look(self):
        presets = Section(t("presets"))
        grid = QGridLayout()
        grid.setSpacing(10)
        names = t("preset_names")
        self.preset_buttons = {}
        for i, (key, p) in enumerate(theme.PRESETS.items()):
            b = QPushButton(names[key])
            b.setCheckable(True)
            b.setMinimumSize(60, 52)
            b.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Fixed)
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            a = p["accent"]
            b.setStyleSheet(
                "QPushButton { color: white; font-weight: 600; border-radius: 12px; border: 2px solid transparent; padding: 0 4px;"
                f" background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {theme._mix(a, '#ffffff', .12)},"
                f" stop:1 {theme._mix(a, '#000000', .28)}); }}"
                "QPushButton:hover { border: 2px solid rgba(255,255,255,.55); }"
                "QPushButton:checked { border: 3px solid palette(window-text); }")
            b.clicked.connect(lambda _=False, k=key: self._apply_preset(k))
            grid.addWidget(b, i // 4, i % 4)
            self.preset_buttons[key] = b
        presets.form.addRow(grid)

        colors = Section(t("colors"))
        src = QHBoxLayout()
        self.accent_source = self._combo([("manual", t("src_manual")), ("system", t("src_system")),
                                          ("wallpaper", t("src_wallpaper"))])
        self.accent_source.currentIndexChanged.connect(lambda _: None if self._loading else self._detect_accent())
        self.b_redetect = QPushButton(t("redetect"))
        self.b_redetect.clicked.connect(self._detect_accent)
        src.addWidget(self.accent_source, 1)
        src.addWidget(self.b_redetect)
        colors.form.addRow(t("accent_source"), src)
        self.accent_info = QLabel()
        self.accent_info.setObjectName("ctHint")
        self.accent_info.setWordWrap(True)
        colors.row(self.accent_info)
        self.accent = ColorButton("#000000")
        self.bg_light = ColorButton("#ffffff")
        self.bg_dark = ColorButton("#000000")
        for cb in (self.accent, self.bg_light, self.bg_dark):
            cb.changed.connect(self._custom_changed)
        # die Hintergrundfarben wirken nur im jeweiligen Modus, also die Vorschau dorthin schalten
        self.bg_light.changed.connect(lambda: self.preview.set_night(False))
        self.bg_dark.changed.connect(lambda: self.preview.set_night(True))
        colors.row(t("accent"), self.accent)
        colors.row(t("bg_light"), self.bg_light)
        colors.row(t("bg_dark"), self.bg_dark)

        bg = Section(t("background"))
        self.bg_style = self._combo([(s, t("style_" + s)) for s in theme.BACKGROUND_STYLES])
        self.bg_style.currentIndexChanged.connect(self._style_changed)
        bg.row(t("bg_style"), self.bg_style)
        self.desktop_info = QLabel()
        self.desktop_info.setObjectName("ctHint")
        self.desktop_info.setWordWrap(True)
        bg.row(self.desktop_info)
        self.bg_intensity = bg.row(t("bg_intensity"), self._slider(0, 100, " %"))
        img = QHBoxLayout()
        img.setContentsMargins(0, 0, 0, 0)
        self.bg_image_label = QLabel()
        self.bg_image_label.setObjectName("ctHint")
        self.bg_image_label.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        b_choose = QPushButton(t("choose"))
        b_choose.clicked.connect(self._choose_image)
        self.b_remove = QPushButton(t("remove"))
        self.b_remove.clicked.connect(self._remove_image)
        img.addWidget(self.bg_image_label, 1)
        img.addWidget(b_choose)
        img.addWidget(self.b_remove)
        self.img_row = QWidget()
        self.img_row.setLayout(img)
        bg.row(t("bg_image"), self.img_row)
        return [presets, colors, bg]

    def _page_shape(self):
        glass = Section(t("glass_title"), t("glass_hint"))
        self.glass = self._toggle(t("glass"))
        self.glass.toggled.connect(self._update_enabled)
        glass.row(self.glass)
        self.blur = glass.row(t("blur"), self._slider(0, 40, " px"))
        self.opacity = glass.row(t("opacity"), self._slider(10, 100, " %"))

        shapes = Section(t("shapes"))
        self.radius = shapes.row(t("radius"), self._slider(0, 32, " px"))
        self.button_shape = shapes.row(t("buttons"), self._combo(
            [("pill", t("btn_pill")), ("rounded", t("btn_rounded")), ("square", t("btn_square"))]))
        self.shadow = shapes.row(t("shadow"), self._combo(list(enumerate(t("shadow_levels")))))

        bars = Section(t("bars"))
        self.toolbar_style = bars.row(t("toolbar"), self._combo([("floating", t("tb_floating")), ("flat", t("tb_flat"))]))
        self.compact = self._toggle(t("compact"))
        bars.row(self.compact)

        perf = Section(t("performance"))
        self.performance = perf.row(t("perf_mode"), self._combo(
            [("auto", t("perf_auto")), ("full", t("perf_full")), ("light", t("perf_light"))]))
        self.performance.currentIndexChanged.connect(self._update_enabled)
        self.perf_info = QLabel(self._hardware_text())
        self.perf_info.setObjectName("ctHint")
        self.perf_info.setWordWrap(True)
        perf.row(self.perf_info)
        return [perf, glass, shapes, bars]

    def _hardware_text(self):
        hw = self.api.hardware()
        facts = []
        if hw["software"]:
            facts.append(t("hw_software"))
        if hw["threads"]:
            facts.append(t("hw_threads").format(n=hw["threads"]))
        if hw["ram"]:
            facts.append(t("hw_ram").format(n=round(hw["ram"])))
        if hw["battery"]:
            facts.append(t("hw_battery"))
        verdict = t("hw_weak") if hw["weak"] else t("hw_strong")
        return t("hw_detected").format(facts=", ".join(facts), verdict=verdict)

    def _page_text(self):
        sec = Section(t("font"), t("font_hint"))
        self.font_default = self._toggle(t("font_default"))
        self.font_default.toggled.connect(self._update_enabled)
        sec.row(self.font_default)
        self.font_family = QFontComboBox()
        self.font_family.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
        self.font_family.setMinimumContentsLength(8)
        ui.modern_popup(self.font_family, own_delegate=False)
        self.font_family.currentFontChanged.connect(self._changed)
        sec.row(t("font"), self.font_family)
        self.font_scale = sec.row(t("font_scale"), self._slider(80, 140, " %"))
        return [sec]

    def _page_study(self):
        bg = Section(t("review_bg"), t("rb_hint"))
        self.review_background = self._combo(
            [("calm", t("rb_calm")), ("full", t("rb_full")), ("note", t("rb_note"))])
        self.review_background.currentIndexChanged.connect(
            lambda _: None if self._loading else self.preview.set_view("study"))
        bg.row(self.review_background)
        display = Section(t("display"))
        self.colored_answers = self._toggle(t("answers"))
        self.count_badges = self._toggle(t("badges"))
        self.highlight_today = self._toggle(t("highlight_today"))
        self.highlight_today.toggled.connect(lambda _: None if self._loading else self.preview.set_view("home"))
        display.row(self.highlight_today)
        display.row(self.colored_answers)
        display.row(self.count_badges)
        return [bg, display]

    def _page_addons(self):
        hint = t("hm_hint") if heatmap_active() else t("hm_missing")
        sec = Section(t("heatmap"), hint)
        self.heatmap_style = sec.row(t("hm_style"), self._combo(
            [("theme", t("hm_theme")), ("colors", t("hm_colors")), ("original", t("hm_original"))]))
        self.heatmap_style.currentIndexChanged.connect(
            lambda _: None if self._loading else self.preview.set_view("home"))
        return [sec]

    def _page_advanced(self):
        areas = Section(t("areas"))
        self.area_checks = {}
        for key in ("main", "review_bar", "other"):
            c = self._toggle(t("area_" + key))
            areas.row(c)
            self.area_checks[key] = c
        motion = Section(t("motion"), t("motion_hint"))
        self.animations = self._toggle(t("animations"))
        motion.row(self.animations)
        css = Section(t("custom_css"), t("custom_css_hint"))
        self.custom_css = QPlainTextEdit()
        self.custom_css.setFont(QFontDatabase.systemFont(QFontDatabase.SystemFont.FixedFont))
        self.custom_css.setPlaceholderText("html body .hitem { letter-spacing: .02em; }")
        self.custom_css.setMinimumHeight(140)
        self.custom_css.textChanged.connect(self._changed)
        css.row(self.custom_css)
        share = Section(t("share"), t("share_hint"))
        h = QHBoxLayout()
        b_exp = QPushButton(t("export"))
        b_exp.clicked.connect(self._export)
        b_imp = QPushButton(t("import"))
        b_imp.clicked.connect(self._import)
        h.addWidget(b_exp)
        h.addWidget(b_imp)
        h.addStretch()
        share.form.addRow(h)

        help_ = Section(t("help"), t("help_hint"))
        b_diag = QPushButton(t("copy_diag"))
        b_diag.clicked.connect(self._copy_diagnostics)
        hh = QHBoxLayout()
        hh.addWidget(b_diag)
        hh.addStretch()
        help_.form.addRow(hh)
        return [areas, motion, css, share, help_]

    def _copy_diagnostics(self):
        QApplication.clipboard().setText(diagnostics(self.api, self._collect()))
        tooltip(t("diag_copied"), parent=self)

    # ---------- Werte <-> Widgets ----------

    @staticmethod
    def _set_combo(combo, key):
        i = combo.findData(key)
        combo.setCurrentIndex(max(0, i))

    def _load_into_widgets(self):
        c = self.cfg
        self._loading = True
        self._set_combo(self.accent_source, c["accent_source"])
        self.accent.set_color(c["accent"])
        self.bg_light.set_color(c["bg_light"])
        self.bg_dark.set_color(c["bg_dark"])
        self._set_combo(self.bg_style, c["background"])
        self.bg_intensity.slider.setValue(c["bg_intensity"])
        self.glass.setChecked(c["glass"])
        self.blur.slider.setValue(c["blur"])
        self.opacity.slider.setValue(c["glass_opacity"])
        self.radius.slider.setValue(c["radius"])
        self._set_combo(self.button_shape, c["button_shape"])
        self._set_combo(self.shadow, c["shadow"])
        self._set_combo(self.toolbar_style, c["toolbar_style"])
        self._set_combo(self.performance, c["performance"])
        self.compact.setChecked(c["compact"])
        self.font_default.setChecked(not c["font_family"])
        # ohne eigene Schrift die Anki-Schrift vorauswählen, nicht den ersten Eintrag der Liste
        self.font_family.setCurrentFont(QFont(c["font_family"] or mw.web.font().family()))
        self.font_scale.slider.setValue(c["font_scale"])
        self.count_badges.setChecked(c["count_badges"])
        self.colored_answers.setChecked(c["colored_answers"])
        self.animations.setChecked(c["animations"])
        self.highlight_today.setChecked(c["highlight_today"])
        self._set_combo(self.review_background, c["review_background"])
        self._set_combo(self.heatmap_style, c["heatmap_style"])
        for k, cb in self.area_checks.items():
            cb.setChecked(c["areas"].get(k, False))
        self.custom_css.setPlainText(c["custom_css"])
        self._update_image_label()
        self._update_presets()
        self._loading = False
        self._update_enabled()

    def _collect(self):
        c = dict(self.cfg)
        c.update({
            "accent_source": self.accent_source.currentData(),
            "accent": self.accent.color(), "bg_light": self.bg_light.color(), "bg_dark": self.bg_dark.color(),
            "background": self.bg_style.currentData(), "bg_intensity": self.bg_intensity.slider.value(),
            "glass": self.glass.isChecked(), "blur": self.blur.slider.value(),
            "glass_opacity": self.opacity.slider.value(), "radius": self.radius.slider.value(),
            "button_shape": self.button_shape.currentData(), "shadow": self.shadow.currentData(),
            "toolbar_style": self.toolbar_style.currentData(), "compact": self.compact.isChecked(),
            "performance": self.performance.currentData(),
            "font_family": "" if self.font_default.isChecked() else self.font_family.currentFont().family(),
            "font_scale": self.font_scale.slider.value(),
            "count_badges": self.count_badges.isChecked(), "colored_answers": self.colored_answers.isChecked(),
            "animations": self.animations.isChecked(),
            "highlight_today": self.highlight_today.isChecked(),
            "review_background": self.review_background.currentData(),
            "heatmap_style": self.heatmap_style.currentData(),
            "areas": {k: cb.isChecked() for k, cb in self.area_checks.items()},
            "custom_css": self.custom_css.toPlainText(),
        })
        return c

    def _update_enabled(self):
        manual = self.accent_source.currentData() == "manual"
        self.accent.setEnabled(manual)
        self.b_redetect.setVisible(not manual)
        self.accent_info.setVisible(not manual)
        if not manual and not self.accent_info.text():
            self.accent_info.setText(t("src_hint"))
        style = self.bg_style.currentData()
        self.img_row.setEnabled(style == "image")
        self.bg_intensity.setEnabled(style != "solid")
        self.desktop_info.setVisible(style == "desktop")
        if style == "desktop" and not self.desktop_info.text():
            self._update_desktop_info()
        light = self.performance.currentData() == "light" or (
            self.performance.currentData() == "auto" and self.api.hardware()["weak"])
        self.blur.setEnabled(self.glass.isChecked() and not light)
        self.opacity.setEnabled(self.glass.isChecked())
        self.font_family.setEnabled(not self.font_default.isChecked())

    def _update_presets(self):
        for k, b in self.preset_buttons.items():
            b.setChecked(k == self.cfg.get("preset"))

    def _update_image_label(self):
        name = self.cfg.get("bg_image") or ""
        self.bg_image_label.setText(name or t("none"))
        self.b_remove.setEnabled(bool(name))

    def _restyle(self):
        """Stylesheet nur neu setzen, wenn sich die Akzentfarbe geändert hat."""
        accent = self.cfg["accent"]
        if accent == self._styled_accent:
            return
        self._styled_accent = accent
        colors = ui.palette(accent, theme_manager.night_mode)
        ui.COLORS.clear()
        ui.COLORS.update(colors)
        self.setStyleSheet(ui.stylesheet(colors))

    # ---------- Aktionen ----------

    def _changed(self, *_):
        if self._loading:
            return
        self.cfg = self._collect()
        self._restyle()
        self._timer.start()

    def _custom_changed(self):
        self.cfg["preset"] = ""
        self._update_presets()
        self._changed()

    def _apply_preset(self, key):
        self.cfg = self._collect()
        accent = self.cfg["accent"]
        self.cfg.update(theme.PRESETS[key])
        if self.cfg["accent_source"] != "manual":
            # automatische Akzentfarbe hat Vorrang, die Vorlage liefert nur den Rest
            self.cfg["accent"] = accent
        self.cfg["preset"] = key
        self._load_into_widgets()
        self._restyle()
        self._render_preview()

    def _detect_accent(self):
        self.cfg = self._collect()
        source = self.cfg["accent_source"]
        self._update_enabled()
        if source == "manual":
            return
        changes = self.api.sync_desktop(self.cfg, force=True)
        accent = changes.get("accent") or (self.cfg["accent"] if source == "system" and desktop.system_accent() else None)
        if not accent:
            self.accent_info.setText(t("src_failed"))
            return
        where = t("src_system_where") if source == "system" else os.path.basename(
            desktop.wallpaper_path(theme_manager.night_mode) or "")
        self.cfg.update(changes)
        self.cfg["preset"] = ""
        self._load_into_widgets()
        self.accent_info.setText(t("src_found").format(color=accent.upper(), where=where) + "\n" + t("src_hint"))
        self._restyle()
        self._render_preview()

    def _style_changed(self):
        """Beim Wechsel auf "Desktop-Hintergrund" das Wallpaper sofort holen."""
        self._update_enabled()
        if self._loading or self.bg_style.currentData() != "desktop":
            return
        self.cfg = self._collect()
        changes = self.api.sync_desktop(self.cfg, force=True)
        if not changes.get("desktop_image"):
            tooltip(t("no_wallpaper"), parent=self)
            self.desktop_info.setText(t("no_wallpaper"))
            return
        self.cfg.update(changes)
        self._update_desktop_info()
        self._render_preview()

    def _update_desktop_info(self):
        path = desktop.wallpaper_path(theme_manager.night_mode)
        self.desktop_info.setText(t("desktop_hint").format(name=os.path.basename(path)) if path else t("no_wallpaper"))

    def _choose_image(self):
        def chosen(path):
            if not path:
                return
            name = desktop.prepare_image(path, USER_DIR, "background")
            if not name:
                showWarning(f"{t('import_err')}\n{path}", parent=self)
                return
            self.cfg = self._collect()
            self.cfg["bg_image"] = name
            self.cfg["background"] = "image"
            self._load_into_widgets()
            self._render_preview()

        exts = " ".join("*" + e for e in desktop.IMAGE_EXTS)
        getFile(self, t("bg_image"), cb=chosen, filter=exts, key="deckorator_bg")

    def _remove_image(self):
        self.cfg = self._collect()
        self.cfg["bg_image"] = ""
        if self.cfg["background"] == "image":
            self.cfg["background"] = "spotlight"
        self._load_into_widgets()
        self._render_preview()

    def _export(self):
        path = getSaveFile(self, t("export"), "deckorator_export", "Theme", ".json", "deckorator-theme.json")
        if path:
            data = {k: v for k, v in self._collect().items() if k not in PRIVATE_KEYS}
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

    def _import(self):
        def chosen(path):
            if not path:
                return
            try:
                with open(path, encoding="utf-8") as f:
                    data = json.load(f)
                if not isinstance(data, dict):
                    raise ValueError("not a JSON object")
            except Exception as e:
                showWarning(f"{t('import_err')}\n{e}", parent=self)
                return
            merged = dict(self.cfg)
            merged.update({k: v for k, v in data.items() if k in self.defaults and k not in PRIVATE_KEYS})
            self.cfg = merged
            self._load_into_widgets()
            self._restyle()
            self._render_preview()

        getFile(self, t("import"), cb=chosen, filter="*.json", key="deckorator_export")

    def _reset(self):
        self.cfg = json.loads(json.dumps(self.defaults))
        self._load_into_widgets()
        self._restyle()
        self._render_preview()

    def _apply(self):
        self.cfg = self._collect()
        self.api.save_config(self.cfg)
        tooltip(t("saved"), parent=self)

    def _ok(self):
        self._apply()
        self.accept()

    def done(self, result):
        # Vorschau-Webansichten freigeben, sonst bleiben sie nach dem Schließen im Speicher
        self._timer.stop()
        self.preview.cleanup()
        super().done(result)

    # ---------- Vorschau ----------

    def _render_preview(self):
        self.preview.set_config(self.cfg)
