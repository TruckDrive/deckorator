# Add-on-Zentrale: Karten statt Ankis grauer Namensliste. Ankis Liste bleibt unsichtbar im
# Fenster und wird beim Anklicken einer Karte mit ausgewählt, damit alle vorhandenen Knöpfe
# (Löschen, Updates, Dateien …) unverändert funktionieren.
import datetime
import json
import os

from aqt.qt import *

from . import ui
from .ui import Toggle

# Angeheftete Add-ons stehen oben. Eigene Datei statt Add-on-Konfiguration, damit ein offenes
# Einstellungsfenster sie beim Speichern nicht mit einem alten Stand überschreibt.
PINNED_FILE = os.path.join(os.path.dirname(__file__), "user_files", "pinned_addons.json")
PIN_SVG = ('<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 16 16"><path d="M10.2 1.8 '
           '14.2 5.8 12.9 6.2 10.4 8.7 10.6 11.6 9.6 12.6 6.8 9.8 3 13.6 2.4 13 6.2 9.2 3.4 6.4 4.4 5.4 7.3 5.6 9.8 '
           '3.1Z" fill="{color}"/></svg>')


def pinned():
    try:
        with open(PINNED_FILE, encoding="utf-8") as f:
            return [d for d in json.load(f) if isinstance(d, str)]
    except (OSError, ValueError, TypeError):
        return []


def _set_pinned(dir_name, on):
    dirs = [d for d in pinned() if d != dir_name] + ([dir_name] if on else [])
    os.makedirs(os.path.dirname(PINNED_FILE), exist_ok=True)
    with open(PINNED_FILE, "w", encoding="utf-8") as f:
        json.dump(dirs, f)


def _pin_icon(color):
    pm = QPixmap()
    pm.loadFromData(PIN_SVG.format(color=color).encode(), "SVG")
    return QIcon(pm)


def _card(dialog, row, addon, t, is_pinned):
    mgr = dialog.mgr
    card = QFrame()
    card.setObjectName("ctAddonCard")
    card.setCursor(Qt.CursorShape.PointingHandCursor)
    h = QHBoxLayout(card)
    h.setContentsMargins(14, 10, 12, 10)
    h.setSpacing(12)

    text = QVBoxLayout()
    text.setSpacing(2)
    title = QLabel(addon.human_name())
    title.setObjectName("ctAddonTitle")
    title.setWordWrap(True)
    facts = []
    if addon.human_version:
        facts.append(addon.human_version)
    if addon.installed_at:
        facts.append(t("ac_updated").format(date=datetime.date.fromtimestamp(addon.installed_at).strftime("%d.%m.%Y")))
    if addon.ankiweb_id():
        facts.append(f"AnkiWeb {addon.ankiweb_id()}")
    if not addon.compatible():
        facts.append(t("ac_incompatible"))
    sub = QLabel(" · ".join(facts) or addon.dir_name)
    sub.setObjectName("ctHint")
    sub.setWordWrap(True)
    text.addWidget(title)
    text.addWidget(sub)
    h.addLayout(text, 1)

    def select():
        dialog.form.addonList.setCurrentRow(row)

    configurable = bool(mgr.configAction(addon.dir_name) or mgr.getConfig(addon.dir_name) is not None)
    if configurable:
        b = QPushButton(t("ac_settings"))
        b.clicked.connect(lambda: (select(), dialog.onConfig()))
        h.addWidget(b)
    if addon.page():
        b = QPushButton(t("ac_page"))
        b.clicked.connect(lambda: (select(), dialog.onViewPage()))
        h.addWidget(b)
    pin = QToolButton()
    pin.setObjectName("ctAddonPin")
    pin.setCheckable(True)
    pin.setChecked(is_pinned)
    pin.setIcon(_pin_icon(ui.COLORS.get("accent", "#f59e0b") if is_pinned else ui.COLORS.get("sub", "#8a8a94")))
    pin.setIconSize(QSize(16, 16))
    pin.setCursor(Qt.CursorShape.PointingHandCursor)
    pin.setToolTip(t("ac_unpin") if is_pinned else t("ac_pin"))
    # neu aufbauen erst nach dem Klick, der Knopf selbst wird dabei gelöscht
    pin.clicked.connect(lambda on: (_set_pinned(addon.dir_name, on), QTimer.singleShot(0, lambda: build(dialog, t))))
    h.addWidget(pin)
    toggle = Toggle("")
    toggle.setChecked(addon.enabled)
    toggle.setToolTip(t("ac_toggle"))
    toggle.setFixedWidth(Toggle.W + 4)

    def on_toggle(_state):
        select()
        dialog.onToggleEnabled()

    toggle.clicked.connect(on_toggle)
    h.addWidget(toggle)
    if not addon.enabled:
        effect = QGraphicsOpacityEffect(card)
        effect.setOpacity(.55)
        card.setGraphicsEffect(effect)
    card.mousePressEvent = lambda _e: select()
    return card


