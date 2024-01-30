from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtWidgets import QApplication, QMainWindow
from random import randint

import sys


class Cell(QtWidgets.QPushButton):

    def mousePressEvent(self, QMouseEvent):
        if not self._opened and self.game.game:
            if QMouseEvent.button() == QtCore.Qt.LeftButton:
                self._click_left()
            elif QMouseEvent.button() == QtCore.Qt.RightButton:
                self._click_right()

    def __init__(self, window, game, pos_x, pos_y, size):
        super(Cell, self).__init__(window)

        self._window = window
        self.game = game
        self._pos_x = pos_x
        self._pos_y = pos_y
        self._size = size
        self._opened = False
        self._marked = False
        self._role = 'empty'

        self.setGeometry(self._pos_x, self._pos_y, self._size, self._size)
        self.setCursor(QtCore.Qt.PointingHandCursor)

        self._set_image()

    def _click_left(self):
        self._opened = True
        self.setCursor(QtCore.Qt.ArrowCursor)

        if self._role == 'empty':
            self._change_image(0)
        elif self._role == 'bomb':
            self.game.defeat()
        else:
            print('error Cell:_click_left')

        if (self._marked):
            self.game.change_amound_marked(False)

    def _click_right(self):
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

    def setRole(self, role):
        self._role = role
        # self._change_image(9)

    def kill(self):
        if (self._role == 'bomb'):
            self._change_image(9)
        else:
            self.setCursor(QtCore.Qt.ArrowCursor)


class Game:
    def __init__(self, window):
        self.window = window

        self.game = True
        self.level = [5, 5, 3]
        self._cellSize = 35

        self._cell_MaxX = self.window.getSize()[0] / self._cellSize
        self._cell_MaxY = self.window.getSize()[1] / self._cellSize

        self._cells = []
        self._bombs = []
        self._amound_marked = 0

        self._createCell()
        self._createBomb()

    def _createCell(self):
        if not self._check_level():
            return False

        for i in range(self.level[1]):
            for j in range(self.level[0]):
                # x = self.window.getPosZero()[0] + (self._cellSize * j)
                # y = self.window.getPosZero()[1] + (self._cellSize * i)

                x = self._cellSize * j
                y = self._cellSize * i

                cell = Cell(self.window.body, self, x, y, self._cellSize)
                self._cells.append(cell)

    def _createBomb(self):
        for i in range(self.level[2]):
            last = len(self._cells) - 1
            index = randint(0, last)
            self._cells[index].setRole('bomb')
            self._bombs.append(index)


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

    def defeat(self):
        self.game = False
        for cell in self._cells:
            cell.kill()
        label = QtWidgets.QLabel('Game Over', self.window.body)
        label.setStyleSheet('color: red;font-size: 32px;background: none')
        label.move(0, 0)
        # label.show()


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
