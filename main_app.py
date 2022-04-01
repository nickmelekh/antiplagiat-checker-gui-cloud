import os
import sys
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

class Dropbox():
    def __init__(self):
        self.accesstoken = dropbox_token
        self.target = ''
        self.dbx = dropbox.Dropbox(self.accesstoken)
        self.folder_list = self.get_directory_names(self.target)
        self.dir = {}
        self.queue = []
        self.dataframe = []
        self.dbx_dir()

    def get_directory_names(self, path_):
        folder_list = []
        response = self.dbx.files_list_folder(path_)
        for i in range(len(response.entries)):
            folder_list.append(response.entries[i].name)
        return folder_list

    def dbx_dir(self):
        self.dir = {}
        for i in self.get_directory_names(self.target):
            self.dir[i] = {}
            for j in self.get_directory_names(self.target + '/' + i):
                if 'controlwork' in j:
                    self.dir[i][j] = []
                    for k in self.get_directory_names(self.target + '/' + i + '/' + j + '/result'):
                        if 'ipynb' in k:
                            task = {}
                            task['task_name'] = k
                            task['active_flag'] = 0
                            self.dir[i][j].append(task)
        print(self.dir)

    def print_directory_names(self, path_):
        print(self.get_directory_names(path_))

    def download(self, dbx, folder, subfolder, name):
        path = '/%s/%s/%s' % (folder, subfolder.replace(os.path.sep, '/'), name)
        while '//' in path:
            path = path.replace('//', '/')
        try:
            md, res = dbx.files_download(path)
        except dropbox.exceptions.HttpError as err:
            print('*** HTTP error', err)
            return None
        data = res.content
        return data

    def load_json(self, filename):
        with open(filename, 'rt', encoding='utf-8') as f:
            return json.load(f)

    def get_solution(self, notebook, task):
        flag = 0
        lst = []
        for cell in notebook['cells']:
            if flag == 0:
                if is_task_cell(cell) and cell['metadata']['task'] == task:
                    flag = 1
            elif flag == 1:
                if cell['cell_type'] == 'code':
                    lst.append(cell)
                else:
                    break
        return lst

    def count_students(self, notebook):
        student_number = 0
        for i in range(len(notebook['cells'])):
            if str(list(notebook['cells'][i]['metadata'].keys()))[2:-2] == 'hash':
                student_number += 1
        return student_number

    def normalize_text(self, code):
        # code - содержание ячейки из ноутбука
        if type(code) == str:
            code = re.sub('^\s+|\t|\r|\\n|\s{2,}|\s+$', '', code)
            code = re.split('[- : ( ) + \\ \n \' "]', code)
            code = list(filter(None, code))
            code = [(el.strip()) for el in code]
        return code

    def split_notebook(self, notebook):
        task_dict_by_student = {}
        code = []
        i = 1
        student_number = self.count_students(notebook)
        while student_number > 0:
            if notebook['cells'][i]['cell_type'] == 'markdown':
                hash_student = str(list(notebook['cells'][i]['metadata'].values()))[2:-2]
                # name_student = notebook['cells'][i]['source'][0]
                if notebook['cells'][i + 1]['cell_type'] == 'code':
                    code = str(notebook['cells'][i + 1]['source'])[2:-2]
                try:
                    if notebook['cells'][i + 2]['cell_type']== 'code':
                        code += ' '
                        code += str(notebook['cells'][i + 2]['source'])[2:-2]
                except:
                    pass
                task_dict_by_student[hash_student] = self.normalize_text(code)
                student_number -= 1
            i += 1
        return task_dict_by_student

    def download_checked_item(self):
        queue = []
        for group in self.dir.keys():
            for controlwork in self.dir[group].keys():
                for task in self.dir[group][controlwork]:
                    package = []
                    if task['active_flag'] == 1:
                        package.append(group)
                        package.append(controlwork)
                        package.append(task['task_name'])
                        queue.append(package)
        self.queue = queue

        queue_dataframe = pd.DataFrame()

        for package in self.queue:

            folder = '/' + package[0] + '/'
            subfolder = '/' + package[1] + '/result/'
            task = package[2]
            notebook = json.loads(str(dbx.download(dbx.dbx, folder, subfolder, task),'utf-8'))
            data = dbx.split_notebook(notebook)
            package_dataframe = pd.Series(data).rename_axis('hash_value').reset_index(name = 'task_code')
            queue_dataframe = queue_dataframe.append(package_dataframe, ignore_index = True)

        return queue_dataframe

