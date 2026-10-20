# Optik des Einstellungsfensters: eigenes Qt-Stylesheet (hell/dunkel, Akzentfarbe live)
# und Schalter statt Häkchen. Unabhängig vom System-Qt-Stil, damit es überall gleich aussieht.
import os

from aqt.qt import *

from . import theme

ASSETS = os.path.join(os.path.dirname(__file__), "assets").replace(os.sep, "/")

# Aktuelle Farben, damit selbst gezeichnete Widgets (Toggle) zum Stylesheet passen
COLORS = {}


def palette(accent, night):
    if night:
        c = {"window": "#18181b", "surface": "#222226", "input": "#2b2b30", "border": "#34343a",
             "track": "#3d3d44", "text": "#ececef", "sub": "#9d9da6", "accent_text": theme._mix(accent, "#ffffff", .35)}
    else:
        c = {"window": "#f3f3f5", "surface": "#ffffff", "input": "#f6f6f8", "border": "#e2e2e7",
             "track": "#d4d4da", "text": "#1d1d21", "sub": "#6c6c75", "accent_text": theme._mix(accent, "#000000", .2)}
    c["accent"] = accent
    c["accent_soft"] = theme._rgba(accent, .16 if night else .12)
    c["on_accent"] = "#ffffff" if _luma(accent) < .62 else "#111111"
    c["chevron"] = f"{ASSETS}/chevron-{'dark' if night else 'light'}.svg"
    return c


def _luma(hex_color):
    r, g, b = theme._rgb(hex_color)
    return (0.299 * r + 0.587 * g + 0.114 * b) / 255


def stylesheet(c):
    return f"""
QDialog#ctDialog {{ background: {c['window']}; }}
QDialog#ctDialog QWidget {{ color: {c['text']}; font-size: 10pt; }}
QScrollArea, QScrollArea > QWidget > QWidget, QStackedWidget, QWidget#ctPage {{ background: transparent; border: none; }}

QListWidget#ctNav {{ background: transparent; border: none; outline: 0; padding-top: 4px; }}
QListWidget#ctNav::item {{ padding: 9px 14px; margin: 1px 0; border-radius: 10px; }}
QListWidget#ctNav::item:hover {{ background: {c['accent_soft']}; }}
QListWidget#ctNav::item:selected {{ background: {c['accent_soft']}; color: {c['accent_text']}; font-weight: 600; }}

QDialog#ctDialog QLabel#ctPageTitle {{ font-size: 18pt; font-weight: 700; padding: 0 2px 4px; }}
QDialog#ctDialog QLabel#ctSectionTitle {{ font-weight: 650; font-size: 10.5pt; }}
QDialog#ctDialog QLabel#ctHint {{ color: {c['sub']}; font-size: 9pt; }}
QFrame#ctCard {{ background: {c['surface']}; border: 1px solid {c['border']}; border-radius: 14px; }}
QFrame#ctPreviewFrame {{ background: {c['surface']}; border: 1px solid {c['border']}; border-radius: 14px; }}

QPushButton {{ background: {c['input']}; border: 1px solid {c['border']}; border-radius: 9px;
  padding: 6px 14px; color: {c['text']}; }}
QPushButton:hover {{ border-color: {c['accent']}; }}
QPushButton:checked {{ background: {c['accent_soft']}; border-color: {c['accent']}; color: {c['accent_text']}; font-weight: 600; }}
QPushButton:disabled {{ color: {c['sub']}; border-color: {c['border']}; }}
QPushButton#ctPrimary {{ background: {c['accent']}; color: {c['on_accent']}; border: none; font-weight: 600; padding: 7px 20px; }}
QPushButton#ctPrimary:hover {{ background: {theme._mix(c['accent'], '#000000', .1)}; }}
QPushButton#ctGhost {{ background: transparent; border: none; color: {c['sub']}; }}
QPushButton#ctGhost:hover {{ color: {c['text']}; }}

QComboBox, QFontComboBox {{ background: {c['input']}; border: 1px solid {c['border']}; border-radius: 9px;
  padding: 5px 10px; min-height: 20px; combobox-popup: 0; }}
QComboBox:on {{ border-color: {c['accent']}; }}
QComboBox:hover, QFontComboBox:hover {{ border-color: {c['accent']}; }}
QComboBox::drop-down {{ border: none; width: 26px; }}
QComboBox::down-arrow {{ image: url({c['chevron']}); width: 12px; height: 12px; }}
QComboBox QFrame {{ background: transparent; border: none; }}
QComboBox QAbstractItemView {{ background: {c['surface']}; border: 1px solid {c['border']}; border-radius: 12px;
  padding: 6px; outline: 0; selection-background-color: {c['accent_soft']}; selection-color: {c['accent_text']}; }}
QComboBox QAbstractItemView::item {{ min-height: 30px; padding: 0 10px; border-radius: 8px; color: {c['text']}; }}
QComboBox QAbstractItemView::item:hover {{ background: {c['accent_soft']}; }}
QComboBox QAbstractItemView::item:selected {{ background: {c['accent_soft']}; color: {c['accent_text']}; font-weight: 600; }}

QSlider::groove:horizontal {{ height: 4px; background: {c['track']}; border-radius: 2px; }}
QSlider::sub-page:horizontal {{ background: {c['accent']}; border-radius: 2px; }}
QSlider::handle:horizontal {{ background: #ffffff; border: 2px solid {c['accent']}; width: 14px; height: 14px;
  margin: -7px 0; border-radius: 9px; }}
QSlider::sub-page:horizontal:disabled {{ background: {c['track']}; }}
QSlider::handle:horizontal:disabled {{ border-color: {c['track']}; }}

QPlainTextEdit {{ background: {c['input']}; border: 1px solid {c['border']}; border-radius: 10px; padding: 6px; }}
QPlainTextEdit:focus {{ border-color: {c['accent']}; }}

QScrollBar:vertical {{ background: transparent; width: 10px; margin: 2px; }}
QScrollBar::handle:vertical {{ background: {c['track']}; border-radius: 3px; min-height: 30px; }}
QScrollBar::add-line, QScrollBar::sub-line {{ height: 0; width: 0; }}
QScrollBar::add-page, QScrollBar::sub-page {{ background: transparent; }}
QSplitter::handle {{ background: transparent; width: 10px; }}
QToolTip {{ background: {c['surface']}; color: {c['text']}; border: 1px solid {c['border']}; padding: 4px 6px; }}
"""


