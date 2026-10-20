# Online-Galerie: Wallpaper aus öffentlichen GitHub-Sammlungen durchsehen und für sich selbst
# laden. Die Bilder werden nicht mit Deckorator verteilt (sie gehören ihren Urhebern); erst wenn
# der Nutzer die Galerie öffnet, werden Liste und gewähltes Bild direkt von GitHub geladen.
# Damit das Durchblättern schnell geht, kommen Vorschaubilder verkleinert über den Bild-Proxy
# wsrv.nl (ein paar KB statt mehrerer MB); das Originalbild wird erst beim Übernehmen geladen.
import hashlib
import json
import os
import re
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor

from aqt import mw
from aqt.qt import *
from aqt.utils import openLink, showWarning, tooltip

from . import designs, theme, ui

UA = {"User-Agent": "Deckorator (Anki add-on)"}
CACHE = os.path.join(os.path.dirname(__file__), "user_files", "gallery")
IMAGE_RE = r"\.(jpe?g|png|webp)$"
LIST_MAX_AGE = 3 * 86400  # Liste so lange von der Platte nehmen, dann im Hintergrund auffrischen
THUMB = QSize(168, 95)
PROXY = "https://wsrv.nl/?url={url}&w={w}&h={h}&fit=cover&output=jpg&q=78"

# Repo und Branch werden über die API aufgelöst (Omarchy ist z.B. schon umgezogen)
SOURCES = {
    "omarchy": {"title": "Omarchy", "repo": "basecamp/omarchy",
                "match": r"^themes/([^/]+)/backgrounds/(?!omarchy\.)[^/]+" + IMAGE_RE},
    "ml4w": {"title": "ML4W Wallpaper", "repo": "mylinuxforwork/wallpaper",
             "match": r"^([^/]+)" + IMAGE_RE},
}
_resolved = {}
# eigener kleiner Pool: viele Vorschaubilder parallel, ohne Ankis Hintergrund-Threads zu blockieren
_pool = ThreadPoolExecutor(max_workers=6, thread_name_prefix="deckorator-gallery")


def _get(url, timeout=30):
    return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout).read()


