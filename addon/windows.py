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

ADDON_LIST = """
{root} QListWidget {{ background: {surface}; border: 1px solid {border}; border-radius: 12px; padding: 6px; outline: 0; }}
{root} QListWidget::item {{ padding: 7px 10px; border-radius: 8px; }}
{root} QListWidget::item:hover {{ background: {hover}; }}
{root} QListWidget::item:selected {{ background: {accent_soft}; }}
{root} QLabel {{ color: {sub}; }}
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
    return c


def _style_browser(browser, cfg):
    c = _colors(cfg)
    root = "QMainWindow#ctWindow"
    browser.setObjectName("ctWindow")
    # Schriftgröße nicht anfassen: die Kartenverwaltung hat eine eigene Schrifteinstellung
    browser.setStyleSheet(ui.stylesheet(c, root, font_size=None) + TABLE.format(root=root, **c))
    browser.sidebar.setStyleSheet(SIDEBAR.format(**c))
    browser.form.tableView.setShowGrid(False)
    if not getattr(browser, "_ct_popup", False):
        ui.modern_popup(browser.form.searchEdit)
        browser._ct_popup = True


def _unstyle_browser(browser):
    browser.setStyleSheet("")
    browser.sidebar._setup_style()  # Ankis eigenes Sidebar-Styling zurück
    browser.form.tableView.setShowGrid(True)


def _style_addcards(window, cfg):
    c = _colors(cfg)
    root = "QMainWindow#ctAddCards"
    window.setObjectName("ctAddCards")
    add_button = getattr(window, "addButton", None)
    if add_button is not None:
        # Hauptaktion in Akzentfarbe; Name vor dem Stylesheet setzen, sonst greift die Regel nicht
        add_button.setObjectName("ctPrimary")
    window.setStyleSheet(ui.stylesheet(c, root, font_size=None))


def _style_addons(dialog, cfg):
    c = _colors(cfg)
    root = "QDialog#ctAddons"
    dialog.setObjectName("ctAddons")
    dialog.setStyleSheet(ui.stylesheet(c, root) + ADDON_LIST.format(root=root, **c))


def _apply(window, kind, cfg):
    try:
        enabled = cfg["areas"].get("editor" if kind == "addcards" else kind, True)
        if kind == "addcards":
            _style_addcards(window, cfg) if enabled else window.setStyleSheet("")
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
