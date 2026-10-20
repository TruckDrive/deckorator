# Eigene, gezeichnete Wallpaper als SVG: rechtlich unbedenklich, gestochen scharf in jeder
# Größe und automatisch in der Akzentfarbe des Themes (Hell- und Dunkelvariante).
# Reines Python ohne aqt-Import; Zufall immer mit festem Seed, damit sich nichts verändert.
import math
import random

from .theme import _hue_shift, _mix

W, H = 1600, 1000

# Name -> (Zeichenfunktion, vertikaler Fokus 0..1 für den schmalen Banner-Ausschnitt)
ART = {}


def art(name, focus):
    def deco(fn):
        ART[name] = (fn, focus)
        return fn
    return deco


def _palette(accent, night):
    base = "#0e0e14" if night else "#f7f6fa"
    return {
        "base": base,
        "sky_top": _mix(base, accent, .38 if night else .30),
        "sky_mid": _mix(base, accent, .18 if night else .14),
        "a": accent,
        "b": _hue_shift(accent, 32),
        "c": _hue_shift(accent, -38),
        "ink": "#ffffff" if night else "#1a1a24",
        "light": _mix(accent, "#ffffff", .55),
        "deep": _mix(accent, "#000000", .55 if night else .25),
    }


def _ridge(rng, y, amp, steps=9, jitter=.35):
    """Weiche Bergkante als Pfad von links nach rechts (Catmull-Rom-ähnlich über Bezier)."""
    xs = [i * W / steps for i in range(steps + 1)]
    ys = [y + rng.uniform(-amp, amp) * (1 if i % 2 else jitter) for i in range(steps + 1)]
    d = f"M0,{H} L0,{ys[0]:.0f}"
    for i in range(steps):
        x0, y0, x1, y1 = xs[i], ys[i], xs[i + 1], ys[i + 1]
        cx = (x0 + x1) / 2
        d += f" C{cx:.0f},{y0:.0f} {cx:.0f},{y1:.0f} {x1:.0f},{y1:.0f}"
    return d + f" L{W},{H} Z"


def _stars(rng, n, top, bottom, color, max_r=1.6):
    out = []
    for _ in range(n):
        x, y = rng.uniform(0, W), rng.uniform(top, bottom)
        r = rng.uniform(.4, max_r)
        out.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{r:.2f}" fill="{color}" opacity="{rng.uniform(.35, .95):.2f}"/>')
    return "".join(out)


def _svg(body, defs=""):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" preserveAspectRatio="xMidYMid slice">'
            f"<defs>{defs}</defs>{body}</svg>")


def _sky(p, id_="sky"):
    return (f'<linearGradient id="{id_}" x1="0" y1="0" x2="0" y2="1">'
            f'<stop offset="0" stop-color="{p["sky_top"]}"/><stop offset=".55" stop-color="{p["sky_mid"]}"/>'
            f'<stop offset="1" stop-color="{p["base"]}"/></linearGradient>')


# ---------- Wallpaper ----------

@art("mountains", .62)
def mountains(p, night):
    rng = random.Random(7)
    defs = _sky(p)
    body = f'<rect width="{W}" height="{H}" fill="url(#sky)"/>'
    body += f'<circle cx="1140" cy="360" r="120" fill="{p["light"]}" opacity="{.8 if night else .7}"/>'
    if night:
        body += _stars(rng, 140, 0, 520, "#ffffff")
    layers = [(520, 70, .72), (600, 80, .55), (690, 70, .38), (790, 60, .2)]
    for i, (y, amp, t) in enumerate(layers):
        if night:  # hinten dunstig hell, vorne tief
            color = _mix(_mix(p["a"], p["base"], .45), _mix(p["deep"], "#000000", .4), i / 3)
        else:
            color = _mix(p["a"], p["base"], t + .15)
        body += f'<path d="{_ridge(rng, y, amp, steps=7 + i)}" fill="{color}"/>'
    return _svg(body, defs)


@art("lofi_city", .74)
def lofi_city(p, night):
    rng = random.Random(21)
    sky_top = _mix("#07070f", p["a"], .25) if night else _mix(p["base"], p["b"], .35)
    defs = (f'<linearGradient id="s" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{sky_top}"/>'
            f'<stop offset="1" stop-color="{_mix(sky_top, p["a"], .35)}"/></linearGradient>')
    body = f'<rect width="{W}" height="{H}" fill="url(#s)"/>'
    body += _stars(rng, 160 if night else 0, 0, 560, "#ffffff")
    moon = "#fff6e0" if night else "#ffffff"
    body += f'<circle cx="420" cy="260" r="80" fill="{moon}" opacity=".9"/>'
    body += f'<circle cx="450" cy="245" r="72" fill="{sky_top}" opacity="{.85 if night else 0}"/>'
    window = _mix(p["a"], "#ffe6a8", .55)
    for layer, (base_y, dark) in enumerate(((660, .55), (720, .75), (790, .92))):
        x = -20
        fill = _mix(sky_top, "#000000", dark) if night else _mix(sky_top, _mix(p["deep"], "#3a3550", .5), dark * .7)
        while x < W:
            w = rng.randint(60, 140)
            h = rng.randint(80, 260) + layer * 30
            body += f'<rect x="{x}" y="{base_y - h}" width="{w}" height="{h + 400}" fill="{fill}"/>'
            if layer == 2:
                for wy in range(base_y - h + 18, base_y + 120, 26):
                    for wx in range(x + 12, x + w - 14, 22):
                        if rng.random() < .28:
                            body += f'<rect x="{wx}" y="{wy}" width="9" height="12" fill="{window}" opacity="{rng.uniform(.5, .95):.2f}"/>'
            x += w + rng.randint(0, 12)
    return _svg(body, defs)


