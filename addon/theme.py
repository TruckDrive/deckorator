# Baut das Theme-CSS aus der Konfiguration. Reines Python ohne aqt-Import,
# damit es auch für die Vorschau im Einstellungsfenster genutzt werden kann.
# Selektoren mit html:root, damit sie Ankis eigene :root/.night-mode-Regeln schlagen.
import colorsys
from urllib.parse import quote

# Presets setzen nur Farben + Hintergrundstil; alles andere bleibt wie eingestellt.
PRESETS = {
    "rose":     {"accent": "#db2777", "bg_light": "#f7f6f8", "bg_dark": "#151416", "background": "spotlight"},
    "ocean":    {"accent": "#0ea5e9", "bg_light": "#f5f7f9", "bg_dark": "#131517", "background": "waves"},
    "forest":   {"accent": "#16a34a", "bg_light": "#f5f7f5", "bg_dark": "#131514", "background": "dots"},
    "lavender": {"accent": "#8b5cf6", "bg_light": "#f7f6fa", "bg_dark": "#151418", "background": "grain"},
    "amber":    {"accent": "#f59e0b", "bg_light": "#f9f7f3", "bg_dark": "#161513", "background": "spotlight"},
    "coral":    {"accent": "#f43f5e", "bg_light": "#faf6f6", "bg_dark": "#171414", "background": "grid"},
    "teal":     {"accent": "#14b8a6", "bg_light": "#f4f8f7", "bg_dark": "#121615", "background": "waves"},
    "graphite": {"accent": "#71717a", "bg_light": "#f5f5f5", "bg_dark": "#121212", "background": "dots"},
}

IMAGE_EXTS = ("png", "jpg", "jpeg", "webp", "gif")


def _rgb(hex_color):
    h = hex_color.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    try:
        return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
    except ValueError:
        return (219, 39, 119)


def _hex(rgb):
    return "#%02x%02x%02x" % tuple(max(0, min(255, round(c))) for c in rgb)


def _mix(a, b, t):
    """t=0 -> a, t=1 -> b"""
    ra, rb = _rgb(a), _rgb(b)
    return _hex([ra[i] + (rb[i] - ra[i]) * t for i in range(3)])


def _rgba(hex_color, alpha):
    r, g, b = _rgb(hex_color)
    return f"rgba({r},{g},{b},{alpha:.3f})"


def _hue_shift(hex_color, degrees):
    r, g, b = (c / 255 for c in _rgb(hex_color))
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    r, g, b = colorsys.hls_to_rgb((h + degrees / 360) % 1, l, s)
    return _hex((r * 255, g * 255, b * 255))


def _palette(cfg, night):
    accent = cfg["accent"]
    op = cfg["glass_opacity"] / 100 if cfg["glass"] else 1.0
    shadow = cfg["shadow"] / 3  # 0..1
    if cfg.get("_light"):
        # Sparmodus: Flächen fast deckend, weil ohne Unschärfe sonst das Muster durchscheint
        op = max(op, .92)
    if night:
        canvas = cfg["bg_dark"]
        panel = _mix(canvas, "#ffffff", .07)
        return {
            "canvas": canvas, "fg": "#e7e7ea", "fg-subtle": "#9b9ba4",
            "glass": _rgba(panel, op), "glass-strong": _rgba(_mix(canvas, "#ffffff", .1), min(1, op + .2)),
            "glass-edge": "rgba(255,255,255,.07)", "border": "rgba(255,255,255,.10)",
            "accent": accent, "accent-text": _mix(accent, "#ffffff", .4),
            "accent-bg": _rgba(accent, .16),
            "primary-a": _mix(accent, "#ffffff", .1), "primary-b": _mix(accent, "#000000", .2),
            "button-bg": _rgba(_mix(canvas, "#ffffff", .12), max(.5, op)),
            "inset": _rgba(_mix(canvas, "#ffffff", .05), .8),
            "shadow": f"0 8px 32px rgba(0,0,0,{.4 * shadow:.3f}), 0 1px 2px rgba(0,0,0,{.3 * shadow:.3f})",
            "state-new": "#60a5fa", "state-learn": "#fbbf24", "state-review": "#34d399",
        }
    canvas = cfg["bg_light"]
    return {
        "canvas": canvas, "fg": "#1f2024", "fg-subtle": "#6b6d76",
        "glass": _rgba("#ffffff", op), "glass-strong": _rgba("#ffffff", min(1, op + .15)),
        "glass-edge": "rgba(255,255,255,.75)", "border": "rgba(110,110,125,.20)",
        "accent": accent, "accent-text": _mix(accent, "#000000", .18),
        "accent-bg": _rgba(accent, .11),
        "primary-a": _mix(accent, "#ffffff", .08), "primary-b": _mix(accent, "#000000", .18),
        "button-bg": _rgba("#ffffff", max(.6, op)),
        "inset": "rgba(255,255,255,.8)",
        "shadow": f"0 8px 32px rgba(20,20,30,{.09 * shadow:.3f}), 0 1px 2px rgba(20,20,30,{.07 * shadow:.3f})",
        "state-new": "#2563eb", "state-learn": "#d97706", "state-review": "#059669",
    }


