import os
import sys
import shutil
# import subprocess

import re
import json
import dropbox

import numpy as np
import pandas as pd
import networkx as nx
import pygraphviz
from networkx.drawing.nx_agraph import graphviz_layout

from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *

import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

from inspect import getmembers, isfunction

# импорт файла с алгоритмами сравнения
scriptfile = 'ext/script/check_scripts.py'
sys.path.append(os.path.dirname(os.path.expanduser(scriptfile)))
import check_scripts
from check_scripts import *

myconfig = 'config/config.py'
sys.path.append(os.path.dirname(os.path.expanduser(myconfig)))
from config import *

class LocalData():
    def __init__(self):
        self.file_list = self.select_files_from_local()
        self.file_list = [i for i in self.file_list if i.endswith('.c')]
        self.active_files = self.file_list.copy()
        self.local_dataframe = pd.DataFrame()

    def select_files_from_local(self):
        return os.listdir('local')

    def print_active_files(self):
        print(self.active_files)

    def normalize_text(self, code):
        if type(code) == str:
            code = re.sub('^\s+|\t|\r|\\n|\s{2,}|\s+$', '', code)
            code = re.split('[- : ( ) + \\ \n \' "]', code)
            code = list(filter(None, code))
            code = [(el.strip()) for el in code]
        return code

    def import_active_files(self):
        data = pd.DataFrame()
        self.local_dataframe = pd.DataFrame()

        for element in self.active_files:
            f = open('local/' + str(element))

            data = [[element, self.normalize_text(f.read())]] 
            self.local_dataframe = self.local_dataframe.append(data, ignore_index = True)

        self.local_dataframe.columns = ['hash_value', 'task_code']
        print(self.local_dataframe)
        window.update_table(self.local_dataframe)

class CheckMethod():
    def __init__(self):
        self.methods_list = [o for o in getmembers(check_scripts) if isfunction(o[1])]
        # список доступных методов
        self.method_name = []
        self.active_methods = []
        for i in range(len(self.methods_list)):
            self.method_name.append(self.methods_list[i][0])

        print('All methods:', self.method_name)
        print('Active methods:', self.active_methods)
        # dataframe, хранящий результаты работы функции анализа из check_scripts.py. Каждый новый вызов функции анализа вызывает перезапись этого dataframe'а
        self.result_dataframe = pd.DataFrame()

    def merge_results(self, df1, df2):
        # объединение данных dataframe'ов df1 и df2
        if df1.shape[0] > 0 and df1.shape[0] > 0:
            df11 = df1.iloc[:, :1]
            df12 = df1.iloc[:, 1:]
            df22 = df2.iloc[:, 1:]
            df12 = round((df12 + df22) / 2, 2)
            result = pd.concat([df11, df12], axis = 1, sort = False)
        else:
            result = df2
        return result

    # поочередно вызывает выполнение активных методов анализа, объявленных в блоке функций анализа
    def start_scripts(self):
        self.result_dataframe = pd.DataFrame()
        for method in self.active_methods:
            print('Method_name:', method)
            function = getattr(check_scripts, method) 
            self.result_dataframe = self.merge_results(self.result_dataframe, function(lcl.local_dataframe))

