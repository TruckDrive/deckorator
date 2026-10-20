# Add-on-Zentrale: Karten statt Ankis grauer Namensliste. Ankis Liste bleibt unsichtbar im
# Fenster und wird beim Anklicken einer Karte mit ausgewählt, damit alle vorhandenen Knöpfe
# (Löschen, Updates, Dateien …) unverändert funktionieren.
import datetime

from aqt.qt import *

from . import ui
from .ui import Toggle


def _card(dialog, row, addon, t):
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
    for row, addon in enumerate(dialog.addons):
        v.addWidget(_card(dialog, row, addon, t))
    v.addStretch()
    area.setWidget(holder)


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
{root} QScrollArea#ctAddonCenter, {root} QScrollArea#ctAddonCenter > QWidget > QWidget {{ background: transparent; }}
"""
