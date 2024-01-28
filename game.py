from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtWidgets import QApplication, QMainWindow

import sys


class Cell(QtWidgets.QPushButton):

    def mousePressEvent(self, QMouseEvent):
        if not self._opened:
            if QMouseEvent.button() == QtCore.Qt.LeftButton:
                self._click('left')
            elif QMouseEvent.button() == QtCore.Qt.RightButton:
                self._click('right')

    def __init__(self, window, game, pos_x, pos_y, size):
        super(Cell, self).__init__(window)

        self._window = window
        self.game = game
        self._pos_x = pos_x
        self._pos_y = pos_y
        self._size = size
        self._opened = False
        self._marked = False
        self._role = 'bomb'

        self.setGeometry(self._pos_x, self._pos_y, self._size, self._size)
        self.setCursor(QtCore.Qt.PointingHandCursor)

        self._set_image()

    def _click(self, click):
        if click == 'left':
            self._opened = True
            self.setCursor(QtCore.Qt.ArrowCursor)
            self._change_image(0)
            if (self._marked):
                self.game.change_amound_marked(False)
        elif click == 'right':
            self._marked = not self._marked
            if self._marked:
                self.game.change_amound_marked(True)
                self._change_image(10)
            else:
                self.game.change_amound_marked(False)
                self._change_image(11)


    def _set_image(self):
        img = QtGui.QPixmap('image/cell/cell_11.bmp')
        img = img.scaled(self._size, self._size)
        self.label = QtWidgets.QLabel(self)
        self.label.resize(self._size, self._size)
        self.label.setPixmap(img)

    def _change_image(self, id):
        img = QtGui.QPixmap(f'image/cell/cell_{id}.bmp')
        img = img.scaled(self._size, self._size)
        self.label.setPixmap(img)


class Game:
    def __init__(self, window):
        self.window = window

        self.level = [20, 12, 3]
        self._cellSize = 35

        self._cell_MaxX = self.window.getSize()[0] / self._cellSize
        self._cell_MaxY = self.window.getSize()[1] / self._cellSize

        self._cells = []
        self._amound_marked = 0

        self._showCell()

    def _showCell(self):
        if not self._check_level():
            return False

        for i in range(self.level[1]):
            for j in range(self.level[0]):
                x = self.window.getPosZero()[0] + (self._cellSize * j)
                y = self.window.getPosZero()[1] + (self._cellSize * i)

                cell = Cell(self.window, self, x, y, self._cellSize)
                self._cells.append(cell)


    def _check_level(self):
        x = self.level[0] > self._cell_MaxX
        y = self.level[1] > self._cell_MaxY
        bomb = self.level[2] > (self.level[0] * self.level[1])

        if x or y or bomb:
            return False
        else:
            return True

    def change_amound_marked(self, adding):
        if adding:
            self._amound_marked += 1
        else:
            self._amound_marked -= 1

        print(self._amound_marked)


class Window(QMainWindow):
    def __init__(self):
        super(Window, self).__init__()

        self.title = 'Minesweeper';

        self._width = 700
        self._height = 450
        self._posXZero = 0
        self._posYZero = 30

        self.setWindowTitle(self.title)
        self.setGeometry(720, 400, self._width, self._height)

        self._createMenu()
        self._createBody()

    def _createBody(self):
        self.body = QtWidgets.QWidget(self)

        body_width = self._width
        body_height = self._height - self._posYZero;
        self.body.setGeometry(self._posXZero, self._posYZero, body_width, body_height)
        self.body.setStyleSheet('background-color: grey;')

    def _createMenu(self):
        menu = self.menuBar()
        game = menu.addMenu('Игра')
        settings = menu.addMenu('Настройки')
        aboud = menu.addMenu('Oб проекте')

        play = game.addAction(QtWidgets.QAction('Играть', self))
        game.addAction(QtWidgets.QAction('Заново', self))
        game.addAction(QtWidgets.QAction('Новый уровень', self))




    def getSize(self):
        w = self._width - self._posXZero
        h = self._height - self._posYZero
        return [w, h]

    def getPosZero(self):
        return [self._posXZero, self._posYZero]





def application():
    app = QApplication(sys.argv)
    window = Window()
    game = Game(window)

    window.show()
    sys.exit(app.exec_())

if (__name__ == '__main__'):
    application()