@art("fuji", .55)
def fuji(p, night):
    rng = random.Random(3)
    top = _mix(p["base"], p["c"], .45 if night else .3)
    defs = (f'<linearGradient id="s" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{top}"/>'
            f'<stop offset=".7" stop-color="{_mix(top, p["a"], .45)}"/><stop offset="1" stop-color="{p["base"]}"/></linearGradient>'
            )
    body = f'<rect width="{W}" height="{H}" fill="url(#s)"/>'
    if night:
        body += _stars(rng, 90, 0, 420, "#ffffff", 1.2)
    sun = _mix(p["a"], "#ffd27a", .45)
    body += f'<circle cx="800" cy="430" r="230" fill="{sun}"/>'
    for i in range(7):  # Retro-Streifen im unteren Teil der Sonne, als Sehnen des Kreises
        y = 470 + i * 26
        half = math.sqrt(max(0, 230 ** 2 - (y - 430) ** 2))
        body += f'<rect x="{800 - half:.0f}" y="{y}" width="{2 * half:.0f}" height="{6 + i * 2}" fill="{_mix(top, p["a"], .45)}"/>'
    mountain = _mix(p["deep"], "#000000", .3) if night else _mix(p["a"], "#2a2440", .55)
    body += (f'<path d="M360,760 C560,640 680,470 760,420 L840,420 C920,470 1040,640 1240,760 Z" fill="{mountain}"/>'
             f'<path d="M760,420 L840,420 C870,440 895,470 915,500 C880,490 860,515 835,500 C815,520 790,495 770,510 '
             f'C750,495 725,505 690,500 C715,465 735,440 760,420 Z" fill="#ffffff" opacity=".92"/>')
    body += f'<path d="{_ridge(rng, 790, 25, 6)}" fill="{_mix(mountain, p["base"], .25)}"/>'
    body += f'<path d="{_ridge(rng, 860, 20, 5)}" fill="{_mix(mountain, "#000000", .25)}"/>'
    petal = _mix(p["a"], "#ffd6e6", .6)
    for _ in range(46):  # Kirschblüten
        x, y, r = rng.uniform(0, W), rng.uniform(0, H), rng.uniform(5, 11)
        body += (f'<ellipse cx="{x:.0f}" cy="{y:.0f}" rx="{r:.1f}" ry="{r * .55:.1f}" fill="{petal}" '
                 f'opacity="{rng.uniform(.45, .9):.2f}" transform="rotate({rng.uniform(0, 180):.0f} {x:.0f} {y:.0f})"/>')
    return _svg(body, defs)


@art("sakura", .2)
def sakura(p, night):
    rng = random.Random(11)
    defs = _sky(p)
    body = f'<rect width="{W}" height="{H}" fill="url(#sky)"/>'
    branch = _mix(p["deep"], "#000000", .35) if night else "#4a3a40"
    # Ast von oben rechts
    body += (f'<path d="M1650,40 C1450,90 1300,130 1150,230 C1060,290 990,300 900,330" stroke="{branch}" stroke-width="16" '
             f'fill="none" stroke-linecap="round"/>'
             f'<path d="M1300,140 C1260,210 1250,260 1270,330" stroke="{branch}" stroke-width="9" fill="none" stroke-linecap="round"/>'
             f'<path d="M1100,255 C1060,200 1010,180 960,170" stroke="{branch}" stroke-width="7" fill="none" stroke-linecap="round"/>')
    blossom = _mix(p["a"], "#ffd1e3", .55)
    centers = [(1500, 70), (1400, 105), (1320, 130), (1240, 180), (1180, 220), (1100, 255), (1020, 290), (940, 320),
               (1280, 250), (1270, 320), (1010, 180), (960, 168), (1350, 95), (1150, 250), (1060, 205)]
    for cx, cy in centers:
        for k in range(5):
            a = k * 72 + rng.uniform(-8, 8)
            x, y = cx + 13 * math.cos(math.radians(a)), cy + 13 * math.sin(math.radians(a))
            body += f'<circle cx="{x:.0f}" cy="{y:.0f}" r="11" fill="{blossom}" opacity=".95"/>'
        body += f'<circle cx="{cx}" cy="{cy}" r="5" fill="{_mix(blossom, p["a"], .6)}"/>'
    for _ in range(40):
        x, y, r = rng.uniform(300, W), rng.uniform(200, H), rng.uniform(5, 10)
        body += (f'<ellipse cx="{x:.0f}" cy="{y:.0f}" rx="{r:.1f}" ry="{r * .55:.1f}" fill="{blossom}" '
                 f'opacity="{rng.uniform(.35, .8):.2f}" transform="rotate({rng.uniform(0, 180):.0f} {x:.0f} {y:.0f})"/>')
    body += f'<path d="{_ridge(rng, 880, 25, 6)}" fill="{_mix(p["a"], p["base"], .78 if night else .7)}"/>'
    return _svg(body, defs)


