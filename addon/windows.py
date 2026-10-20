# Qt-Fenster von Anki im Deckorator-Look: Kartenverwaltung (Browse) und Add-on-Liste.
# Nur Farben, Rundungen und Abstände; Aufbau und Funktionen der Fenster bleiben unverändert.
import weakref

from aqt.qt import *
from aqt.theme import theme_manager

from . import ui

# Offene, gestylte Fenster, damit Speichern und Hell/Dunkel-Wechsel sie live umfärben
_open = weakref.WeakKeyDictionary()  # Fenster -> Art ("browser" / "addons")

TABLE = """
{root} QTableView {{ background: {surface}; alternate-background-color: {alt}; border: 1px solid {border};
  border-radius: 12px; gridline-color: transparent; outline: 0; }}
{root} QHeaderView {{ background: transparent; border: none; }}
/* Auswahlfarbe der Kartenliste bewusst nicht ändern: in Akzentfarbe wäre sie z.B. bei Rosé
   nicht von einer roten Flagge zu unterscheiden */
{root} QHeaderView::section {{ background: {surface}; color: {sub}; border: none; border-bottom: 1px solid {border};
  padding: 6px 10px; font-weight: 600; }}
{root} QHeaderView::section:hover {{ color: {text}; }}
{root} QTableCornerButton::section {{ background: {surface}; border: none; }}
{root} QComboBox#searchEdit {{ border-radius: 17px; padding: 6px 14px; min-height: 22px; }}
{root} QComboBox#searchEdit QLineEdit {{ background: transparent; border: none; selection-background-color: {accent_soft}; }}
{root} QDockWidget {{ titlebar-close-icon: none; }}
{root} QDockWidget::title {{ background: transparent; padding: 6px 4px; }}
{root} QLineEdit {{ background: {input}; border: 1px solid {border}; border-radius: 9px; padding: 5px 10px; }}
{root} QLineEdit:focus {{ border-color: {accent}; }}
{root} QToolBar {{ background: transparent; border: none; spacing: 2px; }}
{root} QToolButton {{ background: transparent; border: none; border-radius: 8px; padding: 4px; }}
{root} QToolButton:hover {{ background: {accent_soft}; }}
{root} QToolButton:checked {{ background: {accent_soft}; }}
{root} QMenuBar {{ background: {window}; }}
{root} QMenuBar::item:selected {{ background: {accent_soft}; border-radius: 6px; }}
"""

# Die Seitenleiste setzt ihr eigenes Stylesheet; dieses ersetzt es
SIDEBAR = """
QTreeView {{ background: transparent; border: 0; padding: 4px 0 4px 4px; outline: 0;
  selection-background-color: {accent_soft}; selection-color: {text}; show-decoration-selected: 0; }}
QTreeView::item {{ padding: 2px 6px; border-radius: 7px; }}
QTreeView::item:hover {{ background: {hover}; }}
QTreeView::item:selected {{ background: {accent_soft}; color: {accent_text}; }}
"""

# "Kräftig": Spotlight in Akzentfarbe hinter dem Fenster, schwebende Glas-Karten, Akzente
BOLD = """
{root} {{ background: qradialgradient(cx:0.5, cy:-0.2, radius:1.05, fx:0.5, fy:-0.2,
  stop:0 {glow}, stop:0.6 {window}, stop:1 {window}); }}
{root} QTableView {{ background: {panel}; alternate-background-color: {panel_alt}; border: 1px solid {edge};
  border-radius: 16px; }}
{root} QHeaderView::section {{ background: transparent; color: {accent_text}; border: none;
  border-bottom: 2px solid {accent}; padding: 9px 10px; font-weight: 650; }}
{root} QTableCornerButton::section {{ background: transparent; }}
{root} QComboBox#searchEdit {{ background: {panel}; border: 1px solid {accent_mid}; }}
{root} QListWidget {{ background: {panel}; border: 1px solid {edge}; border-radius: 16px; }}
{root} QListWidget::item:selected {{ background: {accent}; color: {on_accent}; }}
"""

SIDEBAR_BOLD = """
QTreeView {{ background: {panel}; border: 1px solid {edge}; border-radius: 16px; padding: 8px 4px 8px 6px; outline: 0;
  show-decoration-selected: 0; }}
QTreeView::item {{ padding: 4px 6px; border-radius: 8px; }}
QTreeView::item:hover {{ background: {hover}; }}
QTreeView::item:selected {{ background: {accent}; color: {on_accent}; }}
"""

