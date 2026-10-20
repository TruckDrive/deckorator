# Karten-Designs: fertige Stile für das CSS von Notiztypen (wie bei der Muskeltabelle), für
# beliebige eigene Decks. Deckorator hängt sein CSS als klar markierten Block an; das eigene CSS
# des Notiztyps bleibt unberührt und "Entfernen" stellt den Originalzustand wieder her.
# Farben werden beim Anwenden fest eingetragen, damit die Karten auch auf dem Handy so aussehen.
import re

from aqt import mw

from .theme import _mix, _rgba

BEGIN = "/* deckorator-card-style:{id} begin */"
END = "/* deckorator-card-style end */"
BLOCK_RE = re.compile(r"\n*/\* deckorator-card-style:[\w-]+ begin \*/.*?/\* deckorator-card-style end \*/\n*", re.S)

# Jeder Stil: Hell- und Dunkelvariante (Anki setzt .nightMode auf die Karte)
STYLES = {
    "clean": """
.card {{ font-family: -apple-system, "Segoe UI", Roboto, "Noto Sans", sans-serif; font-size: 20px; line-height: 1.55;
  color: #1f2937; background: {bg_light}; text-align: center; }}
#qa {{ max-width: 680px; margin: 18px auto; background: #ffffff; border-radius: 16px; padding: 22px 26px;
  box-shadow: 0 1px 3px rgba(0,0,0,.08), 0 8px 24px rgba(0,0,0,.05); }}
.card b, .card strong {{ color: {accent_text}; }}
.card hr#answer {{ border: none; height: 1px; background: #e5e7eb; margin: 18px 0; }}
.card ul, .card ol {{ text-align: left; display: inline-block; margin: 6px 0; }}
.card li::marker {{ color: {accent}; }}
.nightMode.card {{ color: #e5e7eb; background: {bg_dark}; }}
.nightMode #qa {{ background: {panel_dark}; box-shadow: none; }}
.nightMode.card b, .nightMode.card strong {{ color: {accent_night}; }}
.nightMode.card hr#answer {{ background: #374151; }}
""",
    "index": """
.card {{ font-family: Georgia, "Noto Serif", serif; font-size: 21px; line-height: 32px; color: #2b2b2b; text-align: left;
  background: #e9e4da; }}
#qa {{ max-width: 640px; margin: 22px auto; padding: 30px 28px 26px 56px; border-radius: 6px;
  background: repeating-linear-gradient(#fffdf6 0 31px, #cfe0f3 31px 32px);
  box-shadow: 0 2px 6px rgba(0,0,0,.18); position: relative; }}
#qa::before {{ content: ""; position: absolute; left: 40px; top: 0; bottom: 0; width: 2px; background: {accent}; opacity: .55; }}
.card b, .card strong {{ color: {accent_text}; }}
.card hr#answer {{ border: none; border-top: 2px dashed #c9bfae; margin: 12px 0; }}
.nightMode.card {{ background: #1e1c19; color: #e8e2d6; }}
.nightMode #qa {{ background: repeating-linear-gradient(#2a2723 0 31px, #34404d 31px 32px); box-shadow: none; }}
.nightMode.card b, .nightMode.card strong {{ color: {accent_night}; }}
""",
    "minimal": """
.card {{ font-family: -apple-system, "Segoe UI", Roboto, "Noto Sans", sans-serif; font-size: 26px; line-height: 1.5;
  color: #111111; background: #ffffff; text-align: center; padding-top: 12vh; }}
.card b, .card strong {{ font-weight: 700; color: #111111; }}
.card hr#answer {{ width: 40px; border: none; height: 3px; background: {accent}; margin: 28px auto; border-radius: 2px; }}
.card ul, .card ol {{ text-align: left; display: inline-block; font-size: 22px; }}
.nightMode.card {{ color: #f2f2f2; background: #0d0d0d; }}
.nightMode.card b, .nightMode.card strong {{ color: #ffffff; }}
""",
    "focus": """
.card {{ font-family: -apple-system, "Segoe UI", Roboto, "Noto Sans", sans-serif; font-size: 21px; line-height: 1.6;
  color: #e6e6ea; background: #121216; text-align: center; }}
#qa {{ max-width: 700px; margin: 20px auto; padding: 24px 28px; border-radius: 18px; background: #1b1b21;
  border: 1px solid {accent_border}; }}
.card b, .card strong {{ color: {accent_night}; }}
.card hr#answer {{ border: none; height: 1px; background: {accent_border}; margin: 18px 0; }}
.card li::marker {{ color: {accent_night}; }}
.card ul, .card ol {{ text-align: left; display: inline-block; }}
""",
    "notes": """
.card {{ font-family: -apple-system, "Segoe UI", Roboto, "Noto Sans", sans-serif; font-size: 19px; line-height: 1.6;
  color: #1f2937; background: {bg_light}; text-align: left; }}
#qa {{ max-width: 720px; margin: 18px auto; padding: 4px 8px; }}
.card b, .card strong {{ color: {accent_text}; }}
.card h1, .card h2, .card h3 {{ color: {accent_text}; margin: .4em 0 .3em; }}
.card hr#answer {{ border: none; height: 2px; background: {accent_soft}; margin: 16px 0; }}
.card li {{ margin: 4px 0; }}
.card li::marker {{ color: {accent}; }}
.card blockquote {{ margin: 10px 0; padding: 8px 14px; border-left: 4px solid {accent}; background: {accent_soft};
  border-radius: 0 10px 10px 0; }}
.nightMode.card {{ color: #e5e7eb; background: {bg_dark}; }}
.nightMode.card b, .nightMode.card strong, .nightMode.card h1, .nightMode.card h2, .nightMode.card h3 {{ color: {accent_night}; }}
""",
    "theme": """
.card {{ font-family: -apple-system, "Segoe UI", Roboto, "Noto Sans", sans-serif; font-size: 20px; line-height: 1.55;
  color: #1f2024; background: {bg_light}; text-align: center; }}
#qa {{ max-width: 680px; margin: 18px auto; padding: 22px 26px; border-radius: 18px;
  background: rgba(255,255,255,.75); border: 1px solid {accent_border}; }}
.card b, .card strong {{ color: {accent_text}; }}
.card hr#answer {{ border: none; height: 1px; background: {accent_border}; margin: 18px 0; }}
.card li::marker {{ color: {accent}; }}
.card ul, .card ol {{ text-align: left; display: inline-block; }}
.nightMode.card {{ color: #e7e7ea; background: {bg_dark}; }}
.nightMode #qa {{ background: rgba(255,255,255,.05); }}
.nightMode.card b, .nightMode.card strong {{ color: {accent_night}; }}
""",
}


