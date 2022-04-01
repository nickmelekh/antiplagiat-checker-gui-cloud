import os
import sys

from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtPrintSupport import *

myscripts = './ext/script/check_scripts.py'
sys.path.append(os.path.dirname(os.path.expanduser(myscripts)))

class MainWindow(QMainWindow):

    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)

        self.default_file = ''

        self.resize(600, 800)
        self.center()

        layout = QVBoxLayout()
        self.editor = QPlainTextEdit()

        fixedfont = QFontDatabase.systemFont(QFontDatabase.FixedFont)
        fixedfont.setPointSize(12)
        self.editor.setFont(fixedfont)
        self.path = None

        layout.addWidget(self.editor)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        file_toolbar = QToolBar('File')
        file_toolbar.setToolButtonStyle(3)
        self.addToolBar(file_toolbar)
        file_menu = self.menuBar().addMenu('&File')

        open_file_action = QAction(QIcon('./ext/style/add.png'), 'Open file', self)
        open_file_action.triggered.connect(self.file_open)
        file_menu.addAction(open_file_action)
        file_toolbar.addAction(open_file_action)

        save_file_action = QAction(QIcon('./ext/style/save.png'), 'Save', self)
        save_file_action.triggered.connect(self.file_save)
        file_menu.addAction(save_file_action)
        file_toolbar.addAction(save_file_action)

        saveas_file_action = QAction(QIcon('./ext/style/save.png'), 'Save As...', self)
        saveas_file_action.triggered.connect(self.file_saveas)
        file_menu.addAction(saveas_file_action)
        file_toolbar.addAction(saveas_file_action)

        edit_toolbar = QToolBar('Edit')
        edit_toolbar.setToolButtonStyle(3)
        self.addToolBar(edit_toolbar)
        edit_menu = self.menuBar().addMenu('&Edit')

        undo_action = QAction(QIcon('./ext/style/previous-1.png'), 'Undo', self)
        undo_action.triggered.connect(self.editor.undo)
        edit_toolbar.addAction(undo_action)
        edit_menu.addAction(undo_action)

        redo_action = QAction(QIcon('./ext/style/next.png'), 'Redo', self)
        redo_action.triggered.connect(self.editor.redo)
        edit_toolbar.addAction(redo_action)
        edit_menu.addAction(redo_action)

        edit_menu.addSeparator()

        cut_action = QAction(QIcon('./ext/style/pie-chart-1.png'), 'Cut', self)
        cut_action.triggered.connect(self.editor.cut)
        edit_toolbar.addAction(cut_action)
        edit_menu.addAction(cut_action)

        copy_action = QAction(QIcon('./ext/style/copy.png'), 'Copy', self)
        copy_action.triggered.connect(self.editor.copy)
        edit_toolbar.addAction(copy_action)
        edit_menu.addAction(copy_action)

        paste_action = QAction(QIcon('./ext/style/logout.png'), 'Paste', self)
        paste_action.triggered.connect(self.editor.paste)
        edit_toolbar.addAction(paste_action)
        edit_menu.addAction(paste_action)

        select_action = QAction(QIcon('./ext/style/password.png'), 'Select all', self)
        select_action.triggered.connect(self.editor.selectAll)
        edit_toolbar.addAction(select_action)
        edit_menu.addAction(select_action)

        edit_menu.addSeparator()

        wrap_action = QAction(QIcon('./ext/style/add.png'), 'Wrap text to window', self)
        wrap_action.setCheckable(True)
        wrap_action.setChecked(True)
        wrap_action.triggered.connect(self.edit_toggle_wrap)
        edit_menu.addAction(wrap_action)

        self.update_title()
        self.show()

        self.file_open(myscripts)

    def dialog_critical(self, s):
        dlg = QMessageBox(self)
        dlg.setText(s)
        dlg.setIcon(QMessageBox.Critical)
        dlg.show()

    def file_open(self, default_path = 0):
        if default_path == 0:
            path, _ = QFileDialog.getOpenFileName(self, 'Open file', '', 'Text documents (*.txt);All files (*.*)')
        else:
            path = default_path
            
        if path:
            try:
                with open(path, 'rU') as f:
                    text = f.read()

            except Exception as e:
                self.dialog_critical(str(e))

            else:
                self.path = path
                self.editor.setPlainText(text)
                self.update_title()

    def center(self):
        # отрисовка окна приложения по центру экрана
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def file_save(self):
        if self.path is None:
            return self.file_saveas()

        self._save_to_path(self.path)

    def file_saveas(self):
        path, _ = QFileDialog.getSaveFileName(self, 'Save file', '', 'Text documents (*.txt);All files (*.*)')

        if not path:
            return

        self._save_to_path(path)

    def _save_to_path(self, path):
        text = self.editor.toPlainText()
        try:
            with open(path, 'w') as f:
                f.write(text)

        except Exception as e:
            self.dialog_critical(str(e))

        else:
            self.path = path
            self.update_title()

    def update_title(self):
        pass

    def edit_toggle_wrap(self):
        self.editor.setLineWrapMode( 1 if self.editor.lineWrapMode() == 0 else 0 )


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setApplicationName('Scripts editor')
    path = os.path.join(os.path.dirname(sys.modules[__name__].__file__), './ext/style/icon_4.png')
    app.setWindowIcon(QIcon(path))

    window = MainWindow()
    app.exec_()