ADDON_LIST = """
{root} QListWidget {{ background: {surface}; border: 1px solid {border}; border-radius: 12px; padding: 6px; outline: 0; }}
{root} QListWidget::item {{ padding: 7px 10px; border-radius: 8px; }}
{root} QListWidget::item:hover {{ background: {hover}; }}
{root} QListWidget::item:selected {{ background: {accent_soft}; }}
{root} QLabel {{ color: {sub}; }}
"""


# Standard-Bedienelemente für Dialoge wie Ankis Einstellungen: Reiter, Gruppen, Häkchen, Zahlenfelder
CONTROLS = """
{root} QTabWidget::pane {{ background: {panel}; border: 1px solid {edge}; border-radius: 14px; top: -1px; padding: 6px; }}
{root} QTabBar::tab {{ background: transparent; color: {sub}; padding: 6px 11px; margin: 0 2px 8px 0;
  border-radius: 9px; border: none; }}
{root} QTabBar::tab:hover:!selected {{ background: {hover}; color: {text}; }}
{root} QTabBar::tab:selected {{ background: {accent_soft}; color: {accent_text}; font-weight: 600; }}
{root} QGroupBox {{ background: {panel}; border: 1px solid {edge}; border-radius: 12px; margin-top: 16px;
  padding: 14px 10px 8px; }}
{root} QGroupBox::title {{ subcontrol-origin: margin; subcontrol-position: top left; left: 12px; padding: 0 4px;
  color: {accent_text}; font-weight: 600; }}
{root} QCheckBox, {root} QRadioButton {{ spacing: 8px; }}
{root} QCheckBox::indicator {{ width: 16px; height: 16px; border-radius: 5px; border: 1.5px solid {track};
  background: {input}; }}
{root} QCheckBox::indicator:hover {{ border-color: {accent}; }}
{root} QCheckBox::indicator:checked {{ background: {accent}; border-color: {accent}; image: url({check}); }}
{root} QRadioButton::indicator {{ width: 14px; height: 14px; border-radius: 8px; border: 1.5px solid {track};
  background: {input}; }}
{root} QRadioButton::indicator:checked {{ border: 5px solid {accent}; background: #ffffff; }}
{root} QSpinBox, {root} QDoubleSpinBox, {root} QLineEdit {{ background: {input}; border: 1px solid {border};
  border-radius: 8px; padding: 4px 8px; }}
{root} QSpinBox:focus, {root} QDoubleSpinBox:focus, {root} QLineEdit:focus {{ border-color: {accent}; }}
{root} QSpinBox::up-button, {root} QSpinBox::down-button, {root} QDoubleSpinBox::up-button,
{root} QDoubleSpinBox::down-button {{ subcontrol-origin: border; width: 18px; border: none; background: transparent; }}
{root} QSpinBox::up-button, {root} QDoubleSpinBox::up-button {{ subcontrol-position: top right; }}
{root} QSpinBox::down-button, {root} QDoubleSpinBox::down-button {{ subcontrol-position: bottom right; }}
{root} QSpinBox::up-arrow, {root} QDoubleSpinBox::up-arrow {{ image: url({chevron_up}); width: 9px; height: 9px; }}
{root} QSpinBox::down-arrow, {root} QDoubleSpinBox::down-arrow {{ image: url({chevron}); width: 9px; height: 9px; }}
"""


def _colors(cfg):
    """Fensterfarben aus der Deckorator-Hintergrundfarbe, damit Browse & Co. zum Hauptfenster passen."""
    from . import theme
    night = theme_manager.night_mode
    c = ui.palette(cfg["accent"], night)
    if night:
        bg = cfg["bg_dark"]
        c.update(window=bg, surface=theme._mix(bg, "#ffffff", .05), input=theme._mix(bg, "#ffffff", .08),
                 border=theme._mix(bg, "#ffffff", .12), track=theme._mix(bg, "#ffffff", .2))
    else:
        bg = cfg["bg_light"]
        c.update(window=bg, surface="#ffffff", input=theme._mix(bg, "#ffffff", .5),
                 border=theme._mix(bg, "#000000", .1), track=theme._mix(bg, "#000000", .18))
    c["alt"] = "#26262b" if night else "#f8f8fa"
    c["hover"] = "rgba(255,255,255,.05)" if night else "rgba(0,0,0,.04)"
    # für den kräftigen Stil
    c["glow"] = theme._mix(c["window"], cfg["accent"], .30 if night else .18)
    c["panel"] = "rgba(255,255,255,.045)" if night else "rgba(255,255,255,.80)"
    c["panel_alt"] = "rgba(255,255,255,.075)" if night else "rgba(250,250,252,.88)"
    c["edge"] = "rgba(255,255,255,.09)" if night else "rgba(0,0,0,.08)"
    c["accent_mid"] = theme._rgba(cfg["accent"], .55)
    c["check"] = f"{ui.ASSETS}/check.svg"
    c["chevron_up"] = f"{ui.ASSETS}/chevron-up-{'dark' if night else 'light'}.svg"
    return c


