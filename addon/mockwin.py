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