def _vars_block(selector, p, cfg):
    btn_radius = {"pill": "999px", "rounded": f"{max(6, cfg['radius'] * .6):.0f}px", "square": "4px"}[cfg["button_shape"]]
    v = {
        # eigene Variablen
        "--ct-canvas": p["canvas"], "--ct-fg": p["fg"], "--ct-fg-subtle": p["fg-subtle"],
        "--ct-glass": p["glass"], "--ct-glass-strong": p["glass-strong"], "--ct-glass-edge": p["glass-edge"],
        "--ct-border": p["border"], "--ct-accent": p["accent"], "--ct-accent-text": p["accent-text"],
        "--ct-accent-bg": p["accent-bg"], "--ct-primary-a": p["primary-a"], "--ct-primary-b": p["primary-b"],
        "--ct-button-bg": p["button-bg"], "--ct-inset": p["inset"], "--ct-shadow": p["shadow"],
        "--ct-radius": f"{cfg['radius']}px", "--ct-btn-radius": btn_radius,
        "--ct-blur": f"{cfg['blur'] if cfg['glass'] and not cfg.get('_light') else 0}px",
        # Ankis Variablen, damit auch nicht explizit gestylte Elemente passen
        "--canvas": p["canvas"], "--canvas-elevated": p["glass"], "--canvas-inset": p["inset"],
        "--fg": p["fg"], "--fg-subtle": p["fg-subtle"], "--fg-link": p["accent-text"],
        "--border": p["border"], "--border-subtle": p["border"], "--border-focus": p["accent"],
        "--button-bg": p["button-bg"], "--button-primary-bg": p["accent"],
        "--button-primary-gradient-start": p["primary-a"], "--button-primary-gradient-end": p["primary-b"],
        "--accent-card": p["accent-text"], "--accent-note": p["accent-text"], "--shadow-focus": p["accent"],
        "--state-new": p["state-new"], "--state-learn": p["state-learn"], "--state-review": p["state-review"],
    }
    body = "\n".join(f"  {k}: {val};" for k, val in v.items())
    return f"{selector} {{\n{body}\n}}\n"


# Alte Stilnamen aus früheren Versionen
LEGACY_STYLES = {"aurora": "spotlight", "soft": "spotlight"}
BACKGROUND_STYLES = ("solid", "spotlight", "dots", "grid", "grain", "waves", "desktop", "image")

FADE_MASK = "radial-gradient(ellipse 85% 75% at 50% 38%, #000 30%, transparent 85%)"
EDGE_MASK = "linear-gradient(transparent, #000 14%, #000 86%, transparent)"


def _svg_url(svg):
    return 'url("data:image/svg+xml,' + quote(svg, safe="") + '")'


def _glow(accent, alpha):
    return f"radial-gradient(ellipse 75% 60% at 50% -12%, {_rgba(accent, alpha)}, transparent 70%) center / 100% 100% no-repeat"


