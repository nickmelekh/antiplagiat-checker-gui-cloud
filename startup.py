import os
import sys
import subprocess
import dropbox

from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *

myconfig = './config/config.py'
sys.path.append(os.path.dirname(os.path.expanduser(myconfig)))

from config import dropbox_token
print(dropbox_token)

main = 'main_app.py'
sys.path.append(os.path.dirname(os.path.expanduser(main)))
import main_app

text_editor = 'text_editor.py'
sys.path.append(os.path.dirname(os.path.expanduser(text_editor)))
import text_editor

html_viewer = 'html_viewer.py'
sys.path.append(os.path.dirname(os.path.expanduser(html_viewer)))

class StackedWidget(QStackedWidget):
    def __init__(self, parent=None):
        QStackedWidget.__init__(self, parent=parent)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.drawPixmap(self.rect(), QPixmap('./ext/style/startup_background_1.png'))
        QStackedWidget.paintEvent(self, event)

class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        QMainWindow.__init__(self, parent=parent)
        self.init_ui()
        self.account_is_checked = False
        self.token_is_changed = False

    def init_ui(self):
        self.setFixedSize(500, 480)
        self.center()
        
        self.frame = QFrame(self)
        self.layout = QGridLayout()
        self.frame.setLayout(self.layout)

        self.setWindowTitle('Welcome page')
        self.setCentralWidget(StackedWidget())
        self.statusBar().showMessage('Ready')

        tb = QToolBar('Menu')
        self.addToolBar(Qt.BottomToolBarArea, tb)
        tb.setToolButtonStyle(3)
        tb.setOrientation(1)
        tb.setMovable(0)

        # вызов основного приложения
        startMainApp = QAction(QIcon('./ext/style/run.png'), 'Dropbox', self)
        startMainApp.triggered.connect(self.launch_main_app)
        tb.addAction(startMainApp)
        startMainApp = QAction(QIcon('./ext/style/local.png'), 'Local', self)
        startMainApp.triggered.connect(self.launch_local_app)
        tb.addAction(startMainApp)

        # вызов функции проверки доступности Dropbox
        checkConnection = QAction(QIcon('./ext/style/net.png'), 'Account', self)
        checkConnection.triggered.connect(self.check_connection)
        tb.addAction(checkConnection)

        # вызов функции изменения аккаунта Dropbox
        changeSettings = QAction(QIcon('./ext/style/settings.png'), 'Settings', self)
        changeSettings.triggered.connect(self.show_dbx_settings)
        tb.addAction(changeSettings)

        # открытие текстового редактора
        openEditMenu = QAction(QIcon('./ext/style/edit.png'), 'Scripts', self)
        openEditMenu.triggered.connect(self.open_text_editor)
        tb.addAction(openEditMenu)

        # вызов помощника
        openHelp = QAction(QIcon('./ext/style/search.png'), 'Help', self)
        openHelp.triggered.connect(self.open_help)
        tb.addAction(openHelp)

        # выход из приложения
        exitAct = QAction(QIcon('./ext/style/close.png'), 'Exit', self)
        exitAct.setShortcut('Ctrl+Q')
        exitAct.triggered.connect(qApp.quit)
        tb.addAction(exitAct)

        self.show()

    def center(self):
        # отрисовка окна приложения по центру экрана
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def replace_in_file(self, filename, key, new_value):
        with open(filename, 'r') as file :
            filedata = file.read()

        filedata = filedata.replace(key, new_value)

        with open(filename, 'w') as file:
            file.write(filedata)

        self.statusBar().showMessage('Accesstoken changed')

    def show_dbx_settings(self):
        text, ok = QInputDialog.getText(self, 'Dropbox settings', 'Enter Dropbox token:')
        if ok:
            self.replace_in_file(myconfig, dropbox_token, text)
            self.token_is_changed = True


    def launch_main_app(self):
        self.check_connection()
        if self.account_is_checked == True:
            subprocess.Popen('python main_app.py', shell=True)
            self.statusBar().showMessage('Main app started. Please wait')
        else:
            pass

    def launch_local_app(self):
        subprocess.Popen('python main_app_local.py', shell=True)
        self.statusBar().showMessage('Local app started. Please wait')

    def open_text_editor(self):
        subprocess.Popen('python text_editor.py', shell=True)
        self.statusBar().showMessage('Text editor opened')

    def open_help(self):
        subprocess.Popen('python html_viewer_loc.py', shell=True)
        self.statusBar().showMessage('Help opened')

    def check_connection(self):
        self.statusBar().showMessage('Сheck in progress. Please wait')
        try:
            dbx = dropbox.Dropbox(dropbox_token)
            if dbx.users_get_current_account().email != '':
                print(dbx.users_get_current_account().email)
                self.statusBar().showMessage('Welcome, ' + dbx.users_get_current_account().email + '!')
                self.account_is_checked = True
                self.token_is_changed = False
        except:
            self.statusBar().showMessage('Account check error. Please check your Dropbox token')

if __name__ == '__main__':
    # инициализация класса приложения
    app = QApplication(sys.argv)
    # передача приложению кастомной иконки
    path = os.path.join(os.path.dirname(sys.modules[__name__].__file__), './ext/style/icon_4.png')
    app.setWindowIcon(QIcon(path))
    w = MainWindow()
    w.show()

    sys.exit(app.exec_())