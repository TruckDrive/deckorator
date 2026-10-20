# Online-Galerie: Wallpaper aus öffentlichen GitHub-Sammlungen durchsehen und für sich selbst
# laden. Die Bilder werden nicht mit Deckorator verteilt (sie gehören ihren Urhebern); erst wenn
# der Nutzer die Galerie öffnet, werden Liste und gewähltes Bild direkt von GitHub geladen.
import json
import os
import re
import urllib.request

from aqt import mw
from aqt.qt import *
from aqt.utils import openLink, showWarning, tooltip

from . import designs, theme

UA = {"User-Agent": "Deckorator (Anki add-on)"}
CACHE = os.path.join(os.path.dirname(__file__), "user_files", "gallery")
IMAGE_RE = r"\.(jpe?g|png|webp)$"

# Repo und Branch werden beim Öffnen über die API aufgelöst (Omarchy ist z.B. schon umgezogen)
SOURCES = {
    "omarchy": {"title": "Omarchy", "repo": "basecamp/omarchy",
                "match": r"^themes/([^/]+)/backgrounds/(?!omarchy\.)[^/]+" + IMAGE_RE},
    "ml4w": {"title": "ML4W Wallpaper", "repo": "mylinuxforwork/wallpaper",
             "match": r"^([^/]+)" + IMAGE_RE},
}
_resolved = {}


def _resolve(source):
    """(aktueller Repo-Name, Standard-Branch); folgt Umbenennungen und Umzügen."""
    if source not in _resolved:
        info = json.loads(_get(f"https://api.github.com/repos/{SOURCES[source]['repo']}"))
        _resolved[source] = (info["full_name"], info["default_branch"])
    return _resolved[source]


def _get(url, timeout=30):
    return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout).read()


def list_images(source):
    """[(Anzeigename, Pfad, Gruppe)] aus dem Git-Baum des Repos (ein API-Aufruf)."""
    src = SOURCES[source]
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
    return sorted(out)


def download(source, path):
    repo, branch = _resolve(source)
    os.makedirs(CACHE, exist_ok=True)
    local = os.path.join(CACHE, f"{source}-" + re.sub(r"[^A-Za-z0-9._-]", "_", path))
    if not os.path.isfile(local):
        data = _get(f"https://raw.githubusercontent.com/{repo}/{branch}/{path}", timeout=90)
        with open(local, "wb") as f:
            f.write(data)
    return local


class GalleryDialog(QDialog):
    def __init__(self, parent, t, get_cfg, on_design):
        super().__init__(parent)
        self.t = t
        self.get_cfg = get_cfg
        self.on_design = on_design
        self.items = []
        self.current = None
        self.setWindowTitle(t("gallery"))
        self.resize(980, 640)
        v = QVBoxLayout(self)
        note = QLabel(t("gallery_note"))
        note.setWordWrap(True)
        note.setObjectName("ctHint")
        v.addWidget(note)
        top = QHBoxLayout()
        self.source = QComboBox()
        for key, src in SOURCES.items():
            self.source.addItem(src["title"], key)
        self.source.currentIndexChanged.connect(self.load_list)
        b_repo = QPushButton(t("gallery_repo"))
        b_repo.clicked.connect(lambda: openLink(f"https://github.com/{SOURCES[self.source.currentData()]['repo']}"))
        self.filter = QLineEdit()
        self.filter.setPlaceholderText(t("gallery_filter"))
        self.filter.textChanged.connect(self._fill)
        top.addWidget(self.source)
        top.addWidget(self.filter, 1)
        top.addWidget(b_repo)
        v.addLayout(top)
        split = QHBoxLayout()
        self.list = QListWidget()
        self.list.currentRowChanged.connect(self._select)
        self.preview = QLabel(t("gallery_pick"))
        self.preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview.setMinimumSize(560, 360)
        self.preview.setObjectName("ctHint")
        split.addWidget(self.list, 2)
        split.addWidget(self.preview, 3)
        v.addLayout(split, 1)
        bottom = QHBoxLayout()
        bottom.addStretch()
        self.use = QPushButton(t("gallery_use"))
        self.use.setObjectName("ctPrimary")
        self.use.setEnabled(False)
        self.use.clicked.connect(self._use)
        close = QPushButton(t("cancel"))
        close.clicked.connect(self.reject)
        bottom.addWidget(close)
        bottom.addWidget(self.use)
        v.addLayout(bottom)
        self.load_list()

    def load_list(self):
        source = self.source.currentData()
        self.list.clear()
        self.list.addItem(self.t("gallery_loading"))

        def done(fut):
            try:
                self.items = fut.result()
            except Exception as e:
                self.list.clear()
                self.list.addItem(self.t("gallery_error").format(err=e))
                return
            self._fill()

        mw.taskman.run_in_background(lambda: list_images(source), done)

    def _fill(self):
        q = self.filter.text().lower()
        self.list.clear()
        self.shown = [it for it in self.items if q in it[0].lower()]
        for label, _path, _group in self.shown:
            self.list.addItem(label)

    def _select(self, row):
        if row < 0 or row >= len(getattr(self, "shown", [])):
            return
        label, path, group = self.shown[row]
        source = self.source.currentData()
        self.use.setEnabled(False)
        self.preview.setText(self.t("gallery_loading"))

        def done(fut):
            try:
                local = fut.result()
            except Exception as e:
                self.preview.setText(self.t("gallery_error").format(err=e))
                return
            pm = QPixmap(local)
            self.preview.setPixmap(pm.scaled(self.preview.size(), Qt.AspectRatioMode.KeepAspectRatio,
                                             Qt.TransformationMode.SmoothTransformation))
            self.current = (local, label, group, source)
            self.use.setEnabled(True)

        mw.taskman.run_in_background(lambda: download(source, path), done)

    def _use(self):
        local, label, group, source = self.current
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