class GraphWindow(QWidget):
    def __init__(self, data):
        super().__init__()
        self.setWindowTitle('New graph')
        self.data = data
        self.df_klasters = data
        self.approval_rate = 70
        self.initUI()

    def initUI(self):
        sizeObject = QDesktopWidget().screenGeometry(-1)
        self.resize(1200, 800)

        title = QLabel('Actions:')
        table_title = QLabel('Сalculated clusters:')

        self.m = PlotCanvas(self, self.data, self.approval_rate)

        self.table = QTableWidget()
        window.convert_pandas_to_widget(self.table, self.nodes_to_dataframe(self.m.G))

        btnRedraw = QPushButton('Redraw', self)
        btnRedraw.clicked.connect(self.redraw_click)
        btnSave = QPushButton('Save', self)
        btnSave.clicked.connect(self.save_picture)

        sld = QSlider(Qt.Horizontal, self)
        sld.setFocusPolicy(Qt.NoFocus)
        sld.setGeometry(155, 90, 100, 30)
        sld.setMinimum(1)
        sld.setMaximum(99)
        sld.setValue(50)
        sld.valueChanged[int].connect(self.change_value)

        self.label = QLabel(self)
        self.label.setText(str(self.approval_rate))
        self.label.setGeometry(260, 90, 40, 30)

        grid = QGridLayout()
        grid.setSpacing(5)

        grid.addWidget(title, 0, 0)
        grid.addWidget(btnRedraw, 1, 0)
        grid.addWidget(btnSave, 1, 1)
        grid.addWidget(self.m, 0, 3, 16, 16)
        grid.addWidget(table_title, 3, 0)
        grid.addWidget(self.table, 4, 0, 16, 2)
        grid.setColumnStretch(3, 16)
        self.setLayout(grid)
        self.show()

    def update_table(self):
        self.nodes_to_dataframe(self.m.G)
        print(self.df_klasters)
        window.convert_pandas_to_widget(self.table, self.df_klasters)
        self.table.setHorizontalHeaderLabels(list(data.columns.values))
        self.table.setWordWrap(True)
        self.table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)

    def redraw_click(self):
        self.update_table()
        self.m.plot()

    def change_value(self, value):
        self.approval_rate = value
        self.label.setText(str(self.approval_rate))
        self.m.approval_rate = self.approval_rate

    def save_picture(self):
        self.m.fig.savefig('./ext/style/f.png', dpi = 50, format = 'png')

    def show_names(self):
        pass

    def nodes_to_dataframe(self, G):
        nodes = []
        df_klasters = pd.DataFrame()

        for node in G.adj:
            nodes.append(node)
        d_edges = dict(G.adj)

        for node in nodes:
            klaster = []
            klaster.append(node)
            for key in dict(d_edges[node]).keys():
                klaster.append(key)
                try:
                    nodes.remove(key)
                except:
                    pass
            df_klaster = pd.Series(klaster)
            df_klasters = pd.concat([df_klasters, df_klaster], ignore_index = True, axis = 1)
        self.df_klasters = df_klasters
        return df_klasters

class PlotCanvas(FigureCanvas):
    def __init__(self, filename, data, approval_rate, parent = None, width = 50, height = 80, dpi = 100):
        self.fig = Figure(figsize = (width, height), dpi = dpi)
        self.axes = self.fig.add_subplot(111)
        self.data = data
        self.df_gr = self.data
        self.approval_rate = approval_rate
        self.G = ''
        self.ax1 = ''

        FigureCanvas.__init__(self, self.fig)
        self.setParent(parent)
        FigureCanvas.setSizePolicy(self, QSizePolicy.Expanding, QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)
        self.plot()

    def plot(self):
        print(self.approval_rate)
        self.ax1 = self.figure.add_subplot(111)
        self.ax1.cla()

        box = self.ax1.get_position()
        self.ax1.set_position([box.x0, box.y0, box.width * 1 , box.height * 1])

        df_gr = pd.DataFrame({'From': [], 'To': [], 'Weight': []})

        for hash1 in self.data.columns[1:]:
            for hash2 in range(0, self.data.shape[0]):
                weight = self.data[hash1][hash2]
                if weight > self.approval_rate and weight < 100:
                    df_gr = df_gr.append({'From': hash1,
                                        'To': self.data['File'][hash2],
                                        'Weight': weight},
                                        ignore_index = True)

        # self.min_weight = ((df_gr['Weight'].mean() // 10) + 1) * 10

        self.G = nx.from_pandas_edgelist(df_gr, 'From', 'To')
        # pos = nx.spring_layout(self.G, k = 0.55, iterations = 800)
        # pos = graphviz_layout(self.G, prog = 'circo', args = '')
        pos = graphviz_layout(self.G, prog = 'twopi', args = '')

        colors = [i / len(self.G.nodes) for i in range(len(self.G.nodes))]

        nx.draw(self.G,
                pos,
                ax = self.ax1,
                node_size = list(df_gr['Weight'] ** 2.5 / 35),
                line_color = 'grey',
                linewidths = 0.7,
                width = 0.5,
                with_labels = True,
                font_size = 8,
                node_color = colors,
                cmap = plt.cm.get_cmap('rainbow'),
                alpha = 0.8)
        self.draw()

