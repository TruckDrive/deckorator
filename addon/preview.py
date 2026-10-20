# Live-Vorschau im Einstellungsfenster. Zeigt die echte Deckliste und echte Karten
# des Nutzers (inkl. Bilder, MathJax, Notiztyp-CSS) über Ankis eigene Webansichten,
# damit jeder die Wirkung mit seinen eigenen Karten und in seiner Sprache sieht.
import html
import json

from anki.utils import ids2str
from aqt import gui_hooks, mw
from aqt.deckbrowser import DeckBrowserContent
from aqt.qt import *
from aqt.theme import theme_manager
from aqt.utils import tooltip, tr
from aqt.webview import AnkiWebView

from . import theme

# Ersetzt den Theme-Stil ohne Neuladen und schaltet Hell/Dunkel um
APPLY_JS = """(function (css, night) {
  var s = document.getElementById("deckorator");
  if (!s) { s = document.createElement("style"); s.id = "deckorator"; document.head.appendChild(s); }
  s.textContent = css;
  document.documentElement.classList.toggle("night-mode", night);
  document.documentElement.dataset.bsTheme = night ? "dark" : "light";
  document.body.classList.toggle("nightMode", night);
  document.body.classList.toggle("night_mode", night);
})(%s, %s);"""


class ThemePreview(QWidget):
    def __init__(self, t, api, parent=None):
        super().__init__(parent)
        self.t = t
        self.api = api
        self.px = api.base_font_px()
        self.cfg = None
        self.night = theme_manager.night_mode
        self.card = None
        self.view = "home"
        self._build()

    # ---------- Aufbau ----------

    def _segmented(self, layout, items, callback):
        group = QButtonGroup(self)
        group.setExclusive(True)
        buttons = {}
        for key, label in items:
            b = QPushButton(label)
            b.setCheckable(True)
            b.clicked.connect(lambda _=False, k=key: callback(k))
            group.addButton(b)
            layout.addWidget(b)
            buttons[key] = b
        return buttons

    def _web(self):
        w = AnkiWebView(self, title="theme preview")
        w.set_bridge_command(lambda _cmd: None, theme.PreviewContext())
        w.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)
        return w

    def _build(self):
        v = QVBoxLayout(self)
        v.setContentsMargins(0, 0, 0, 0)

        head = QHBoxLayout()
        self.view_buttons = self._segmented(
            head, [("home", self.t("view_home")), ("study", self.t("view_study"))], self.set_view)
        head.addStretch()
        self.mode_buttons = self._segmented(
            head, [(False, self.t("light")), (True, self.t("dark"))], self.set_night)
        v.addLayout(head)

        self.card_bar = QWidget()
        cb = QHBoxLayout(self.card_bar)
        cb.setContentsMargins(0, 0, 0, 0)
        b_other = QPushButton(self.t("other_card"))
        b_other.clicked.connect(lambda: self.next_card(image=False))
        b_image = QPushButton(self.t("image_card"))
        b_image.clicked.connect(lambda: self.next_card(image=True))
        self.answer_toggle = QPushButton(self.t("answer_side"))
        self.answer_toggle.setCheckable(True)
        self.answer_toggle.toggled.connect(lambda _: self._render_study())
        self.card_info = QLabel()
        self.card_info.setObjectName("ctHint")
        self.card_info.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        for w in (b_other, b_image, self.answer_toggle):
            cb.addWidget(w)
        cb.addWidget(self.card_info, 1)
        v.addWidget(self.card_bar)

        self.stack = QStackedWidget()
        self.home_web = self._web()
        self.stack.addWidget(self.home_web)
        study = QWidget()
        sl = QVBoxLayout(study)
        sl.setContentsMargins(0, 0, 0, 0)
        sl.setSpacing(0)
        self.card_web = self._web()
        self.bar_web = self._web()
        self.bar_web.setFixedHeight(76)
        sl.addWidget(self.card_web, 1)
        sl.addWidget(self.bar_web)
        self.stack.addWidget(study)
        v.addWidget(self.stack, 1)

        self.view_buttons["home"].setChecked(True)
        self.mode_buttons[self.night].setChecked(True)
        self.card_bar.setVisible(False)

    # ---------- Steuerung ----------

    def set_config(self, cfg):
        """Neues CSS in die vorhandenen Ansichten schieben (ohne Neuladen)."""
        first = self.cfg is None
        self.cfg = cfg
        if first:
            self._render_home()
        else:
            self._apply_all()

    def set_view(self, view):
        if view == self.view:
            return
        self.view = view
        self.view_buttons[view].setChecked(True)
        self.card_bar.setVisible(view == "study")
        self.stack.setCurrentIndex(0 if view == "home" else 1)
        if view == "study":
            if self.card is None:
                self.next_card(image=False)
            else:
                self._render_study()
        else:
            self._render_home()

    def set_night(self, night):
        self.night = night
        self.mode_buttons[night].setChecked(True)
        if self.view == "study":
            # Kartenklassen (nightMode) hängen am Kartenrendering
            self._render_study()
        else:
            self._apply_all()

    def next_card(self, image):
        cid = self._random_card_id(image)
        if image and not cid:
            tooltip(self.t("no_image"), parent=self)
            return
        self.card = mw.col.get_card(cid) if cid else None
        self.answer_toggle.setChecked(False)
        self._render_study()

    def _random_card_id(self, image):
        col = mw.col
        if not col:
            return None
        dids = col.decks.deck_and_child_ids(col.decks.get_current_id())
        img = "and n.flds like '%<img%'" if image else ""
        # zuerst im aktuellen Stapel, dann in der ganzen Sammlung
        for deck in (f"and c.did in {ids2str(dids)}", ""):
            cid = col.db.scalar(
                f"select c.id from cards c join notes n on c.nid = n.id "
                f"where c.queue >= 0 {img} {deck} order by random() limit 1")
            if cid:
                return cid
        return None

    # ---------- Rendern ----------

    def _apply(self, web, scope):
        # gleiche Ableitungen (z.B. Sparmodus) wie im Hauptfenster, damit die Vorschau stimmt
        cfg = self.api.effective(self.cfg)
        css = theme.build_css_text(cfg, scope, self.px, self.api.bg_url(cfg))
        web.eval(APPLY_JS % (json.dumps(css), json.dumps(self.night)))

    def _apply_all(self):
        if self.view == "home":
            self._apply(self.home_web, "main")
        else:
            self._apply(self.card_web, "card")
            self._apply(self.bar_web, "bar")

    def _home_body(self):
        links = (tr.actions_decks(), tr.actions_add(), tr.qt_misc_browse(), tr.qt_misc_stats(), tr.qt_misc_sync())
        # Topbar und untere Leiste sind in Anki eigene Flächen, hier als Bänder nachgebaut
        toolbar = ('<div class="ct-band"><div class="header"><div class="left-tray"></div><div class="toolbar">%s</div>'
                   '<div class="right-tray"></div></div></div>') % "".join(
            f'<a class="hitem" href="#">{html.escape(x)}</a>' for x in links)
        try:
            # dieselbe Deckliste wie im Hauptfenster
            db = mw.deckBrowser
            data = DeckBrowserContent(tree=db._renderDeckTree(db._render_data.tree), stats=db._renderStats())
            # andere Add-ons (z.B. Review Heatmap) hängen sich hier ein, genau wie im Hauptfenster
            gui_hooks.deck_browser_will_render_content(db, data)
            content = db._body % data.__dict__
        except Exception:
            content = f"<center><div id='outer'><p>{html.escape(self.t('no_decks'))}</p></div></center>"
        buttons = "".join(f"<button>{html.escape(x)}</button> "
                          for x in (tr.decks_get_shared(), tr.decks_create_deck(), tr.decks_import_file()))
        band = ("<style>html body { margin: 0; padding: 0; } .ct-band { background: var(--ct-canvas); padding: 2px 0; }"
                ".ct-bottom { position: fixed; bottom: 0; left: 0; right: 0; padding: 6px 0; text-align: center; }"
                ".ct-main { padding: 0 16px 90px; } html { zoom: .82; }</style>")
        return (f"{band}{toolbar}<div class='ct-main'>{content}</div>"
                f"<div class='ct-band ct-bottom'>{buttons}</div>")

    def _render_home(self):
        self.home_web.stdHtml(self._home_body(), css=["css/toolbar.css", "css/deckbrowser.css"],
                              js=["js/vendor/jquery.min.js"], context=theme.PreviewContext())
        self._apply(self.home_web, "main")

    def _render_study(self):
        card = self.card
        answer = self.answer_toggle.isChecked()
        if card:
            q = mw.prepare_card_text_for_display(card.question())
            a = mw.prepare_card_text_for_display(card.answer())
            bodyclass = theme_manager.body_classes_for_card_ord(card.ord, self.night)
            self.card_info.setText(mw.col.decks.name(card.did))
        else:
            q = f"<div style='text-align:center;font-size:1.4em'>{html.escape(self.t('demo_q'))}</div>"
            a = q + f"<hr id=answer><div style='text-align:center'>{html.escape(self.t('demo_a'))}</div>"
            bodyclass = "card card1 " + theme_manager.body_class(self.night, reviewer=True)
            self.card_info.setText(self.t("no_cards"))

        self.card_web.stdHtml(mw.reviewer.revHtml(), css=["css/reviewer.css"], js=["js/reviewer.js"],
                              context=theme.PreviewContext())
        self._apply(self.card_web, "card")
        self.card_web.eval(f"_showQuestion({json.dumps(q)}, {json.dumps(a)}, {json.dumps(bodyclass)});")
        if answer:
            self.card_web.eval(f"_showAnswer({json.dumps(a)});")
        # _showQuestion setzt die Body-Klassen neu, daher danach nochmal Hell/Dunkel setzen
        self._apply(self.card_web, "card")

        self.bar_web.stdHtml(self._bar_body(answer), css=["css/toolbar-bottom.css", "css/reviewer-bottom.css"],
                             js=["js/vendor/jquery.min.js"], context=theme.PreviewContext())
        self._apply(self.bar_web, "bar")

    def _remaining(self):
        """Restzähler wie im Reviewer: Neu + Lernen + Wiederholen, aktuelle Kartenart unterstrichen."""
        if not mw.col.conf.get("dueCounts", True):
            return ""
        try:
            counts = list(mw.col.sched.counts())[:3]
        except Exception:
            counts = [12, 3, 48]
        idx = 0
        if self.card:
            idx = {0: 0, 1: 1, 3: 1}.get(self.card.queue, 2)
        counts[idx] = f"<u>{counts[idx]}</u>"
        return ("<span class=stattxt><span class=new-count>%s</span> + "
                "<span class=learn-count>%s</span> + <span class=review-count>%s</span></span>" % tuple(counts))

    def cleanup(self):
        for w in (self.home_web, self.card_web, self.bar_web):
            w.cleanup()

    def _bar_body(self, answer):
        if answer:
            labels = ["", "", "", ""]
            if self.card and mw.col.conf.get("estTimes", True):
                try:
                    states = mw.col._backend.get_scheduling_states(self.card.id)
                    labels = list(mw.col.sched.describe_next_states(states))
                except Exception:
                    pass
            names = (tr.studying_again(), tr.studying_hard(), tr.studying_good(), tr.studying_easy())
            middle = "<table cellpadding=0><tr>%s</tr></table>" % "".join(
                f"<td align=center><button data-ease='{i + 1}'{' id=defease' if i == 2 else ''}>"
                f"{f'<span class=nobold>{html.escape(lbl)}</span>' if lbl else ''}{html.escape(name)}</button></td>"
                for i, (name, lbl) in enumerate(zip(names, labels)))
        else:
            middle = ("<table cellpadding=0><tr><td class=stat2 align=center>"
                      f"<button id=ansbut>{html.escape(tr.studying_show_answer())}{self._remaining()}</button>"
                      "</td></tr></table>")
        return f"""<center id=outer><table id=innertable width=100% cellspacing=0 cellpadding=0><tr>
<td align=start valign=top class=stat><button>{html.escape(tr.studying_edit())}</button></td>
<td align=center valign=top id=middle>{middle}</td>
<td align=end valign=top class=stat><button>{html.escape(tr.studying_more())} ▾</button></td>
</tr></table></center>"""