def style_css(style_id, cfg):
    accent = cfg["accent"]
    values = {
        "accent": accent, "accent_text": _mix(accent, "#000000", .2), "accent_night": _mix(accent, "#ffffff", .4),
        "accent_soft": _rgba(accent, .12), "accent_border": _rgba(accent, .35),
        "bg_light": cfg["bg_light"], "bg_dark": cfg["bg_dark"], "panel_dark": _mix(cfg["bg_dark"], "#ffffff", .07),
    }
    return STYLES[style_id].format(**values).strip()


def strip(css):
    return BLOCK_RE.sub("\n", css or "").rstrip() + "\n"


def current_style(css):
    m = re.search(r"deckorator-card-style:([\w-]+) begin", css or "")
    return m.group(1) if m else None


def note_types():
    """[(id, Name, Anzahl Karten, aktueller Deckorator-Stil)]"""
    col = mw.col
    counts = dict(col.db.all("select n.mid, count(c.id) from cards c join notes n on c.nid = n.id group by n.mid"))
    out = []
    for nt in col.models.all():
        out.append((nt["id"], nt["name"], counts.get(nt["id"], 0), current_style(nt.get("css"))))
    return sorted(out, key=lambda x: -x[2])


def note_types_in_deck(did):
    col = mw.col
    from anki.utils import ids2str
    dids = col.decks.deck_and_child_ids(did)
    return set(col.db.list(f"select distinct n.mid from cards c join notes n on c.nid = n.id where c.did in {ids2str(dids)}"))


def apply(ntids, style_id, cfg):
    col = mw.col
    block = f"{BEGIN.format(id=style_id)}\n{style_css(style_id, cfg)}\n{END}"
    for ntid in ntids:
        nt = col.models.get(ntid)
        nt["css"] = strip(nt.get("css")) + "\n" + block + "\n"
        col.models.update_dict(nt)


def remove(ntids):
    col = mw.col
    for ntid in ntids:
        nt = col.models.get(ntid)
        if current_style(nt.get("css")):
            nt["css"] = strip(nt.get("css"))
            col.models.update_dict(nt)