class App(QMainWindow):
    def __init__(self):
        super().__init__()
        self.data = chm.result_dataframe
        self.level = '1'
        self.graphs = []

        self.init_ui()

    def init_ui(self):
        self.resize(800, 600)
        self.center()
        self.setWindowTitle('Consequentia')
        self.frame = QFrame(self)
        self.layout = QGridLayout()
        self.frame.setLayout(self.layout)
        self.setCentralWidget(self.frame)
        self.statusBar().showMessage('')

        tb = self.addToolBar('Menu')
        tb.setToolButtonStyle(3)

        # объявление кнопок верхнего меню
        addFile = QAction(QIcon('./ext/style/add.png'), 'Add', self)
        addFile.triggered.connect(self.add_files_to_local)
        tb.addAction(addFile)

        startAnalyze = QAction(QIcon('./ext/style/analyze.png'), 'Analyze', self)
        startAnalyze.triggered.connect(self.analyze_dataframe)
        tb.addAction(startAnalyze)

        createGraph = QAction(QIcon('./ext/style/graph.png'), 'Graph', self)
        createGraph.triggered.connect(self.create_graph)
        tb.addAction(createGraph)

        saveResults = QAction(QIcon('./ext/style/save.png'), 'Save', self)
        saveResults.triggered.connect(self.save_data)
        tb.addAction(saveResults)

        showAct = QAction(QIcon('./ext/style/run.png'), 'Show files', self)
        showAct.triggered.connect(lcl.import_active_files)
        tb.addAction(showAct)

        # updateLocalAct = QAction(QIcon('./ext/style/close.png'), 'Update tree', self)
        # updateLocalAct.triggered.connect(self.update_local_tree)
        # tb.addAction(updateLocalAct)

        exitAct = QAction(QIcon('./ext/style/close.png'), 'Exit', self)
        exitAct.setShortcut('Ctrl+Q')
        exitAct.triggered.connect(qApp.quit)
        tb.addAction(exitAct)

        # список доступных методов
        self.method_tree = QTreeWidget()
        self.method_tree.setHeaderLabels(['Methods:'])
        methodCategory = QTreeWidgetItem([' '])
        self.method_tree.addTopLevelItem(methodCategory)
        for i in chm.method_name:
            methodName = QTreeWidgetItem(self.method_tree)
            methodName.setText(0, i)
            methodName.setFlags(methodName.flags() | Qt.ItemIsTristate | Qt.ItemIsUserCheckable)
            methodName.setCheckState(0, Qt.Unchecked)
            methodCategory.addChild(methodName)

        self.method_tree.itemChanged.connect(self.handle_item_changed)

        # результирующая таблица
        self.table = QTableWidget()
        self.convert_pandas_to_widget(self.table, self.data)
        self.table.setHorizontalHeaderLabels(str(i) for i in range(self.data.shape[1]))
        self.table.horizontalHeader().setVisible(True)

        # развертка окна приложения
        self.layout.addWidget(self.method_tree, 1, 0)
        self.layout.setRowStretch(1, 1)
        self.layout.setRowStretch(2, 2)
        self.layout.addWidget(self.table, 1, 1, 3, 3)
        self.init_local_tree()
        self.layout.setColumnStretch(1, 1)

        self.show()

    def init_local_tree(self):
        # список выбранных файлов
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(['Files:'])
        fileCategory = QTreeWidgetItem([' '])
        self.tree.addTopLevelItem(fileCategory)
        for i in lcl.file_list:
            fileName = QTreeWidgetItem(self.tree)
            fileName.setText(0, i)
            fileName.setFlags(fileName.flags() | Qt.ItemIsTristate | Qt.ItemIsUserCheckable)
            fileName.setCheckState(0, Qt.Checked)
            fileCategory.addChild(fileName)
        self.layout.addWidget(self.tree, 2, 0)

        self.tree.itemChanged.connect(self.handle_item_changed)

    def update_local_tree(self):
        lcl.file_list = os.listdir('local')
        lcl.file_list = [i for i in lcl.file_list if not i.endswith('.DS_Store')]
        lcl.active_files = lcl.file_list.copy()
        print(lcl.file_list, lcl.active_files)

        self.init_local_tree()

    def add_files_to_local(self):
        filenames = QFileDialog.getOpenFileNames(self, 'Select files', '/')
        print(filenames)

        for item in filenames[0]:
            shutil.copy(item, './local')

        self.update_local_tree()


    def get_tree_path(self, item):
        path = []
        while item is not None:
            path.append(str(item.text(0)))
            item = item.parent()
        return '/'.join(reversed(path))

    def handle_item_changed(self, item, column):
        # чек бокс. функция выбора
        if item.flags() & Qt.ItemIsUserCheckable:
            path = self.get_tree_path(item)
            if item.checkState(0) == Qt.Checked:
                if item.text(0) in chm.method_name:
                    if item.text(0) not in chm.active_methods:
                        chm.active_methods.append(item.text(0))
                else:
                    if item.text(0) in lcl.file_list:
                        if item.text(0) not in lcl.active_files:
                            lcl.active_files.append(item.text(0))
            else:
                if item.text(0) in chm.method_name:
                    if item.text(0) in chm.active_methods:
                        chm.active_methods.remove(item.text(0))
                else:
                    if item.text(0) in lcl.file_list:
                        if item.text(0) in lcl.active_files:
                            lcl.active_files.remove(item.text(0))

    def create_graph(self):
        # окно с графиком по результатам анализа таблицы
        graphWindow = GraphWindow(self.data)
        # окон может быть произвольное количество, поэтому хранятся они в виде списка
        self.graphs.append(graphWindow)
        self.graphs[-1].show()

    def save_data(self):
        text, ok = QInputDialog.getText(self, 'Save report', 'Enter name:')
        if ok:
            # экспорт в Excel
            self.data.to_excel('./reports/' + text +'.xlsx', sheet_name = self.level)

    def hide_widget(self):
        print(self.pr)

    def center(self):
        # отрисовка окна приложения по центру экрана
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def convert_pandas_to_widget(self, widget, data):
        # адаптация Pandas dataframe в таблицу QT для отображения в интерфейсе
        headers = data.columns.values.tolist()
        table = widget
        table.clear()
        table.setColumnCount(len(headers))
        for i, row in data.iterrows():
            table.setRowCount(table.rowCount() + 1)
            for j in range(table.columnCount()):
                table.setItem(i, j, QTableWidgetItem(str(row[j])))
        table.resizeColumnsToContents()

    def update_table(self, data):
        # обновление отображаемых в таблице интерфейса данных
        self.convert_pandas_to_widget(self.table, data)
        self.table.setHorizontalHeaderLabels(list(data.columns.values))
        self.table.setWordWrap(True)
        self.table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)

    def analyze_dataframe(self):

        lcl.import_active_files()

        if (lcl.local_dataframe.shape[0] != 0) and (lcl.local_dataframe.shape[1] != 0):
            print(len(lcl.local_dataframe.index))
            print(len(chm.active_methods))

            chm.start_scripts()
            self.data = chm.result_dataframe
            self.statusBar().showMessage('Rendering table')
            print(self.data)
            self.update_table(self.data)
            chm.result_dataframe = pd.DataFrame()
        else:
            pass

        self.statusBar().showMessage('Ready')

if __name__ == '__main__':
    # инициализация класса приложения
    app = QApplication(sys.argv)
    # передача приложению кастомной иконки
    path = os.path.join(os.path.dirname(sys.modules[__name__].__file__), './ext/style/icon_4.png')
    app.setWindowIcon(QIcon(path))
    
    lcl = LocalData()
    chm = CheckMethod()
    window = App()

    sys.exit(app.exec_())