class CheckMethod():
    def __init__(self):
        self.methods_list = [o for o in getmembers(check_scripts) if isfunction(o[1])]
        # список доступных методов
        self.method_name = []
        self.active_methods = []
        for i in range(len(self.methods_list)):
            self.method_name.append(self.methods_list[i][0])
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
        for method in self.active_methods:
            print('Method_name:', method)
            function = getattr(check_scripts, method) 
            self.result_dataframe = self.merge_results(self.result_dataframe, function(dbx.dataframe))

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
        # self.table.setHorizontalHeaderLabels(list(data.columns.values))
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
        startAnalyze = QAction(QIcon('./ext/style/analyze.png'), 'Analyze', self)
        startAnalyze.triggered.connect(self.analyze_dataframe)
        tb.addAction(startAnalyze)

        downloadItems = QAction(QIcon('./ext/style/net_1.png'), 'Download', self)
        downloadItems.triggered.connect(self.download_checked_item_user)
        tb.addAction(downloadItems)

        createGraph = QAction(QIcon('./ext/style/graph.png'), 'Graph', self)
        createGraph.triggered.connect(self.create_graph)
        tb.addAction(createGraph)

        saveResults = QAction(QIcon('./ext/style/save.png'), 'Save', self)
        saveResults.triggered.connect(self.save_data)
        tb.addAction(saveResults)

        exitAct = QAction(QIcon('./ext/style/close.png'), 'Exit', self)
        exitAct.setShortcut('Ctrl+Q')
        exitAct.triggered.connect(qApp.quit)
        tb.addAction(exitAct)

        # список файлов в директориях Dropbox'а
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(['Dropbox:'])
        for i in dbx.dir.keys():
            courseName = QTreeWidgetItem(self.tree)
            courseName.setText(0, i)
            courseName.setFlags(courseName.flags() | Qt.ItemIsTristate | Qt.ItemIsUserCheckable)
            for j in dbx.dir[i]:
                controlworkNumber = QTreeWidgetItem(courseName)
                controlworkNumber.setFlags(controlworkNumber.flags() | Qt.ItemIsTristate | Qt.ItemIsUserCheckable)
                controlworkNumber.setText(0, j)
                controlworkNumber.setCheckState(0, Qt.Unchecked)
                for k in dbx.dir[i][j]:
                    taskNumber = QTreeWidgetItem(controlworkNumber)
                    taskNumber.setFlags(taskNumber.flags() | Qt.ItemIsUserCheckable)
                    taskNumber.setText(0, k['task_name'])
                    taskNumber.setCheckState(0, Qt.Unchecked)

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
        self.tree.itemChanged.connect(self.handle_item_changed)

        # результирующая таблица
        self.table = QTableWidget()
        self.convert_pandas_to_widget(self.table, self.data)
        self.table.setHorizontalHeaderLabels(str(i) for i in range(self.data.shape[1]))
        self.table.horizontalHeader().setVisible(True)

        # развертка окна приложения
        self.layout.addWidget(self.method_tree, 1, 0)
        self.layout.setRowStretch(1, 1)
        self.layout.addWidget(self.tree, 2, 0)
        self.layout.setRowStretch(2, 2)
        self.layout.addWidget(self.table, 1, 1, 3, 3)
        self.layout.setColumnStretch(1, 1)

        self.show()

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
                    if ('ipynb' in path):
                        path_copy = path.split('/')
                        print(path_copy)
                        if dbx.dir[path_copy[0]][path_copy[1]][int(path_copy[2][:-6].split('_')[-1])]['active_flag'] == 0:
                            dbx.dir[path_copy[0]][path_copy[1]][int(path_copy[2][:-6].split('_')[-1])]['active_flag'] = 1
                        else:
                            dbx.dir[path_copy[0]][path_copy[1]][int(path_copy[2][:-6].split('_')[-1])]['active_flag'] = 0
            else:
                if item.text(0) in chm.method_name:
                    if item.text(0) in chm.active_methods:
                        chm.active_methods.remove(item.text(0))
                else:
                    if ('ipynb' in path):
                        path_copy = path.split('/')
                        if dbx.dir[path_copy[0]][path_copy[1]][int(path_copy[2][:-6].split('_')[-1])]['active_flag'] == 0:
                            dbx.dir[path_copy[0]][path_copy[1]][int(path_copy[2][:-6].split('_')[-1])]['active_flag'] = 1
                        else:
                            dbx.dir[path_copy[0]][path_copy[1]][int(path_copy[2][:-6].split('_')[-1])]['active_flag'] = 0

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

    def download_checked_item_user(self):
        # загрузка из Dropbox только отмеченных из интерфейса файлов
        dbx.dataframe = dbx.download_checked_item()
        self.update_table(dbx.dataframe)

    def analyze_dataframe(self):
        
        print('Downloading files from dropbox')

        self.download_checked_item_user()
        self.statusBar().showMessage('Download complete')

        if (dbx.dataframe.shape[0] != 0) and (dbx.dataframe.shape[1] != 0):
            print(len(dbx.dataframe.index))
            print(len(chm.active_methods))

            chm.start_scripts()
            self.data = chm.result_dataframe
            self.statusBar().showMessage('Rendering table')
            self.update_table(self.data)
            chm.result_dataframe = pd.DataFrame()
        else:
            pass

        self.statusBar().showMessage('Ready')

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

if __name__ == '__main__':
    # инициализация класса приложения
    app = QApplication(sys.argv)
    # передача приложению кастомной иконки
    path = os.path.join(os.path.dirname(sys.modules[__name__].__file__), './ext/style/icon_4.png')
    app.setWindowIcon(QIcon(path))
    
    dbx = Dropbox()
    chm = CheckMethod()
    window = App()

    sys.exit(app.exec_())