def _write(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".part"
    with open(tmp, "wb") as f:
        f.write(data)
    os.replace(tmp, path)


def _resolve(source):
    """(aktueller Repo-Name, Standard-Branch); folgt Umbenennungen und Umzügen."""
    if source not in _resolved:
        info = json.loads(_get(f"https://api.github.com/repos/{SOURCES[source]['repo']}"))
        _resolved[source] = (info["full_name"], info["default_branch"])
    return _resolved[source]


def _list_file(source):
    return os.path.join(CACHE, f"list-{source}.json")


def cached_list(source):
    """(Einträge, Alter in Sekunden) von der Platte oder (None, None)."""
    try:
        with open(_list_file(source), encoding="utf-8") as f:
            data = json.load(f)
        _resolved.setdefault(source, (data["repo"], data["branch"]))
        return [tuple(x) for x in data["items"]], time.time() - data["time"]
    except (OSError, ValueError, KeyError, TypeError):
        return None, None


def list_images(source):
    """[(Anzeigename, Pfad, Gruppe)] aus dem Git-Baum des Repos; landet auch im Cache."""
    src = SOURCES[source]
    _resolved.pop(source, None)
    repo, branch = _resolve(source)
    tree = json.loads(_get(f"https://api.github.com/repos/{repo}/git/trees/{branch}?recursive=1"))
    out = []
    for item in tree.get("tree", []):
        m = re.match(src["match"], item["path"], re.I)
        if m and item.get("type") == "blob":
            group = m.group(1) if source == "omarchy" else ""
            name = os.path.splitext(os.path.basename(item["path"]))[0]
            label = f"{group.replace('-', ' ').title()} · {name}" if group else name.replace("-", " ")
            out.append((label, item["path"], group))
    out.sort(key=lambda x: x[0].lower())
    _write(_list_file(source), json.dumps({"time": time.time(), "repo": repo, "branch": branch, "items": out}).encode())
    return out


def _raw_url(source, path):
    repo, branch = _resolve(source)
    return f"https://raw.githubusercontent.com/{repo}/{branch}/{urllib.parse.quote(path)}"


def _local(folder, source, path, ext=""):
    return os.path.join(CACHE, folder, f"{source}-" + re.sub(r"[^A-Za-z0-9._-]", "_", path) + ext)


def download(source, path):
    """Originalbild (für das Design)."""
    local = _local("", source, path)
    if not os.path.isfile(local):
        _write(local, _get(_raw_url(source, path), timeout=120))
    return local


def scaled(source, path, folder, w, h, fallback=False):
    """Verkleinerte Kopie über den Proxy; fallback=True nimmt das Original, wenn der Proxy nicht geht."""
    local = _local(folder, source, path, ".jpg")
    if os.path.isfile(local):
        return local
    try:
        _write(local, _get(PROXY.format(url=urllib.parse.quote(_raw_url(source, path), safe=""), w=w, h=h), timeout=40))
        return local
    except Exception:
        if not fallback:
            raise
        return download(source, path)


class GalleryDialog(QDialog):
    def __init__(self, parent, t, get_cfg, on_design):
        super().__init__(parent)
        self.t = t
        self.get_cfg = get_cfg
        self.on_design = on_design
        self.items = []
        self.shown = []
        self.current = None
        self._alive = True
        self._list_gen = 0  # verhindert, dass eine spät fertige Liste die andere Quelle überschreibt
        self._preview_gen = 0
        self._thumbs_requested = set()
        self.setObjectName("ctDialog")  # gleicher Look wie das Einstellungsfenster
        self.setWindowTitle(t("gallery"))
        self.resize(1080, 680)
        v = QVBoxLayout(self)
        note = QLabel(t("gallery_note"))
        note.setWordWrap(True)
        note.setObjectName("ctHint")
        v.addWidget(note)
        top = QHBoxLayout()
        # Knöpfe statt Aufklappliste: beide Quellen bleiben immer sichtbar
        self.source_buttons = {}
        group = QButtonGroup(self)
        for key, src in SOURCES.items():
            b = QPushButton(src["title"])
            b.setCheckable(True)
            b.clicked.connect(lambda _=False, k=key: self.set_source(k))
            group.addButton(b)
            top.addWidget(b)
            self.source_buttons[key] = b
        self.source = None
        self.filter = QLineEdit()
        self.filter.setPlaceholderText(t("gallery_filter"))
        self.filter.textChanged.connect(self._fill)
        b_repo = QPushButton(t("gallery_repo"))
        b_repo.clicked.connect(lambda: openLink(f"https://github.com/{SOURCES[self.source]['repo']}"))
        top.addWidget(self.filter, 1)
        top.addWidget(b_repo)
        v.addLayout(top)

        split = QHBoxLayout()
        self.list = QListWidget()
        self.list.setViewMode(QListView.ViewMode.IconMode)
        self.list.setIconSize(THUMB)
        self.list.setGridSize(QSize(THUMB.width() + 14, THUMB.height() + 38))
        self.list.setResizeMode(QListView.ResizeMode.Adjust)
        self.list.setMovement(QListView.Movement.Static)
        self.list.setUniformItemSizes(True)
        self.list.setWordWrap(True)
        self.list.setTextElideMode(Qt.TextElideMode.ElideRight)
        self.list.setMinimumWidth(3 * (THUMB.width() + 14) + 24)
        c = ui.COLORS
        if c:
            self.list.setStyleSheet(
                f"QListWidget {{ background: {c['surface']}; border: 1px solid {c['border']}; border-radius: 12px; outline: 0; }}"
                f"QListWidget::item {{ border-radius: 10px; padding: 4px; color: {c['text']}; }}"
                f"QListWidget::item:hover {{ background: {c['accent_soft']}; }}"
                f"QListWidget::item:selected {{ background: {c['accent_soft']}; color: {c['accent_text']}; }}")
        self.list.currentRowChanged.connect(self._select)
        self.list.verticalScrollBar().valueChanged.connect(lambda _: self._load_visible_thumbs())
        self._placeholder = self._blank_icon()
        right = QVBoxLayout()
        self.preview = QLabel(t("gallery_pick"))
        self.preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview.setMinimumSize(420, 300)
        self.preview.setObjectName("ctHint")
        self.preview.setWordWrap(True)
        self.caption = QLabel()
        self.caption.setObjectName("ctHint")
        self.caption.setAlignment(Qt.AlignmentFlag.AlignCenter)
        right.addWidget(self.preview, 1)
        right.addWidget(self.caption)
        split.addWidget(self.list, 3)
        split.addLayout(right, 2)
        v.addLayout(split, 1)
        bottom = QHBoxLayout()
        self.status = QLabel()
        self.status.setObjectName("ctHint")
        bottom.addWidget(self.status, 1)
        self.use = QPushButton(t("gallery_use"))
        self.use.setObjectName("ctPrimary")
        self.use.setEnabled(False)
        self.use.clicked.connect(self._use)
        close = QPushButton(t("cancel"))
        close.clicked.connect(self.reject)
        bottom.addWidget(close)
        bottom.addWidget(self.use)
        v.addLayout(bottom)
        self.set_source("omarchy")

    def done(self, result):
        self._alive = False
        super().done(result)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        QTimer.singleShot(0, self._load_visible_thumbs)

    def _blank_icon(self):
        pm = QPixmap(THUMB)
        pm.fill(QColor(128, 128, 128, 40))
        return QIcon(pm)

    def _run(self, fn, done):
        """fn im Hintergrund, done(Ergebnis oder Exception) im Hauptthread, solange das Fenster offen ist."""
        def finished(fut):
            try:
                result = fut.result()
            except Exception as e:
                result = e
            mw.taskman.run_on_main(lambda: self._alive and done(result))
        _pool.submit(fn).add_done_callback(finished)

    # ---------- Liste ----------

    def set_source(self, source):
        self.source_buttons[source].setChecked(True)
        if source == self.source:
            return
        self.source = source
        self._list_gen += 1
        gen = self._list_gen
        self.current = None
        self.use.setEnabled(False)
        self.preview.setText(self.t("gallery_pick"))
        self.caption.clear()
        items, age = cached_list(source)
        if items is not None:
            self.items = items
            self._fill()
            if age < LIST_MAX_AGE:
                return
        else:
            self.items = []
            self._fill()
            self.status.setText(self.t("gallery_loading"))

        def done(result):
            if gen != self._list_gen:
                return
            if isinstance(result, Exception):
                # mit Cache weiterarbeiten, sonst Fehler zeigen
                self.status.setText("" if self.items else self.t("gallery_error").format(err=result))
                return
            self.items = result
            self._fill()

        self._run(lambda: list_images(source), done)

    def _fill(self):
        q = self.filter.text().lower()
        self.list.clear()
        self.shown = [it for it in self.items if q in it[0].lower()]
        for label, path, _group in self.shown:
            item = QListWidgetItem(self._placeholder, label)
            item.setToolTip(label)
            item.setSizeHint(self.list.gridSize())
            thumb = _local("thumbs", self.source, path, ".jpg")
            if os.path.isfile(thumb):
                item.setIcon(QIcon(thumb))
            self.list.addItem(item)
        self.status.setText(self.t("gallery_count").format(n=len(self.shown)) if self.items else self.status.text())
        QTimer.singleShot(0, self._load_visible_thumbs)

    def _load_visible_thumbs(self):
        """Nur die Vorschaubilder holen, die gerade zu sehen sind (plus eine Reihe darunter)."""
        if not self.shown:
            return
        view = self.list.viewport().rect().adjusted(0, 0, 0, self.list.gridSize().height())
        source, gen = self.source, self._list_gen
        for row, (_label, path, _group) in enumerate(self.shown):
            key = (source, path)
            if key in self._thumbs_requested:
                continue
            item = self.list.item(row)
            if item is None or not self.list.visualItemRect(item).intersects(view):
                continue
            self._thumbs_requested.add(key)
            if os.path.isfile(_local("thumbs", source, path, ".jpg")):
                continue

            def done(result, path=path):
                if isinstance(result, Exception) or gen != self._list_gen:
                    self._thumbs_requested.discard((source, path))
                    return
                for r, it in enumerate(self.shown):
                    if it[1] == path and self.list.item(r):
                        self.list.item(r).setIcon(QIcon(result))
                        break

            self._run(lambda p=path: scaled(source, p, "thumbs", THUMB.width() * 2, THUMB.height() * 2), done)

    # ---------- Auswahl ----------

    def _select(self, row):
        if row < 0 or row >= len(self.shown):
            return
        label, path, group = self.shown[row]
        source = self.source
        self._preview_gen += 1
        gen = self._preview_gen
        self.current = (path, label, group, source)
        self.use.setEnabled(True)  # das Original wird erst beim Übernehmen geladen
        self.caption.setText(label)
        thumb = _local("thumbs", source, path, ".jpg")
        if os.path.isfile(thumb):  # sofort das kleine Bild, dann das schärfere nachladen
            self._show(thumb)
        else:
            self.preview.setText(self.t("gallery_loading"))

        def done(result):
            if gen != self._preview_gen:
                return
            if isinstance(result, Exception):
                self.preview.setText(self.t("gallery_error").format(err=result))
                return
            self._show(result)

        self._run(lambda: scaled(source, path, "previews", 1200, 675, fallback=True), done)

    def _show(self, local):
        pm = QPixmap(local)
        if pm.isNull():
            return
        self.preview.setPixmap(pm.scaled(self.preview.size(), Qt.AspectRatioMode.KeepAspectRatio,
                                         Qt.TransformationMode.SmoothTransformation))

    def _use(self):
        path, label, group, source = self.current
        self.use.setEnabled(False)
        self.status.setText(self.t("gallery_downloading"))

        def done(result):
            self.use.setEnabled(True)
            self.status.clear()
            if isinstance(result, Exception):
                showWarning(self.t("gallery_error").format(err=result), parent=self)
                return
            self._make_design(result, label, group, source)

        self._run(lambda: download(source, path), done)

    def _make_design(self, local, label, group, source):
        cfg = self.get_cfg()
        overrides = {}
        pack = theme.PACKS.get("om_" + group) if source == "omarchy" else None
        if pack:  # Omarchy-Bild: die Farben des zugehörigen Themes statt der aus dem Bild geschätzten
            overrides = {k: pack[k] for k in ("accent", "bg_light", "bg_dark")}
        look = designs.design_from_image(local, label, cfg, overrides)
        if not look:
            showWarning(self.t("import_err"), parent=self)
            return
        tooltip(self.t("design_saved"), parent=self.parent())
        self.on_design(look)
        self.accept()
