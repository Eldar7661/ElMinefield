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

    def __init__(self, field, game, pos_x, pos_y, size):
        super(Cell, self).__init__(field)

        self._field = field
        self.game = game

        self._pos_x = pos_x
        self._pos_y = pos_y
        self._size = size

        self._level = 0
        self._opened = False
        self._marked = False
        self._role = 'empty'
        self.img = 'image'
        self.imgLabel = 'conteiner'

        self.setGeometry(self._pos_x, self._pos_y, self._size, self._size)
        self.setCursor(QtCore.Qt.PointingHandCursor)

        self._set_image()

    def _click_left(self):
        self._opened = True
        self.setCursor(QtCore.Qt.ArrowCursor)

        if self._role == 'empty':
            self._change_image(self._level)
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

    # def resizeEvent(self, event):
    #     self.setIconSize(event.size())
    #     super().resizeEvent(event)

    def _set_image(self):
        self.img = QtGui.QPixmap('image/cell/cell_11.bmp')
        self.imgLabel = QtWidgets.QLabel(self)
        self._adjustment_image()

    def _change_image(self, id):
        self.img = QtGui.QPixmap(f'image/cell/cell_{id}.bmp')
        self._adjustment_image()

    def _adjustment_image(self):
        self.imgLabel.resize(self._size, self._size)
        self.imgLabel.setPixmap(self.img.scaled(self._size, self._size))

    def setRole(self, role):
        self._change_image(9)
        if self._role == 'bomb':
            return False
        else:
            self._role = role
            return True

    def change_size(self, size, posX, posY):
        self._size = size
        self.setFixedSize(self._size, self._size)
        self.move(posX, posY)
        self._adjustment_image()

    def kill(self):
        if (self._role == 'bomb'):
            self._change_image(9)
        else:
            self.setCursor(QtCore.Qt.ArrowCursor)

    def addLevel(self):
        self._level += 1


