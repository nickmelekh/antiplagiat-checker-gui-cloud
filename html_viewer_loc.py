import sys
import os

from PyQt5 import QtCore, QtWidgets, QtWebEngineWidgets
app = QtWidgets.QApplication(sys.argv)
view = QtWebEngineWidgets.QWebEngineView()

view.load(QtCore.QUrl().fromLocalFile(
    os.path.join(os.path.dirname(sys.modules[__name__].__file__), '/Users/nikitameleh/Documents/apps/plagiarism_repo/wiki/article1/lev.html')
))
view.show()
sys.exit(app.exec_())