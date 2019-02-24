from PyQt5.QtWidgets import QMainWindow, QTabWidget


class MainWindow(QMainWindow):
    def __init__(self, tittle="Potato JS WebKit", width=1366, height=768):
        super().__init__()
        self.setWindowTitle(tittle)
        self.resize(width, height)

        self._tabs = QTabWidget()
        self.setCentralWidget(self._tabs)

        self.show()

    def addTab(self, tab, tittle="Tab"):
        self._tabs.addTab(tab, self.fixTabText(tittle))
        # Connect to tittle change signal and call function to update tab tittle.
        tab.titleChanged.connect(self.setTabText)

    def setTabText(self, str):
        tab = self.sender()
        idx = self._tabs.indexOf(tab)
        self._tabs.setTabText(idx, self.fixTabText(str))

    def fixTabText(self, text):
        if len(text) > 18:
            return text[:18] + "..."

        return text
