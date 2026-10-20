# Modernes, anpassbares Theme für Ankis Web-Ansichten (Topbar, Deckliste,
# Übersicht, Lernen). Nur CSS, keine Datenänderung. Einstellungen über
# Extras → Theme-Einstellungen… oder den Konfigurations-Button im Add-on-Manager.
import json
import os
import re
import sys
import weakref

from aqt import gui_hooks, mw
from aqt.deckbrowser import DeckBrowser, DeckBrowserBottomBar
from aqt.overview import Overview, OverviewBottomBar
from aqt.qt import QAction, QTimer
from aqt.reviewer import Reviewer, ReviewerBottomBar
from aqt.theme import theme_manager
from aqt.toolbar import BottomToolbar, TopToolbar

from . import desktop, log, system, theme, windows

VERSION = "1.1.0"
MODULE = __name__
ADDON_FOLDER = MODULE.split(".")[0]
USER_DIR = os.path.join(os.path.dirname(__file__), "user_files")
mw.addonManager.setWebExports(MODULE, r"user_files/.*\.(png|jpe?g|webp|gif)")

MAIN_CONTEXTS = (DeckBrowser, Overview)
BAR_CONTEXTS = (TopToolbar, BottomToolbar, DeckBrowserBottomBar, OverviewBottomBar)


def defaults():
    return mw.addonManager.addonConfigDefaults(MODULE) or {}


def load_config():
    cfg = defaults()
    user = mw.addonManager.getConfig(MODULE) or {}
    cfg.update(user)
    cfg["areas"] = {**defaults().get("areas", {}), **user.get("areas", {})}
    cfg["background"] = theme.LEGACY_STYLES.get(cfg["background"], cfg["background"])
    return cfg


def bg_url(cfg):
    """URL des Hintergrundbilds; ?v= sorgt dafür, dass ein neues Bild mit gleichem
    Dateinamen nicht aus dem Cache kommt."""
    name = cfg.get("desktop_image") if cfg["background"] == "desktop" else cfg["bg_image"]
    if not name:
        return None
    try:
        version = int(os.path.getmtime(os.path.join(USER_DIR, name)))
    except OSError:
        return None
    return f"/_addons/{ADDON_FOLDER}/user_files/{name}?v={version}"


def base_font_px():
    return mw.web.font().pointSizeF() * mw.web.logicalDpiX() / 72


_hardware = None


def hardware():
    global _hardware
    if _hardware is None:
        _hardware = system.hardware_report(mw)
    return _hardware


def effective(cfg):
    """Konfiguration plus abgeleitete Werte, mit denen das CSS gebaut wird."""
    mode = cfg.get("performance", "auto")
    return {**cfg, "_light": mode == "light" or (mode == "auto" and hardware()["weak"])}


_cache = None  # (cfg, {scope: css}), wird bei jeder Speicherung verworfen


def _cached():
    global _cache
    if _cache is None:
        cfg = effective(load_config())
        px = base_font_px()
        _cache = (cfg, {s: theme.build_css(cfg, s, px, bg_url(cfg)) for s in theme.SCOPES})
    return _cache


def _area(context):
    """(Schalter in areas, CSS-Bereich) für eine Webansicht; Schalter None = immer an"""
    if isinstance(context, MAIN_CONTEXTS):
        return "main", "main"
    if isinstance(context, BAR_CONTEXTS):
        return "main", "bar"
    if isinstance(context, ReviewerBottomBar):
        return "review_bar", "bar"
    if isinstance(context, Reviewer):
        return None, "card"
    return "other", "colors"


def _inject(web_content, context):
    if isinstance(context, theme.PreviewContext):
        return
    try:
        cfg, css = _cached()
    except Exception as e:
        # lieber ungestyltes Anki als eine Fehlermeldung bei jedem Seitenwechsel
        log.record("css", e)
        return
    switch, scope = _area(context)
    if switch is None or cfg["areas"].get(switch):
        web_content.head += css[scope]


# Svelte-Seiten bekommen ihr CSS per JavaScript, sobald Anki ihr eigenes Styling geladen hat
PAGE_AREAS = {"editor": "editor", "deck stats": "stats", "deck options": "deck_options"}
PAGE_JS = """(function (css) {
  var s = document.getElementById("deckorator");
  if (!s) { s = document.createElement("style"); s.id = "deckorator"; document.head.appendChild(s); }
  s.textContent = css;
})(%s);"""
_pages = weakref.WeakSet()