def _background(cfg, night, bg_url):
    """(--ct-bg, --ct-pattern, --ct-mask). --ct-bg ist Licht bzw. Bild, --ct-pattern das Muster
    darüber. Topbar, Inhalt und Leisten sind getrennte Webansichten, deshalb laufen Muster
    zum oberen und unteren Rand hin aus, damit an den Übergängen keine Kante entsteht."""
    style = LEGACY_STYLES.get(cfg["background"], cfg["background"])
    k = cfg["bg_intensity"] / 100
    accent = cfg["accent"]
    canvas = cfg["bg_dark"] if night else cfg["bg_light"]
    ink = "#ffffff" if night else "#000000"
    light = (.34 if night else .22) * k
    if style in ("image", "desktop"):
        if not bg_url:
            return "none", "none", "none"
        overlay = _rgba(canvas, max(0.0, 1 - k * .9))
        return (f"linear-gradient({overlay}, {overlay}) center / cover no-repeat, "
                f"url('{bg_url}') center / cover no-repeat"), "none", "none"
    if style == "spotlight":
        bottom = f"radial-gradient(ellipse 60% 45% at 50% 115%, {_rgba(_hue_shift(accent, 30), light * .45)}, transparent 70%) center / 100% 100% no-repeat"
        return f"{_glow(accent, light)}, {bottom}", "none", "none"
    if style == "dots":
        dot = _rgba(_mix(accent, ink, .5), (.34 if night else .26) * k)
        return _glow(accent, light * .6), f"radial-gradient(circle, {dot} 1.2px, transparent 1.8px) 0 0 / 22px 22px", FADE_MASK
    if style == "grid":
        line = _rgba(_mix(accent, ink, .55), (.13 if night else .10) * k)
        pattern = (f"linear-gradient(to right, {line} 1px, transparent 1px) 0 0 / 36px 36px, "
                   f"linear-gradient(to bottom, {line} 1px, transparent 1px) 0 0 / 36px 36px")
        return _glow(accent, light * .6), pattern, FADE_MASK
    if style == "grain":
        v = 1 if night else 0
        svg = ("<svg xmlns='http://www.w3.org/2000/svg' width='180' height='180'><filter id='n'>"
               "<feTurbulence type='fractalNoise' baseFrequency='.8' numOctaves='3' stitchTiles='stitch'/>"
               f"<feColorMatrix values='0 0 0 0 {v} 0 0 0 0 {v} 0 0 0 0 {v} 0 0 0 {(.16 if night else .11) * k:.3f} 0'/>"
               "</filter><rect width='100%' height='100%' filter='url(#n)'/></svg>")
        return _glow(accent, light * .85), f"{_svg_url(svg)} 0 0 / 180px 180px", EDGE_MASK
    if style == "waves":
        a = (.16 if night else .12) * k
        c2 = _hue_shift(accent, 25)
        svg = ("<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 1440 320' preserveAspectRatio='none'>"
               f"<path fill='{c2}' fill-opacity='{a:.3f}' d='M0,190 C240,120 480,260 720,210 C960,160 1200,90 1440,150 L1440,320 L0,320 Z'/>"
               f"<path fill='{accent}' fill-opacity='{a * 1.2:.3f}' d='M0,240 C320,190 560,300 880,250 C1120,215 1290,215 1440,235 L1440,320 L0,320 Z'/>"
               f"<path fill='{accent}' fill-opacity='{a * 1.6:.3f}' d='M0,285 C360,250 720,318 1080,282 C1260,265 1380,272 1440,282 L1440,320 L0,320 Z'/>"
               "</svg>")
        return _glow(accent, light * .7), f"{_svg_url(svg)} center bottom / 100% 36% no-repeat", "none"
    return "none", "none", "none"