class Game:
    def __init__(self, window):
        self.window = window

        self.game = True
        self.field = 'obj'
        self.level = [26, 26, 600]
        self._cellMinSize = 35
        self._cellSize = 35

        self._cell_MaxX = 0
        self._cell_MaxY = 0

        self._cells = []
        self._bombs = []
        self._amound_marked = 0

        self._createField()
        self._calcCellAmountMax()
        if self._createCell():
            self._createBomb()
            self._calcPositionBomb()
        else:
            print(f'Error: maximum amount cells\nx: {self._cell_MaxX}, y: {self._cell_MaxY}')
        self.calcMinSizeWindow()

    def _createField(self):
        self.field = QtWidgets.QWidget(self.window.body)

    def _createCell(self):
        if not self._check_level():
            return False

        for i in range(self.level[1]):
            self._cells.append([])
            for j in range(self.level[0]):
                x = self._cellSize * j
                y = self._cellSize * i

                cell = Cell(self.field, self, x, y, self._cellSize)
                self._cells[i].append(cell)

        return True

    def _createBomb(self):
        countBomb = 0
        maxIndexX = len(self._cells[0]) - 1
        maxIndexY = len(self._cells) - 1

        while True:
            indexX = randint(0, maxIndexX)
            indexY = randint(0, maxIndexY)
            if self._cells[indexY][indexX].setRole('bomb'):
                self._bombs.append([indexY, indexX])
                countBomb += 1


            if countBomb == self.level[2]:
                break

    def _calcPositionBomb(self):
        maxIndexX = len(self._cells[0]) - 1
        maxIndexY = len(self._cells) - 1

        for bomb in self._bombs:
                i = bomb[0]
                j = bomb[1]
                # Corner
                if i == 0 and j == 0:
                    self._addLevelCells('Corner_NW', i, j)
                elif i == 0 and j == maxIndexX:
                    self._addLevelCells('Corner_NE', i, j)
                elif i == maxIndexY and j == 0:
                    self._addLevelCells('Corner_SW', i, j)
                elif i == maxIndexY and j == maxIndexX:
                    self._addLevelCells('Corner_SE', i, j)

                # Ribs
                elif i == 0 and j > 0 and j < maxIndexX:
                    self._addLevelCells('Ribs_N', i, j)
                elif i > 0 and i < maxIndexY and j == maxIndexX:
                    self._addLevelCells('Ribs_E', i, j)
                elif i == maxIndexY and j > 0 and j < maxIndexX:
                    self._addLevelCells('Ribs_S', i, j)
                elif i > 0 and i < maxIndexY and j == 0:
                    self._addLevelCells('Ribs_W', i, j)
                else:
                    self._addLevelCells('Center', i, j)

    def _addLevelCells(self, pos, posY, posX):
        if pos == 'Corner_NW':
            self._cells[0][posX + 1].addLevel()
            self._cells[posY + 1][0].addLevel()
            self._cells[posY + 1][posX + 1].addLevel()
        elif pos == 'Corner_NE':
            self._cells[0][posX - 1].addLevel()
            self._cells[posY + 1][posX - 1].addLevel()
            self._cells[posY + 1][posX].addLevel()
        elif pos == 'Corner_SW':
            self._cells[posY - 1][posX].addLevel()
            self._cells[posY][posX + 1].addLevel()
            self._cells[posY - 1][posX + 1].addLevel()
        elif pos == 'Corner_SE':
            self._cells[posY - 1][posX].addLevel()
            self._cells[posY][posX - 1].addLevel()
            self._cells[posY - 1][posX - 1].addLevel()


        elif pos == 'Ribs_N':
            self._cells[posY][posX + 1].addLevel()
            self._cells[posY][posX - 1].addLevel()
            self._cells[posY + 1][posX].addLevel()
            self._cells[posY + 1][posX + 1].addLevel()
            self._cells[posY + 1][posX - 1].addLevel()
        elif pos == 'Ribs_E':
            self._cells[posY + 1][posX].addLevel()
            self._cells[posY - 1][posX].addLevel()
            self._cells[posY][posX - 1].addLevel()
            self._cells[posY - 1][posX - 1].addLevel()
            self._cells[posY + 1][posX - 1].addLevel()
        elif pos == 'Ribs_S':
            self._cells[posY][posX + 1].addLevel()
            self._cells[posY][posX - 1].addLevel()
            self._cells[posY - 1][posX].addLevel()
            self._cells[posY - 1][posX + 1].addLevel()
            self._cells[posY - 1][posX - 1].addLevel()
        elif pos == 'Ribs_W':
            self._cells[posY + 1][posX].addLevel()
            self._cells[posY - 1][posX].addLevel()
            self._cells[posY][posX + 1].addLevel()
            self._cells[posY + 1][posX + 1].addLevel()
            self._cells[posY - 1][posX + 1].addLevel()

        elif pos == 'Center':
            self._cells[posY - 1][posX - 1].addLevel()
            self._cells[posY - 1][posX].addLevel()
            self._cells[posY - 1][posX + 1].addLevel()
            self._cells[posY][posX - 1].addLevel()
            self._cells[posY][posX + 1].addLevel()
            self._cells[posY + 1][posX - 1].addLevel()
            self._cells[posY + 1][posX].addLevel()
            self._cells[posY + 1][posX + 1].addLevel()

        else:
            print('Error _addLevelCells()')

    def _check_level(self):
        x = self.level[0] > self._cell_MaxX
        y = self.level[1] > self._cell_MaxY
        bomb = self.level[2] > (self.level[0] * self.level[1])

        if x or y or bomb:
            return False
        else:
            return True

    def changeSizeWindow(self):
        self._calcCellSize()
        self._cell_change_size()
        # self._calcCellAmountMax()

    def _fieldCalcSize(self):
        fieldWidth = self._cellSize * self.level[0]
        fieldHeight = self._cellSize * self.level[1]
        alignHCenter = int((self.window.body.size().width() / 2) - (fieldWidth / 2))

        self.field.setGeometry(alignHCenter, 0, fieldWidth, fieldHeight)

    def _cell_change_size(self):
        countX = 0
        countY = 0
        for row in self._cells:
            for cell in row:
                posX = countX * self._cellSize
                posY = countY * self._cellSize
                cell.change_size(self._cellSize, posX, posY)
                countX += 1

                if (countX == self.level[0]):
                    countX = 0
                    countY += 1

    def _calcCellSize(self):
        cellWidth = self.window.body.size().width() / self.level[0]
        cellHeight = self.window.body.size().height() / self.level[1]
        cellFitsToBody_width = (self.level[0] * self._cellSize) <= (self.window.body.size().width() - 1)
        cellFitsToBody_height = (self.level[1] * self._cellSize) <= (self.window.body.size().height() - 1)

        # if (cellFitsToBody_width) or (not cellFitsToBody_height):
            # self._cellSize = int(cellHeight)
        if cellFitsToBody_width and cellFitsToBody_height:
            if (cellWidth <= cellHeight):
                self._cellSize = int(cellWidth)
                self._fieldCalcSize()
            else:
                self._cellSize = int(cellHeight)
                self._fieldCalcSize()
        if not cellFitsToBody_width:
            self._cellSize = int(cellWidth)
            self._fieldCalcSize()
        if not cellFitsToBody_height:
            self._cellSize = int(cellHeight)
            self._fieldCalcSize()

    def _calcCellAmountMax(self):
        self._cell_MaxX = int(self.window.size().width() / self._cellMinSize)
        self._cell_MaxY = int(self.window.size().height() / self._cellMinSize)

    def calcMinSizeWindow(self):
        min_width = self._cellMinSize * self.level[0]
        min_height = self._cellMinSize * self.level[1]
        self.window.setMinSize(min_width, min_height)


    def change_amound_marked(self, adding):
        if adding:
            self._amound_marked += 1
        else:
            self._amound_marked -= 1

        print(self._amound_marked)

    def defeat(self):
        self.game = False
        for row in self._cells:
            for cell in row:
                cell.kill()

        label = QtWidgets.QLabel('Game Over', self.window.body)
        label.setStyleSheet('color: red;font-size: 32px;background: none')
        label.move(0, 0)
        label.show()


class Window(QMainWindow):
    resized = QtCore.pyqtSignal()

    def resizeEvent(self, event):
        self.resized.emit()
        return super(Window, self).resizeEvent(event)

    def __init__(self):
        super(Window, self).__init__()

        self._width = 935
        self._height = 935
        self._posXZero = 0
        self._posYZero = 30
        self.game = 'obj'
        self.body = 'Widget'

        self.title = 'Minesweeper';
        self.resized.connect(self._changeSize)
        self.setWindowTitle(self.title)
        self.setGeometry(720, 150, self._width, self._height)

        self._createMenu()
        self._createBody()

    def _changeSize(self):
        self._width = self.size().width();
        self._height = self.size().height();
        self.body.setFixedSize(self._width, self._height - self._posYZero)
        self.game.calcMinSizeWindow()
        self.game.changeSizeWindow()

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

    def setMinSize(self, w, h):
        self.setMinimumSize(w + self._posXZero, h + self._posYZero)

    def setGame(self, game):
        self.game = game

    # def getPosZero(self):
    #     return [self._posXZero, self._posYZero]





def application():
    app = QApplication(sys.argv)
    window = Window()
    game = Game(window)
    window.setGame(game)

    window.show()
    sys.exit(app.exec_())

if (__name__ == '__main__'):
    application()
