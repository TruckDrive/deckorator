# Nachbauten von Kartenverwaltung und Anki-Einstellungen aus echten Qt-Bauteilen, damit die
# Vorschau zeigt, was die Einstellungen unter "Bereiche" bewirken. Sie werden mit demselben
# Code gestylt wie die echten Fenster (windows.py).
from types import SimpleNamespace

from aqt.qt import *


class _Sidebar(QTreeView):
    def _setup_style(self):  # wie Ankis Seitenleiste: eigenes Stylesheet zurücksetzen
        self.setStyleSheet("")


class MockBrowser(QMainWindow):
    def __init__(self, t, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.Widget)
        central = QWidget()
        h = QHBoxLayout(central)
        h.setContentsMargins(8, 8, 8, 8)
        self.sidebar = _Sidebar()
        model = QStandardItemModel(self.sidebar)
        for name, children in t("mock_sidebar"):
            item = QStandardItem(name)
            for c in children:
                item.appendRow(QStandardItem(c))
            model.appendRow(item)
        self.sidebar.setModel(model)
        self.sidebar.setHeaderHidden(True)
        self.sidebar.expandAll()
        self.sidebar.setMaximumWidth(170)
        right = QVBoxLayout()
        search = QComboBox()
        search.setObjectName("searchEdit")
        search.setEditable(True)
        search.lineEdit().setPlaceholderText(t("mock_search"))
        table = QTableWidget(6, 3)
        table.setHorizontalHeaderLabels(t("mock_columns"))
        for r, row in enumerate(t("mock_rows")):
            for c, text in enumerate(row):
                table.setItem(r, c, QTableWidgetItem(text))
        table.verticalHeader().hide()
        table.horizontalHeader().setStretchLastSection(True)
        table.setAlternatingRowColors(True)
        table.selectRow(0)
        right.addWidget(search)
        right.addWidget(table, 1)
        h.addWidget(self.sidebar)
        h.addLayout(right, 1)
        self.setCentralWidget(central)
        self.form = SimpleNamespace(tableView=table, searchEdit=search)


class MockPreferences(QDialog):
    def __init__(self, t, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.Widget)
        v = QVBoxLayout(self)
        v.setContentsMargins(8, 8, 8, 8)
        tabs = QTabWidget()
        page = QWidget()
        pv = QVBoxLayout(page)
        group = QGroupBox(t("mock_group"))
        gv = QVBoxLayout(group)
        for i, label in enumerate(t("mock_checks")):
            c = QCheckBox(label)
            c.setChecked(i != 1)
            gv.addWidget(c)
        row = QHBoxLayout()
        row.addWidget(QLabel(t("mock_spin")))
        spin = QSpinBox()
        spin.setValue(20)
        row.addWidget(spin)
        gv.addLayout(row)
        pv.addWidget(group)
        pv.addStretch()
        for name in t("mock_tabs"):
            tabs.addTab(page if name == t("mock_tabs")[0] else QWidget(), name)
        v.addWidget(tabs)


class MockAddons(QDialog):
    """Add-on-Fenster mit den echten installierten Add-ons; Aktionen tun hier nichts."""

    def __init__(self, t, parent=None):
        super().__init__(parent)
        from aqt import mw
        self.setWindowFlags(Qt.WindowType.Widget)
        self.mgr = mw.addonManager
        try:
            self.addons = sorted(self.mgr.all_addon_meta(), key=lambda a: a.human_name().lower())
        except Exception:
            self.addons = []
        v = QVBoxLayout(self)
        v.setContentsMargins(8, 8, 8, 8)
        head = QLabel(t("mock_addons_head"))
        v.addWidget(head)
        body = QHBoxLayout()
        holder = QWidget()
        hl = QVBoxLayout(holder)
        hl.setContentsMargins(0, 0, 0, 0)
        addon_list = QListWidget()
        for a in self.addons:
            addon_list.addItem(a.human_name())
        hl.addWidget(addon_list)
        body.addWidget(holder, 1)
        side = QVBoxLayout()
        for label in t("mock_addon_buttons"):
            side.addWidget(QPushButton(label))
        side.addStretch()
        body.addLayout(side)
        v.addLayout(body, 1)
        self.form = SimpleNamespace(addonList=addon_list)

    def redrawAddons(self):
        pass

    def onConfig(self):
        pass

    def onViewPage(self):
        pass

    def onToggleEnabled(self):
        pass


class MockEditor(QMainWindow):
    """Fenster "Hinzufügen": Qt-Rahmen wie in Anki, die Felder als kleine Webansicht."""

    def __init__(self, t, web, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.Widget)
        central = QWidget()
        v = QVBoxLayout(central)
        v.setContentsMargins(8, 8, 8, 8)
        top = QHBoxLayout()
        for label in t("mock_editor_top"):
            top.addWidget(QLabel(label[0]))
            top.addWidget(QPushButton(label[1]), 1)
        v.addLayout(top)
        v.addWidget(web, 1)
        bottom = QHBoxLayout()
        bottom.addStretch()
        for label in t("mock_editor_buttons")[:-1]:
            bottom.addWidget(QPushButton(label))
        self.addButton = QPushButton(t("mock_editor_buttons")[-1])
        bottom.addWidget(self.addButton)
        v.addLayout(bottom)
        self.setCentralWidget(central)


# Felder des Editors mit Ankis Klassennamen, damit dasselbe CSS greift wie im echten Editor
EDITOR_HTML = """<style>
html, body {{ margin: 0; background: var(--canvas); color: var(--fg); font-family: sans-serif; }}
.fields {{ display: grid; grid-gap: 6px; padding: 10px 12px; }}
.label-container {{ font-size: 13px; padding: 2px 4px; color: var(--fg-subtle); }}
.editor-field {{ border: 1px solid var(--border); border-radius: 5px; background: var(--canvas-elevated);
  padding: 8px 10px; min-height: 22px; font-size: 15px; }}
.editor-toolbar {{ display: flex; gap: 4px; padding: 6px 12px; border-bottom: 1px solid var(--border); }}
.editor-toolbar span {{ width: 26px; height: 22px; border-radius: 5px; background: var(--button-bg); display: inline-block; }}
.tags {{ padding: 4px 12px 12px; }}
.tag {{ display: inline-block; padding: 2px 10px; margin-right: 6px; border-radius: 5px; font-size: 12px;
  background: var(--button-bg); }}
</style>
<div class="editor-toolbar">{tools}</div>
<div class="fields">{fields}</div>
<div class="tags">{tags}</div>"""


def editor_html(t):
    import html
    fields = "".join(f'<div class="field-container"><div class="label-container">{html.escape(n)}</div>'
                     f'<div class="editing-area"><div class="editor-field">{html.escape(v)}</div></div></div>'
                     for n, v in t("mock_editor_fields"))
    tags = "".join(f'<span class="tag">{html.escape(x)}</span>' for x in t("mock_editor_tags"))
    return EDITOR_HTML.format(tools="<span></span>" * 6, fields=fields, tags=tags)