BASE_CSS = """
html body:not(.flat) {
  background-color: var(--ct-canvas) !important; background-image: none !important;
  color: var(--ct-fg); -webkit-font-smoothing: antialiased;
}
html body a, html body a:visited { color: var(--ct-accent-text); text-decoration: none; }

::-webkit-scrollbar { width: 10px; height: 10px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: var(--ct-border); border-radius: 999px;
  border: 3px solid transparent; background-clip: content-box; }
::-webkit-scrollbar-thumb:hover { background-color: var(--ct-fg-subtle); }

/* Topbar */
html body .header { border-bottom: none !important; grid-template-columns: 1fr auto 1fr !important; }
html body .hitem {
  color: var(--ct-fg) !important; border-radius: var(--ct-btn-radius) !important; padding: 5px 14px !important;
  text-decoration: none !important; border: none !important; background: transparent !important; font-weight: 500;
}
html body .hitem:hover { color: var(--ct-accent-text) !important; background: var(--ct-accent-bg) !important; }

/* Panels als Glaskarten */
html body #outer, html body .overview, html body #studiedToday {
  background: var(--ct-glass); backdrop-filter: blur(var(--ct-blur)) saturate(150%);
  border: 1px solid var(--ct-glass-edge); border-radius: var(--ct-radius); padding: 16px;
  box-shadow: var(--ct-shadow);
}

/* "Heute X Karten in Y Min. gelernt": schlanke Kapsel statt breitem Balken */
html body #studiedToday { display: table; width: auto !important; margin: 18px auto 0 !important;
  padding: 8px 20px !important; border-radius: var(--ct-btn-radius) !important;
  color: var(--ct-fg-subtle); font-size: .92em; font-variant-numeric: tabular-nums; }

/* Deckliste */
html body table { border-collapse: separate; border-spacing: 0 2px; }
html body tr.deck td:first-child { border-radius: calc(var(--ct-radius) * .6) 0 0 calc(var(--ct-radius) * .6); }
html body tr.deck td:last-child { border-radius: 0 calc(var(--ct-radius) * .6) calc(var(--ct-radius) * .6) 0; }
html body tr.deck:hover td { background: var(--ct-accent-bg); }
html body tr.current td { background: var(--ct-accent-bg) !important; }
html body tr.current a.deck { font-weight: 600; color: var(--ct-accent-text) !important; }
html body a.deck { color: var(--ct-fg) !important; }
html body .collapse { opacity: .55; }
html body .gears { opacity: .45; border-radius: 999px; }
html body tr.deck:hover .gears { opacity: .9; }
html body th { color: var(--ct-fg-subtle); font-weight: 500; font-size: .9em; }

/* Buttons */
html body button, html body .btn, html body input[type=button], html body input[type=submit] {
  border-radius: var(--ct-btn-radius) !important; padding: 7px 18px !important;
  background: var(--ct-button-bg) !important; color: var(--ct-fg) !important;
  border: 1px solid var(--ct-border) !important; backdrop-filter: blur(var(--ct-blur));
  box-shadow: 0 1px 2px rgba(0,0,0,.05); font-weight: 500; cursor: pointer;
}
html body button:hover, html body .btn:hover { border-color: var(--ct-accent) !important; }
html body button:focus-visible { outline: 2px solid var(--ct-accent); outline-offset: 2px; }

/* Primär-Buttons: "Jetzt lernen", "Antwort zeigen" */
html body #study, html body #ansbut, html body button.primary {
  background: linear-gradient(135deg, var(--ct-primary-a), var(--ct-primary-b)) !important;
  color: #fff !important; border: none !important; padding: 9px 26px !important; font-weight: 600;
  box-shadow: 0 6px 18px color-mix(in srgb, var(--ct-accent) 30%, transparent) !important;
}
html body #study:hover, html body #ansbut:hover {
  box-shadow: 0 10px 26px color-mix(in srgb, var(--ct-accent) 42%, transparent) !important; }
html body button[data-ease] { min-width: 84px; padding: 7px 16px !important; }
html body .nobold { color: var(--ct-fg-subtle); }

/* Eingabefelder */
html body input[type=text], html body input[type=search], html body select, html body textarea {
  border-radius: calc(var(--ct-radius) * .7); border: 1px solid var(--ct-border); background: var(--ct-inset);
  color: var(--ct-fg); padding: 6px 10px;
}
html body input:focus, html body select:focus, html body textarea:focus {
  outline: none; border-color: var(--ct-accent); box-shadow: 0 0 0 3px var(--ct-accent-bg);
}
"""

TOOLBAR_FLOATING = """
html body .toolbar {
  background: var(--ct-glass) !important; backdrop-filter: blur(var(--ct-blur)) saturate(150%);
  border: 1px solid var(--ct-glass-edge); border-radius: var(--ct-btn-radius) !important;
  box-shadow: var(--ct-shadow); padding: 3px 6px !important; margin: 6px auto !important;
  display: inline-flex; gap: 2px; white-space: nowrap;
}
"""

TOOLBAR_FLAT = """
html body .toolbar { background: transparent !important; border: none !important; box-shadow: none !important;
  display: inline-flex; gap: 2px; white-space: nowrap; margin: 4px auto !important; }
"""

BADGES = """
html body .new-count, html body .learn-count, html body .review-count {
  display: inline-block; min-width: 1.6em; padding: 1px 8px; border-radius: 999px;
  font-weight: 600; font-size: .9em; text-align: center;
}
html body .new-count { background: color-mix(in srgb, var(--state-new) 14%, transparent); }
html body .learn-count { background: color-mix(in srgb, var(--state-learn) 14%, transparent); }
html body .review-count { background: color-mix(in srgb, var(--state-review) 14%, transparent); }
html body .zero-count { opacity: .35; background: none !important; }
"""