def build(dialog, t):
    """Kartenansicht anlegen oder neu füllen."""
    area = getattr(dialog, "_ct_center", None)
    if area is None:
        area = QScrollArea()
        area.setObjectName("ctAddonCenter")
        area.setWidgetResizable(True)
        area.setFrameShape(QFrame.Shape.NoFrame)
        layout = dialog.form.addonList.parentWidget().layout()
        layout.replaceWidget(dialog.form.addonList, area)
        dialog.form.addonList.hide()
        dialog._ct_center = area
        # Anki zeichnet die Liste nach jeder Aktion neu; die Karten ziehen mit
        original = dialog.redrawAddons
        dialog.redrawAddons = lambda *a, **k: (original(*a, **k), build(dialog, t))
    holder = QWidget()
    v = QVBoxLayout(holder)
    v.setContentsMargins(2, 2, 6, 2)
    v.setSpacing(8)
    pins = pinned()
    rows = list(enumerate(dialog.addons))
    top = sorted(((r, a) for r, a in rows if a.dir_name in pins), key=lambda x: pins.index(x[1].dir_name))
    rest = [(r, a) for r, a in rows if a.dir_name not in pins]
    for title, group, is_pinned in ((t("ac_pinned"), top, True), (t("ac_all"), rest, False)):
        if not group:
            continue
        if top:  # Überschriften nur, wenn es überhaupt zwei Gruppen gibt
            head = QLabel(title)
            head.setObjectName("ctAddonGroup")
            v.addWidget(head)
        for row, addon in group:
            v.addWidget(_card(dialog, row, addon, t, is_pinned))
    v.addStretch()
    # Bildlaufposition halten, sonst springt die Liste beim Anheften nach oben
    pos = area.verticalScrollBar().value()
    area.setWidget(holder)
    QTimer.singleShot(0, lambda: area.verticalScrollBar().setValue(pos))


def remove(dialog):
    area = getattr(dialog, "_ct_center", None)
    if area is not None:
        layout = area.parentWidget().layout()
        layout.replaceWidget(area, dialog.form.addonList)
        dialog.form.addonList.show()
        area.deleteLater()
        dialog._ct_center = None


CARD_CSS = """
{root} QFrame#ctAddonCard {{ background: {panel}; border: 1px solid {edge}; border-radius: 14px; }}
{root} QFrame#ctAddonCard:hover {{ border-color: {accent_mid}; }}
{root} QLabel#ctAddonTitle {{ font-weight: 650; font-size: 10.5pt; }}
{root} QLabel#ctAddonGroup {{ color: {sub}; font-weight: 600; font-size: 9pt; padding: 6px 4px 0; }}
{root} QToolButton#ctAddonPin {{ background: transparent; border: none; border-radius: 8px; padding: 5px; }}
{root} QToolButton#ctAddonPin:hover {{ background: {accent_soft}; }}
{root} QScrollArea#ctAddonCenter, {root} QScrollArea#ctAddonCenter > QWidget > QWidget {{ background: transparent; }}
"""