def modern_popup(combo, own_delegate=True):
    """Aufklappliste als schwebende, abgerundete Karte statt nativer Liste. own_delegate=False
    für die Schriftauswahl, deren eigener Delegate die Schriften in ihrer Form zeigt."""
    if own_delegate:
        combo.setView(QListView())
        combo.setItemDelegate(QStyledItemDelegate(combo))
    popup = combo.view().window()
    popup.setWindowFlags(popup.windowFlags() | Qt.WindowType.FramelessWindowHint
                         | Qt.WindowType.NoDropShadowWindowHint)
    popup.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)


class Toggle(QCheckBox):
    """Schalter im Stil moderner Einstellungen; verhält sich wie eine QCheckBox."""

    W, H = 38, 22

    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)

    def sizeHint(self):
        fm = self.fontMetrics()
        return QSize(self.W + 12 + fm.horizontalAdvance(self.text()), max(self.H + 6, fm.height() + 8))

    def minimumSizeHint(self):
        return QSize(self.W + 12, self.H + 6)

    def hitButton(self, pos):
        return self.rect().contains(pos)

    def paintEvent(self, _event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        if not self.isEnabled():
            p.setOpacity(.45)
        y = (self.height() - self.H) / 2
        on = self.isChecked()
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(COLORS.get("accent", "#888") if on else COLORS.get("track", "#888")))
        p.drawRoundedRect(QRectF(0, y, self.W, self.H), self.H / 2, self.H / 2)
        p.setBrush(QColor("#ffffff"))
        knob = self.H - 6
        x = self.W - knob - 3 if on else 3
        p.drawEllipse(QRectF(x, y + 3, knob, knob))
        p.setPen(QColor(COLORS.get("text", "#000")))
        p.drawText(QRectF(self.W + 12, 0, self.width() - self.W - 12, self.height()),
                   int(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft), self.text())


class ColorButton(QPushButton):
    """Farbfeld mit Hex-Wert; öffnet beim Klick den Farbwähler."""
    changed = pyqtSignal()

    def __init__(self, color, parent=None):
        super().__init__(parent)
        self.setFixedSize(104, 30)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.clicked.connect(self._pick)
        self.set_color(color)

    def set_color(self, color):
        self._color = color
        fg = "#ffffff" if _luma(color) < .6 else "#111111"
        self.setText(color.upper())
        self.setStyleSheet(f"QPushButton {{ background: {color}; color: {fg}; border: 1px solid rgba(128,128,128,.35);"
                           " border-radius: 9px; font-family: monospace; font-weight: 600; }}"
                           "QPushButton:hover { border: 2px solid rgba(128,128,128,.8); }")

    def color(self):
        return self._color

    def _pick(self):
        col = QColorDialog.getColor(QColor(self._color), self, "")
        if col.isValid():
            self.set_color(col.name())
            self.changed.emit()


class Section(QFrame):
    """Karte mit Titel, optionalem Hinweis und einem Formular darunter."""

    def __init__(self, title, hint=None, parent=None):
        super().__init__(parent)
        self.setObjectName("ctCard")
        v = QVBoxLayout(self)
        v.setContentsMargins(18, 14, 18, 16)
        v.setSpacing(10)
        lbl = QLabel(title)
        lbl.setObjectName("ctSectionTitle")
        v.addWidget(lbl)
        if hint:
            h = QLabel(hint)
            h.setObjectName("ctHint")
            h.setWordWrap(True)
            v.addWidget(h)
        self.form = QFormLayout()
        self.form.setHorizontalSpacing(16)
        self.form.setVerticalSpacing(12)
        self.form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        v.addLayout(self.form)

    def row(self, label, widget=None):
        if widget is None:
            self.form.addRow(label)
        else:
            self.form.addRow(label, widget)
        return widget