COUNT_COLORS = """
html body a.new-count { color: var(--state-new) !important; }
html body a.learn-count { color: var(--state-learn) !important; }
html body a.review-count { color: var(--state-review) !important; }
html body a.zero-count { color: var(--ct-fg-subtle) !important; }
"""

EASE_COLORS = {"1": "#ef4444", "2": "#f59e0b", "3": "#10b981", "4": "#3b82f6"}

ANIMATIONS = """
html body .hitem, html body tr.deck td, html body input, html body select, html body textarea {
  transition: background .18s ease, color .18s ease, border-color .15s, box-shadow .15s; }
html body button, html body .btn {
  transition: transform .15s ease, box-shadow .2s ease, background .2s ease, border-color .2s ease; }
html body #study:hover, html body #ansbut:hover { transform: translateY(-1px); }
html body button:active { transform: scale(.98); }
html body .gears { transition: opacity .15s, transform .3s; }
html body tr.deck:hover .gears { transform: rotate(45deg); }
"""

NO_ANIMATIONS = """
html body *, html body *::before, html body *::after { transition: none !important; animation: none !important; }
"""

# Ankis eigene "Bewegung reduzieren"-Einstellung und die des Systems respektieren
REDUCED_MOTION = """
html body.reduce-motion *, html body.reduce-motion *::before, html body.reduce-motion *::after {
  transition: none !important; animation: none !important; }
html body.reduce-motion button, html body.reduce-motion .gears { transform: none !important; }
@media (prefers-reduced-motion: reduce) {
  html body *, html body *::before, html body *::after { transition: none !important; }
  html body button, html body .gears { transform: none !important; }
}
"""

# Topbar und untere Leisten: ruhige Theme-Fläche ohne schwebende Glaskarte
BAR_CALM = """
html body #outer { background: transparent !important; border: none !important; box-shadow: none !important;
  backdrop-filter: none !important; padding: 0 !important; border-radius: 0 !important; }
"""

# Karte: nur Hintergrund, alles andere bleibt Sache des Notiztyps
CARD_CSS = """
html body { background-color: var(--ct-canvas) !important; background-image: none !important; }
"""

# Verlauf/Bild als fixierte Ebene hinter dem Inhalt. Anders als background-attachment: fixed
# muss Chromium sie beim Scrollen nicht neu malen.
BG_LAYER = """
html body:not(.flat)::before, html body:not(.flat)::after {
  content: ""; position: fixed; inset: 0; z-index: -1; pointer-events: none;
}
html body:not(.flat)::before { background: var(--ct-bg); }
html body:not(.flat)::after { background: var(--ct-pattern); -webkit-mask-image: var(--ct-mask); mask-image: var(--ct-mask); }
"""

# Restzähler über "Antwort zeigen" (Neu + Lernen + Wiederholen) als gut lesbare Chips.
# Ohne transform: verschobene Ebenen rendert Chromium unscharf.
REVIEW_COUNTS = """
html body #middle td[align=center], html body #middle td.stat2 { padding-top: 24px !important; }
html body #middle .stattxt, html body #middle .nobold {
  transform: none !important; top: auto !important; bottom: calc(100%% + 5px) !important;
  left: -80px !important; right: -80px !important; text-align: center; line-height: 1;
}
html body #middle .nobold { font-size: %(small)spx !important; font-weight: 500; }
html body #middle .stattxt { font-size: 0 !important; display: flex !important; justify-content: center; gap: 6px; }
html body #middle .stattxt > span {
  font-size: %(count)spx; font-weight: 650; padding: 3px 9px; border-radius: 999px; min-width: 0;
  font-variant-numeric: tabular-nums;
}
html body #middle .stattxt u { text-decoration: none; }
html body #middle .stattxt span:has(u) { box-shadow: inset 0 0 0 1.5px currentColor; }
"""

