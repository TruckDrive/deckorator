# Konflikt-Check: andere Add-ons, die ebenfalls Ankis Aussehen umbauen, können sich mit
# Deckorator überlagern ("sieht kaputt aus"). Erkannt wird am Namen; nichts wird automatisch
# abgeschaltet, der Nutzer entscheidet.
import re

from aqt import mw
from aqt.qt import *

# Namensmuster typischer Theme-/Design-Add-ons
PATTERNS = (r"redesign", r"beautif", r"\btheme", r"recolou?r", r"dark ?mode", r"night ?mode", r"background",
            r"baloney", r"\bcss\b", r"\bstyl", r"\bskin", r"wallpaper", r"\bui\b", r"interface")


def find(own_module):
    """[(Ordner, Name)] aktiver Add-ons, die nach Theme/Design klingen."""
    am = mw.addonManager
    own = own_module.split(".")[0]
    out = []
    for d in am.allAddons():
        if d == own or not am.isEnabled(d):
            continue
        name = am.addonName(d) or d
        if any(re.search(p, name, re.I) for p in PATTERNS):
            out.append((d, name))
    return out


def check_on_start(own_module, cfg, save_config, open_settings, t):
    """Einmal pro neuem Fund nachfragen; bestätigte Funde merken."""
    known = set(cfg.get("conflicts_ack", []))
    new = [(d, n) for d, n in find(own_module) if d not in known]
    if not new:
        return
    box = QMessageBox(mw)
    box.setWindowTitle("Deckorator")
    box.setIcon(QMessageBox.Icon.Information)
    box.setText(t("conflict_text").format(names="\n".join(f"• {n}" for _d, n in new)))
    b_areas = box.addButton(t("conflict_areas"), QMessageBox.ButtonRole.ActionRole)
    b_disable = box.addButton(t("conflict_disable"), QMessageBox.ButtonRole.DestructiveRole)
    box.addButton(t("conflict_ignore"), QMessageBox.ButtonRole.RejectRole)
    box.exec()
    clicked = box.clickedButton()
    if clicked is b_disable:
        for d, _n in new:
            mw.addonManager.toggleEnabled(d, False)
        from aqt.utils import showInfo
        showInfo(t("conflict_restart"))
    cfg["conflicts_ack"] = sorted(known | {d for d, _n in new})
    save_config(cfg)
    if clicked is b_areas:
        open_settings(page="areas")