WINDOW_KINDS = ("browser", "editor", "stats", "deck_options", "preferences", "addons")


def window_mode(cfg, kind):
    """"bold", "subtle" oder "original" (= Anki unverändert) für ein Fenster."""
    if not cfg["areas"].get(kind, True):
        return "original"
    return cfg.get("window_styles", {}).get(kind) or cfg.get("window_style", "bold")


def _bold(cfg, kind):
    return window_mode(cfg, kind) == "bold"


def _style_browser(browser, cfg):
    c = _colors(cfg)
    root = "QMainWindow#ctWindow"
    browser.setObjectName("ctWindow")
    # Schriftgröße nicht anfassen: die Kartenverwaltung hat eine eigene Schrifteinstellung
    bold = _bold(cfg, "browser")
    browser.setStyleSheet(ui.stylesheet(c, root, font_size=None) + TABLE.format(root=root, **c)
                          + (BOLD.format(root=root, **c) if bold else ""))
    browser.sidebar.setStyleSheet((SIDEBAR_BOLD if bold else SIDEBAR).format(**c))
    table = browser.form.tableView
    table.setShowGrid(False)
    # luftigere Zeilen im kräftigen Stil; Ankis Höhe merken, um sie wiederherzustellen
    header = table.verticalHeader()
    if not hasattr(browser, "_ct_row_height"):
        browser._ct_row_height = header.defaultSectionSize()
    header.setDefaultSectionSize(browser._ct_row_height + (10 if bold else 0))
    if not getattr(browser, "_ct_popup", False):
        ui.modern_popup(browser.form.searchEdit)
        browser._ct_popup = True


def _unstyle_browser(browser):
    browser.setStyleSheet("")
    browser.sidebar._setup_style()  # Ankis eigenes Sidebar-Styling zurück
    browser.form.tableView.setShowGrid(True)
    if hasattr(browser, "_ct_row_height"):
        browser.form.tableView.verticalHeader().setDefaultSectionSize(browser._ct_row_height)


def _style_addcards(window, cfg):
    c = _colors(cfg)
    root = "QMainWindow#ctAddCards"
    window.setObjectName("ctAddCards")
    add_button = getattr(window, "addButton", None)
    if add_button is not None:
        # Hauptaktion in Akzentfarbe; Name vor dem Stylesheet setzen, sonst greift die Regel nicht
        add_button.setObjectName("ctPrimary")
    window.setStyleSheet(ui.stylesheet(c, root, font_size=None) + (BOLD.format(root=root, **c) if _bold(cfg, "editor") else ""))


def _style_preferences(dialog, cfg):
    c = _colors(cfg)
    root = "QDialog#ctPrefs"
    dialog.setObjectName("ctPrefs")
    dialog.setStyleSheet(ui.stylesheet(c, root, font_size=None) + CONTROLS.format(root=root, **c)
                         + (BOLD.format(root=root, **c) if _bold(cfg, "preferences") else ""))


def _style_addons(dialog, cfg):
    c = _colors(cfg)
    root = "QDialog#ctAddons"
    dialog.setObjectName("ctAddons")
    dialog.setStyleSheet(ui.stylesheet(c, root) + ADDON_LIST.format(root=root, **c)
                         + (BOLD.format(root=root, **c) if _bold(cfg, "addons") else ""))


def _apply(window, kind, cfg):
    try:
        enabled = window_mode(cfg, "editor" if kind == "addcards" else kind) != "original"
        if kind == "addcards":
            _style_addcards(window, cfg) if enabled else window.setStyleSheet("")
        elif kind == "preferences":
            _style_preferences(window, cfg) if enabled else window.setStyleSheet("")
        elif kind == "browser":
            _style_browser(window, cfg) if enabled else _unstyle_browser(window)
        else:
            _style_addons(window, cfg) if enabled else window.setStyleSheet("")
    except Exception as e:  # z.B. geänderte Anki-Interna: Fenster bleibt dann einfach im Standardlook
        from . import log
        log.record(f"window:{kind}", e)


def register(window, kind, cfg):
    _open[window] = kind
    _apply(window, kind, cfg)


def refresh_all(cfg):
    for window, kind in list(_open.items()):
        try:
            if window.isVisible():
                _apply(window, kind, cfg)
        except RuntimeError:  # Qt-Objekt schon gelöscht
            pass