# Review Heatmap (Add-on 1771074083) in Theme-Farben: Glaskarte, runde Zellen,
# Zellfarben aus der Akzentfarbe, Kennzahlen als ruhige Zeile darunter.
HEATMAP_CSS = """
html body .rh-container { display: table; margin: 16px auto 0; padding: 14px 18px 12px;
  background: var(--ct-glass); backdrop-filter: blur(var(--ct-blur)) saturate(150%%);
  border: 1px solid var(--ct-glass-edge); border-radius: var(--ct-radius); box-shadow: var(--ct-shadow); }
html body .rh-container .cal-heatmap-container rect { rx: %(cell_r)spx; ry: %(cell_r)spx; }
/* Heatmap schaltet die Kantenglättung ab (crispedges); bei runden Zellen wirkt das pixelig */
html body .rh-container .cal-heatmap-container .graph,
html body .rh-container .cal-heatmap-container rect { shape-rendering: geometricPrecision !important; }
html body .rh-container .cal-heatmap-container .graph-rect { fill: color-mix(in srgb, var(--ct-fg) 7%%, transparent) !important; }
html body .rh-container .cal-heatmap-container .graph-label,
html body .rh-container .cal-heatmap-container .day-name-text { fill: var(--ct-fg-subtle) !important; }
html body .rh-container .cal-heatmap-container rect.highlight-now { stroke: var(--ct-fg) !important; stroke-width: 1.5px; }
html body .rh-container .cal-heatmap-container rect.highlight { stroke: var(--ct-accent) !important; }
html body .rh-container .cal-heatmap-container .graph-subdomain-group rect:hover { stroke: var(--ct-fg) !important; }
html body .rh-container .hm-btn { background: var(--ct-button-bg) !important; border: 1px solid var(--ct-border);
  border-radius: var(--ct-btn-radius) !important; padding: 3px 10px !important; }
html body .rh-container .hm-btn:hover { background: var(--ct-accent-bg) !important; border-color: var(--ct-accent); }
html:root.night-mode body .rh-container .hm-btn img { filter: invert(1); opacity: .75; }
html body .rh-container .streak { display: flex; flex-wrap: wrap; justify-content: center; gap: 4px 6px;
  margin-top: 10px; font-size: .9em; }
html body .rh-container .streak-info { margin-left: 10px; color: var(--ct-fg-subtle); }
html body .rh-container .sstats { font-weight: 650; font-variant-numeric: tabular-nums; }
"""

# Topbar beim Lernen ("flat"): gleiche Fläche wie die Karte. Bei "note" fehlt die Regel,
# dann übernimmt Anki selbst den Kartenhintergrund in die Topbar.
FLAT_TOOLBAR = """
html body.flat { background-color: var(--ct-canvas) !important; background-image: none !important; }
"""

REVIEW_COUNT_BADGES = """
html body #middle .stattxt .new-count { background: color-mix(in srgb, var(--state-new) 16%, transparent); }
html body #middle .stattxt .learn-count { background: color-mix(in srgb, var(--state-learn) 16%, transparent); }
html body #middle .stattxt .review-count { background: color-mix(in srgb, var(--state-review) 16%, transparent); }
"""

# Sparmodus: keine Hintergrund-Unschärfe (teuerster Effekt) und kleinere Schatten
LIGHT_MODE = """
html body *, html body *::before, html body *::after { backdrop-filter: none !important; }
html body #outer, html body .overview, html body #studiedToday, html body .rh-container, html body .toolbar {
  box-shadow: 0 1px 3px rgba(0,0,0,.12) !important; }
"""

# Andere Fenster (Editor, Kartenvorschau, ...): nur Farben, keine Formen. Ankis eigene
# Oberflächen hängen an diesen Variablen; Abstände und Buttons bleiben unangetastet.
COLORS_ONLY = """
html body { background-color: var(--ct-canvas) !important; }
"""

# "Heute X Karten gelernt" als auffällige Kachel; .ct-num setzt der Hook in __init__.py
TODAY_HIGHLIGHT = """
html body #studiedToday {
  background: linear-gradient(135deg, color-mix(in srgb, var(--ct-accent) 24%, var(--ct-glass)),
    color-mix(in srgb, var(--ct-accent) 7%, var(--ct-glass))) !important;
  border: 1px solid color-mix(in srgb, var(--ct-accent) 45%, transparent) !important;
  box-shadow: 0 10px 30px color-mix(in srgb, var(--ct-accent) 22%, transparent) !important;
  color: var(--ct-fg) !important; font-size: 1.02em !important; padding: 12px 26px !important;
  border-radius: calc(var(--ct-radius) * 1.1) !important;
}
html body #studiedToday .ct-num { font-weight: 750; font-size: 1.35em; color: var(--ct-accent-text);
  font-variant-numeric: tabular-nums; margin: 0 .06em; vertical-align: -.04em; }
html body #studiedToday .ct-num:first-child { font-size: 1.9em; vertical-align: -.12em; }
html body #studiedToday .ct-num:nth-child(n+3) { font-size: 1.05em; font-weight: 600; color: var(--ct-fg-subtle);
  vertical-align: 0; }
"""

