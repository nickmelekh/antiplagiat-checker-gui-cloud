import sys
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtWebEngineWidgets import QWebEngineView
 
 
class Browser(QWebEngineView):
    def __init__(self):
        super().__init__()
        self.loadFinished.connect(self._auth)
 
        self._timer = QtCore.QTimer()
        self._timer.timeout.connect(self._check_captcha)
 
    def _auth(self):
        page = self.page()
        page.runJavaScript(
            'document.querySelector("#index_email").value = "{}"'.format(
                '12345'
            )
        )
        page.runJavaScript(
            'document.querySelector("#index_pass").value = {}'.format('12345')
        )
        page.runJavaScript(
            'document.querySelector("#index_login_button").click()'
        )
 
        self._timer.start(1000)
 
    def _check_captcha(self):
        self._timer.stop()
        self.page().runJavaScript(
            ('document.querySelector("#box_layer > div.popup_box_container > '
             'div > div.box_title_wrap > div.box_title").innerHTML'),
            self._check_captcha_callback
        )
 
    def _check_captcha_callback(self, text):
        if text == 'Введите код с картинки':
            print('Нужно ввести капчу')
 
 
app = QtWidgets.QApplication(sys.argv)
b = Browser()
# b.load(QtCore.QUrl('https://ru.wikipedia.org/wiki/Выявление_плагиата'))
b.load(QtCore.QUrl('./1.html'))
b.show()
app.exec_()