def _style_page(web):
    try:
        cfg, _css = _cached()
        area = PAGE_AREAS.get(web.kind.value, "other")
        text = _page_css() if cfg["areas"].get(area, False) else ""
        web.eval(PAGE_JS % json.dumps(text))
    except Exception as e:
        log.record("page", e)


_page_css_cache = None


def _page_css():
    global _page_css_cache
    if _page_css_cache is None:
        _page_css_cache = theme.build_css_text(_cached()[0], "pages")
    return _page_css_cache


def _on_page_styled(web):
    _pages.add(web)
    _style_page(web)


TODAY_RE = re.compile(r'(<div id="?studiedToday"?[^>]*>\s*<span>)(.*?)(</span>)', re.S)


def _highlight_today(deck_browser, content):
    """Zahlen in "Heute X Karten in Y Min. gelernt" hervorheben. Sucht nur Ziffern und
    funktioniert so in jeder Sprache."""
    # Spans immer setzen (harmlos ohne CSS), damit die Vorschau den Schalter live zeigen kann
    if not _cached()[0]["areas"].get("main"):
        return
    number = lambda m: f'<span class="ct-num">{m.group(0)}</span>'
    content.stats = TODAY_RE.sub(lambda m: m.group(1) + re.sub(r"\d+(?:[.,]\d+)?", number, m.group(2)) + m.group(3),
                                 content.stats, count=1)


def _refresh_ui():
    global _cache, _page_css_cache
    _cache = None
    _page_css_cache = None
    for web in list(_pages):
        _style_page(web)
    try:
        mw.toolbar.draw()
        if mw.state == "deckBrowser":
            mw.deckBrowser.refresh()
        elif mw.state == "overview":
            mw.overview.refresh()
        elif mw.state == "review":
            mw.reviewer.show()
    except Exception:
        # Ansicht wird spätestens beim nächsten Wechsel neu gezeichnet
        pass


def save_config(cfg):
    mw.addonManager.writeConfig(MODULE, {k: v for k, v in cfg.items() if not k.startswith("_")})
    _refresh_ui()
    windows.refresh_all(load_config())


def _on_theme_change():
    # nach Ankis eigenen Handlern, die z.B. das Sidebar-Styling zurücksetzen
    QTimer.singleShot(0, lambda: windows.refresh_all(load_config()))


def sync_desktop(cfg, force=False):
    """Akzentfarbe/Desktop-Hintergrund auffrischen; gibt die Änderungen zurück."""
    if force:
        cfg = {**cfg, "desktop_sig": ""}
    try:
        return desktop.sync(cfg, USER_DIR, theme_manager.night_mode)
    except Exception as e:
        log.record("desktop", e)
        return {}


def _sync_on_start():
    cfg = load_config()
    changes = sync_desktop(cfg)
    if changes:
        cfg.update(changes)
        if "accent" in changes:
            cfg["preset"] = ""
        save_config(cfg)


def open_settings():
    from .dialog import ThemeDialog
    ThemeDialog(sys.modules[__name__]).exec()


def _setup_menu():
    from .dialog import t
    action = QAction(t("title") + "…", mw)
    action.triggered.connect(open_settings)
    mw.form.menuTools.addAction(action)


gui_hooks.webview_will_set_content.append(_inject)
gui_hooks.deck_browser_will_render_content.append(_highlight_today)
gui_hooks.browser_will_show.append(lambda browser: windows.register(browser, "browser", load_config()))
gui_hooks.add_cards_did_init.append(lambda addcards: windows.register(addcards, "addcards", load_config()))
gui_hooks.addons_dialog_will_show.append(lambda dialog: windows.register(dialog, "addons", load_config()))
gui_hooks.theme_did_change.append(_on_theme_change)
gui_hooks.webview_did_inject_style_into_page.append(_on_page_styled)
# Der Editor löst den Hook oben (Anki 26.09) nicht zuverlässig aus; er meldet sich aber,
# sobald eine Notiz geladen ist. Das CSS-Einfügen ist idempotent, mehrfach schadet nicht.
gui_hooks.editor_did_load_note.append(lambda editor: _on_page_styled(editor.web))
gui_hooks.profile_did_open.append(_sync_on_start)
gui_hooks.main_window_did_init.append(_setup_menu)
# Bei Änderung über Ankis JSON-Editor ebenfalls neu zeichnen
mw.addonManager.setConfigUpdatedAction(MODULE, lambda _cfg: _refresh_ui())
mw.addonManager.setConfigAction(MODULE, open_settings)