# Ankis Svelte-Seiten (Editor, Statistik, Stapeloptionen): sie hängen an Ankis CSS-Variablen,
# die _vars_block schon setzt. Hier nur Hintergrund und wenige gezielte Details.
PAGES_CSS = """
html body { background-color: var(--ct-canvas) !important; }
.editor-field { box-shadow: none !important; border-color: var(--ct-border) !important; }
.editor-field:focus-within { outline: 2px solid var(--ct-accent) !important; outline-offset: -1px; }
.field-container, .label-container { background: var(--ct-canvas) !important; }
.editor-toolbar { border-bottom-color: var(--ct-border) !important; }
.range-box { background: var(--ct-canvas) !important; border-bottom-color: var(--ct-border) !important; }
"""

# Kräftiger Fensterstil auf Statistik/Stapeloptionen: Spotlight und Überschriften in Akzentfarbe
PAGES_BOLD = """
html body { background: radial-gradient(ellipse 75% 55% at 50% -12%, var(--ct-glow), transparent 70%) fixed,
  var(--ct-canvas) !important; }
h1 { color: var(--ct-accent-text) !important; }
.range-box { background: var(--ct-glass) !important; backdrop-filter: blur(var(--ct-blur)); }
"""

# Kräftiger Stil im Editor: durchsichtiger Hintergrund (das Fenster dahinter trägt den Spotlight),
# Felder als Glaskarten, Feldnamen und Schlagwörter in Akzentfarbe
EDITOR_BOLD = """
html, html body { background: transparent !important; }
.field-container, .label-container, .editing-area { background: transparent !important; }
.editor-field { background: var(--ct-glass) !important; border: 1px solid var(--ct-glass-edge) !important;
  border-radius: calc(var(--ct-radius) * .8) !important; }
.label-container { color: var(--ct-accent-text) !important; font-weight: 600; }
.fields { grid-gap: 12px !important; }
.tag { background: var(--ct-accent-bg) !important; color: var(--ct-accent-text) !important;
  border-radius: 999px !important; --border-color: transparent; }
"""

SCOPES = ("main", "bar", "card", "colors", "pages", "editor")

COMPACT = """
html body #outer, html body .overview, html body #studiedToday { padding: 8px !important; }
html body button, html body .btn { padding: 4px 12px !important; }
html body #study, html body #ansbut { padding: 6px 18px !important; }
html body .hitem { padding: 3px 10px !important; }
html body tr.deck td { padding-top: 1px !important; padding-bottom: 1px !important; }
"""