@art("topo", .5)
def topo(p, night):
    rng = random.Random(5)
    body = f'<rect width="{W}" height="{H}" fill="{p["base"]}"/>'
    line = _mix(p["a"], p["base"], .1 if night else .35)
    strong, weak = (.8, .5) if night else (.55, .32)
    for cx, cy, rings in ((360, 320, 14), (1250, 700, 16), (1350, 150, 8), (500, 880, 9)):
        phase = [rng.uniform(0, 6.28) for _ in range(3)]
        for k in range(1, rings + 1):
            r = k * 34
            pts = []
            for i in range(73):
                a = i * 5 * math.pi / 180
                rr = r * (1 + .10 * math.sin(3 * a + phase[0]) + .06 * math.sin(5 * a + phase[1] + k * .2)
                          + .04 * math.sin(2 * a + phase[2]))
                pts.append(f"{cx + rr * math.cos(a):.0f},{cy + rr * .8 * math.sin(a):.0f}")
            body += (f'<polyline points="{" ".join(pts)}" fill="none" stroke="{line}" stroke-width="{1.6 if k % 5 == 0 else .9}" '
                     f'opacity="{strong if k % 5 == 0 else weak}"/>')
    return _svg(body)


@art("flow", .45)
def flow(p, night):
    defs = (f'<linearGradient id="g" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{p["a"]}"/>'
            f'<stop offset=".5" stop-color="{p["b"]}"/><stop offset="1" stop-color="{p["c"]}"/></linearGradient>')
    body = f'<rect width="{W}" height="{H}" fill="{p["base"]}"/>'
    for i in range(46):
        y = 120 + i * 15
        body += (f'<path d="M-100,{y + 260} C 400,{y - 120} 900,{y + 420} 1700,{y - 40}" fill="none" stroke="url(#g)" '
                 f'stroke-width="1.6" opacity="{(.3 if night else .15) + .6 * math.sin(i / 46 * math.pi):.2f}"/>')
    return _svg(body, defs)


@art("bauhaus", .5)
def bauhaus(p, night):
    soft = lambda c, t: _mix(c, p["base"], t)
    body = f'<rect width="{W}" height="{H}" fill="{p["base"]}"/>'
    body += f'<circle cx="0" cy="0" r="330" fill="{soft(p["a"], .35)}"/>'
    body += f'<path d="M1600,1000 L1600,560 A440,440 0 0 0 1160,1000 Z" fill="{soft(p["b"], .4)}"/>'
    body += f'<rect x="1270" y="70" width="230" height="230" rx="18" fill="{soft(p["c"], .5)}"/>'
    body += f'<path d="M1270,300 A115,115 0 0 1 1500,300 Z" fill="{soft(p["a"], .2)}"/>'
    body += f'<circle cx="260" cy="830" r="95" fill="none" stroke="{soft(p["a"], .3)}" stroke-width="26"/>'
    body += f'<path d="M0,620 L190,620 L0,430 Z" fill="{soft(p["c"], .45)}"/>'
    for i in range(6):
        body += f'<circle cx="{620 + i * 40}" cy="900" r="7" fill="{soft(p["ink"], .55)}"/>'
    return _svg(body)


@art("planet", .8)
def planet(p, night):
    rng = random.Random(9)
    space = "#06060c" if night else _mix(p["base"], p["a"], .12)
    defs = (f'<radialGradient id="pl" cx=".4" cy=".25" r=".8"><stop offset="0" stop-color="{_mix(p["a"], "#ffffff", .35)}"/>'
            f'<stop offset=".6" stop-color="{p["a"]}"/><stop offset="1" stop-color="{p["deep"]}"/></radialGradient>'
            f'<radialGradient id="glow" cx=".5" cy=".5" r=".5"><stop offset=".78" stop-color="{p["a"]}" stop-opacity=".45"/>'
            f'<stop offset="1" stop-color="{p["a"]}" stop-opacity="0"/></radialGradient>')
    body = f'<rect width="{W}" height="{H}" fill="{space}"/>'
    body += _stars(rng, 220, 0, H, "#ffffff" if night else p["deep"], 1.4)
    body += f'<circle cx="800" cy="1650" r="1050" fill="url(#glow)"/>'
    body += f'<circle cx="800" cy="1650" r="900" fill="url(#pl)"/>'
    body += f'<circle cx="1260" cy="240" r="46" fill="{_mix(p["b"], "#ffffff", .3)}" opacity=".9"/>'
    return _svg(body, defs)


def wallpaper_svg(name, accent, night):
    fn, _focus = ART[name]
    return fn(_palette(accent, night), night)


def focus(name):
    return ART[name][1]