def build_css_text(cfg, scope="main", base_px=None, bg_url=None):
    """CSS für einen Bereich: "main" (Deckliste, Übersicht), "bar" (Topbar und untere
    Leisten) oder "card" (Kartenansicht). Leerer String = nichts einfügen."""
    review = cfg["review_background"]
    if scope == "card" and review == "note":
        return ""
    effects = scope == "main" or (scope == "card" and review == "full")
    parts = [
        _vars_block("html:root:not(.night-mode)", _palette(cfg, False), cfg),
        _vars_block("html:root.night-mode", _palette(cfg, True), cfg),
    ]
    if effects:
        for sel, night in (("html:root:not(.night-mode)", False), ("html:root.night-mode", True)):
            bg, pattern, mask = _background(cfg, night, bg_url)
            parts.append(f"{sel} {{ --ct-bg: {bg}; --ct-pattern: {pattern}; --ct-mask: {mask}; }}\n")
    if scope in ("pages", "editor"):
        r = cfg["radius"]
        radii = (f"--border-radius: {max(4, round(r * .45))}px; --border-radius-medium: {max(6, r)}px; "
                 f"--border-radius-large: {max(8, round(r * 1.3))}px;")
        parts.append(f"html:root:not(.night-mode), html:root.night-mode {{ {radii} }}\n")
        parts.append(PAGES_CSS)
        if cfg.get("window_style", "bold") == "bold":
            glow = _rgba(cfg["accent"], .22)
            parts.append(f"html:root {{ --ct-glow: {glow}; }}\n")
            parts.append(EDITOR_BOLD if scope == "editor" else PAGES_BOLD)
        return "".join(parts)
    if scope == "colors":
        parts.append(COLORS_ONLY)
        return "".join(parts)
    if scope == "card":
        parts.append(CARD_CSS)
        if effects:
            parts.append(BG_LAYER)
        return "".join(parts)
    parts += [
        BASE_CSS,
        COUNT_COLORS,
        TOOLBAR_FLOATING if cfg["toolbar_style"] == "floating" else TOOLBAR_FLAT,
    ]
    if effects:
        parts.append(BG_LAYER)
    if scope == "bar":
        parts.append(BAR_CALM)
        if review != "note":
            parts.append(FLAT_TOOLBAR)
        px = (base_px or 14) * cfg["font_scale"] / 100
        parts.append(REVIEW_COUNTS % {"count": f"{px * .92:.1f}", "small": f"{px * .82:.1f}"})
        if cfg["count_badges"]:
            parts.append(REVIEW_COUNT_BADGES)
    if scope == "main" and cfg.get("highlight_today", True):
        parts.append(TODAY_HIGHLIGHT)
    # Heatmap: "theme" = Karte + runde Zellen + Farben, "colors" = nur Farben, "original" = nichts
    if scope == "main" and cfg["heatmap_style"] == "theme":
        parts.append(HEATMAP_CSS % {"cell_r": f"{min(3.5, cfg['radius'] / 5):.1f}"})
    if scope == "main" and cfg["heatmap_style"] in ("theme", "colors"):
        parts.append(_heatmap_colors(cfg))
    if cfg["font_family"]:
        parts.append(f'html body, html body button, html body input, html body select {{ font-family: "{cfg["font_family"]}", sans-serif !important; }}\n')
    if cfg["font_scale"] != 100 and base_px:
        parts.append(f"html body {{ font-size: {base_px * cfg['font_scale'] / 100:.1f}px !important; }}\n")
    if cfg["count_badges"]:
        parts.append(BADGES)
    if cfg["colored_answers"]:
        for ease, col in EASE_COLORS.items():
            parts.append(
                f'html body button[data-ease="{ease}"] {{ background: color-mix(in srgb, {col} 14%, var(--ct-button-bg)) !important; }}\n'
                f'html body button[data-ease="{ease}"]:hover {{ border-color: {col} !important; '
                f'box-shadow: 0 8px 20px {_rgba(col, .25)} !important; }}\n')
    parts.append(ANIMATIONS if cfg["animations"] else NO_ANIMATIONS)
    if cfg.get("_light"):
        parts.append(LIGHT_MODE)
    parts.append(REDUCED_MOTION)
    if cfg["compact"]:
        parts.append(COMPACT)
    if cfg["custom_css"].strip():
        parts.append("/* Eigenes CSS */\n" + cfg["custom_css"] + "\n")
    return "".join(parts)


def _heatmap_colors(cfg):
    """q11–q20 = Wiederholungen (hell -> kräftig), q1–q10 = fällige Karten in der Zukunft (grau)."""
    rules = []
    for i in range(10):
        past = 22 + i * 8.6
        rules.append(f"html body .rh-container .cal-heatmap-container .q{11 + i} {{ fill: color-mix(in srgb, var(--ct-accent) {past:.0f}%, var(--ct-canvas)) !important; }}\n"
                     f"html body .rh-container .rh-col{11 + i} {{ color: color-mix(in srgb, var(--ct-accent-text) {50 + i * 5.5:.0f}%, var(--ct-fg-subtle)) !important; }}\n"
                     f"html body .rh-container .cal-heatmap-container .q{10 - i} {{ fill: color-mix(in srgb, var(--ct-fg) {14 + i * 4:.0f}%, var(--ct-canvas)) !important; }}\n")
    return "".join(rules)


def build_css(cfg, scope="main", base_px=None, bg_url=None):
    text = build_css_text(cfg, scope, base_px, bg_url)
    return f'<style id="deckorator">\n{text}</style>\n' if text else ""


class PreviewContext:
    """Webansichten der Vorschau; der Hook lässt sie aus, die Vorschau setzt ihr CSS selbst."""
