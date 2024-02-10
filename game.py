from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtWidgets import QApplication, QMainWindow

from random import randint
from threading import Timer
import sys


class Cell(QtWidgets.QPushButton):

    def mousePressEvent(self, QMouseEvent):

        if not self._game.started:
            self._game.start()

        if not self._opened and self._game.game:
            if QMouseEvent.button() == QtCore.Qt.LeftButton:
                self.opening()
            elif QMouseEvent.button() == QtCore.Qt.RightButton:
                self._set_mark()

    def __init__(self, game, field, size):
        super(Cell, self).__init__(field)

        self._game = game

        # self._pos_x = pos_x
        # self._pos_y = pos_y
        self._size = size

        self._amountBombAround = 0
        self._opened = False
        self._markedFlag = False
        self._markedSupposed = False
        self._role = 'empty'
        self.img = QtGui.QPixmap('image/cell/cell_11.bmp')
        self.imgLabel = QtWidgets.QLabel(self)

        self.setCursor(QtCore.Qt.PointingHandCursor)

        self._image_adjustment()

    def _set_mark(self):

        if self._markedFlag:
            self._markedFlag = False
            self._markedSupposed = True
            self._game.set_amount_marked(False)
            self._set_image(10)

        elif self._markedSupposed:
            self._markedSupposed = False
            self._set_image(11)

        else:
            self._markedFlag = True
            self._game.set_amount_marked(True)
            self._set_image(9)

    def _set_image(self, id):

        self.img = QtGui.QPixmap(f'image/cell/cell_{id}.bmp')
        self._image_adjustment()

    def _image_adjustment(self):

        self.imgLabel.resize(self._size, self._size)
        self.imgLabel.setPixmap(self.img.scaled(self._size, self._size))

    def set_role(self, role):
        self._set_image(12)
        if self._role == 'bomb':
            return False
        else:
            self._role = role
            return True

    def count_bomb_around(self):

        self._amountBombAround += 1

    def set_geometry(self, size, posX, posY):

        self._size = size
        self.setGeometry(posX, posY, self._size, self._size)
        self.show()
        self._image_adjustment()

    def opening(self):

        if self._opened:
            return False

        self._opened = True
        self.setCursor(QtCore.Qt.ArrowCursor)
        self._game.cell_opening(self._role)

        if (self._markedFlag):
            self._game.set_amount_marked(False)

        if self._role == 'empty':
            self._set_image(self._amountBombAround)
            if self._amountBombAround == 0:
                self._game.opening_around_cells(self)

    def set_cursor_default(self):

        self.setCursor(QtCore.Qt.ArrowCursor)

    def explode(self):

            self._set_image(12)

    def get_opened(self):
        return self._opened

class Game:

    def __init__(self, window):

        self.window = window

        self._cellMinSize = 35
        self._cellMaxAmountX = 0
        self._cellMaxAmountY = 0
        self._cellSize = 35

        self.level = [10, 10, 20]
        self.victoryAmountCellOpened = (self.level[0] * self.level[1]) - self.level[2]
        self._calc_min_size_field()


        self._stopwatch = QtCore.QTimer()
        self._stopwatch.setInterval(1000)
        self._stopwatch.timeout.connect(self._tick)

        self._cell_calc_max_amount()
        self.restart()

    def restart(self):

        self.game = True
        self.started = False
        self._cellsGeneralSize = 0

        self._stopwatch.stop()
        self._time = 0
        self._amountMarked = 0
        self._cellAmountOpened = 0

        try:
            for row in self._cells:
                for cell in row:
                    cell.deleteLater()
        except:
            pass

        self._cells = []
        self._bombs = []

        if self._cell_create():
            self._bomb_create()
            self._cell_calc_size()
            self._cell_set_geometry()
        else:
            print(f'Error: maximum amount cells\nx: {self._cellMaxAmountX}, y: {self._cellMaxAmountY}')

        self.window.set_header_stopwatch(0)
        self.window.set_header_count_marked(0)
        self.window.set_header_btn_image('default')

    def _cell_create(self):

        if not self._chec_level():
            return False

        for i in range(self.level[1]):
            self._cells.append([])
            for j in range(self.level[0]):

                cell = Cell(self, self.window.field, self._cellSize)
                self._cells[i].append(cell)

        return True

    def _cell_calc_position(self, cell):

        amountCellX = len(self._cells[0]) - 1
        amountCellY = len(self._cells) - 1

        for i in range(len(self._cells)):
            for j in range(len(self._cells[0])):
                if self._cells[i][j] == cell:
                    pos_x = j
                    pos_y = i
                    break
            if self._cells[i][j] == cell:
                break
        # Corner
        if pos_y == 0 and pos_x == 0:
            return ['Corner_NW', pos_y, pos_x]
        elif pos_y == 0 and pos_x == amountCellX:
            return ['Corner_NE', pos_y, pos_x]
        elif pos_y == amountCellY and pos_x == 0:
            return ['Corner_SW', pos_y, pos_x]
        elif pos_y == amountCellY and pos_x == amountCellX:
            return ['Corner_SE', pos_y, pos_x]

        # Ribs
        elif pos_y == 0 and pos_x > 0 and pos_x < amountCellX:
            return ['Ribs_N', pos_y, pos_x]
        elif pos_y > 0 and pos_y < amountCellY and pos_x == amountCellX:
            return ['Ribs_E', pos_y, pos_x]
        elif pos_y == amountCellY and pos_x > 0 and pos_x < amountCellX:
            return ['Ribs_S', pos_y, pos_x]
        elif pos_y > 0 and pos_y < amountCellY and pos_x == 0:
            return ['Ribs_W', pos_y, pos_x]
        else:
            return ['Center', pos_y, pos_x]

    def _cell_calc_around_cells(self, position):

        aroundCell = []
        pos = position[0]
        posY = position[1]
        posX = position[2]

        if pos == 'Corner_NW' or pos == 'Corner_SW' or pos == 'Ribs_N' or pos == 'Ribs_S' or pos == 'Ribs_W' or pos == 'Center':
            aroundCell.append(self._cells[posY][posX + 1])
        if pos == 'Corner_NE' or pos == 'Corner_SE' or pos == 'Ribs_N' or pos == 'Ribs_S' or pos == 'Ribs_E' or pos == 'Center':
            aroundCell.append(self._cells[posY][posX - 1])
        if pos == 'Corner_SW' or pos == 'Ribs_S' or pos == 'Ribs_W' or pos == 'Center':
            aroundCell.append(self._cells[posY - 1][posX + 1])
        if pos == 'Corner_SW' or pos == 'Corner_SE' or pos == 'Ribs_E' or pos == 'Ribs_S' or pos == 'Ribs_W' or pos == 'Center':
            aroundCell.append(self._cells[posY - 1][posX])
        if pos == 'Corner_SE' or pos == 'Ribs_E' or pos == 'Ribs_S' or pos == 'Center':
            aroundCell.append(self._cells[posY - 1][posX - 1])
        if pos == 'Corner_NE' or pos == 'Ribs_N' or pos == 'Ribs_E' or pos == 'Center':
            aroundCell.append(self._cells[posY + 1][posX - 1])
        if pos == 'Corner_NW' or pos == 'Corner_NE' or pos == 'Ribs_N' or pos == 'Ribs_E' or pos == 'Ribs_W' or pos == 'Center':
            aroundCell.append(self._cells[posY + 1][posX])
        if pos == 'Corner_NW' or pos == 'Ribs_N' or pos == 'Ribs_W' or pos == 'Center':
            aroundCell.append(self._cells[posY + 1][posX + 1])

        return aroundCell

    def _cell_calc_size(self):

        cellWidth = self.window.field.size().width() / self.level[0]
        cellHeight = self.window.field.size().height() / self.level[1]
        cellFitsToBodyX = (self.level[0] * self._cellSize) < (self.window.field.size().width() + 1)
        cellFitsToBodyY = (self.level[1] * self._cellSize) < (self.window.field.size().height() + 1)

        if cellFitsToBodyX and cellFitsToBodyY:
            if (cellWidth <= cellHeight):
                self._cellSize = int(cellWidth)
            else:
                self._cellSize = int(cellHeight)
        if not cellFitsToBodyX:
            self._cellSize = int(cellWidth)
        if not cellFitsToBodyY:
            self._cellSize = int(cellHeight)

    def _cell_set_geometry(self):

        countX = 0
        countY = 0
        self._cellsGeneralSize = self._cellSize * self.level[0]
        alignHCenter = int((self.window.field.size().width() / 2) - (self._cellsGeneralSize / 2))

        for row in self._cells:
            for cell in row:
                posX = countX * self._cellSize + alignHCenter
                posY = countY * self._cellSize
                cell.set_geometry(self._cellSize, posX, posY)
                countX += 1

                if (countX == self.level[0]):
                    countX = 0
                    countY += 1

        return alignHCenter

    def _cell_calc_max_amount(self):

        self._cellMaxAmountX = int(self.window.field.size().width() / self._cellMinSize)
        self._cellMaxAmountY = int(self.window.field.size().height() / self._cellMinSize)
        # print(f'maximum amount cells\nx: {self._cellMaxAmountX}, y: {self._cellMaxAmountY}')

    def _bomb_create(self):

        countCreatedBomb = 0
        amountCellX = len(self._cells[0]) - 1
        amountCellY = len(self._cells) - 1

        while True:
            indexX = randint(0, amountCellX)
            indexY = randint(0, amountCellY)
            if self._cells[indexY][indexX].set_role('bomb'):
                self._bombs.append(self._cells[indexY][indexX])
                countCreatedBomb += 1

            if countCreatedBomb == self.level[2]:
                break

        for bomb in self._bombs:
            position = self._cell_calc_position(bomb);
            aroundcell = self._cell_calc_around_cells(position);
            for cell in aroundcell:
                cell.count_bomb_around()

    def _chec_level(self):

        x = self.level[0] > self._cellMaxAmountX
        y = self.level[1] > self._cellMaxAmountY
        bomb = self.level[2] >= (self.level[0] * self.level[1])

        if x or y or bomb:
            return False
        else:
            return True

    def _calc_min_size_field(self):

        min_width = self._cellMinSize * self.level[0]
        min_height = self._cellMinSize * self.level[1]
        self.window.set_field_min_size(min_width, min_height)

    def set_amount_marked(self, adding):

        if adding:
            self._amountMarked += 1
        else:
            self._amountMarked -= 1

        self.window.set_header_count_marked(self._amountMarked)

    def cell_change_size(self):

        self._cell_calc_size()
        alignHCenter = self._cell_set_geometry()
        self.window.set_field_alignHCenter(alignHCenter)
        self._cell_calc_max_amount()

    def opening_around_cells(self, cell):

        position = self._cell_calc_position(cell)
        aroundCell = self._cell_calc_around_cells(position)
        for cell in aroundCell:
            cell.opening()

    def _tick(self):
        self._time += 1
        self.window.set_header_stopwatch(self._time)
        if (self._time == 999):
            self._stopwatch.stop()

    def start(self):

        self.started = True
        self._stopwatch.start()

    def end(self, scenario):

        self.game = False
        self._stopwatch.stop()

        for row in self._cells:
            for cell in row:
                cell.set_cursor_default()

        if scenario == 'defeat':
            for bomb in self._bombs:
                bomb.explode()
            self.window.set_header_btn_image('defeat')
        else:
            self.window.set_header_btn_image('defeat')

    def cell_opening(self, role):

        if role == 'bomb':
            self.end('defeat')
        else:
            self._cellAmountOpened += 1

            if self._cellAmountOpened == self.victoryAmountCellOpened:
                self.end('victory')

    def get_cells_general_size(self):
        return self._cellsGeneralSize

class Window(QMainWindow):

    resized = QtCore.pyqtSignal()

    def resizeEvent(self, event):

        self.resized.emit()
        return super(Window, self).resizeEvent(event)

    def keyPressEvent(self, event):
        print(event.key())
        if event.key() == 66:
            self.game.restart()


    def __init__(self):
        super(Window, self).__init__()

        self.game = 'obj'
        self.body = 'Widget'
        self.header = 'Widget'
        self.field = 'Widget'
        self._headerCountMarkedBoard = 'array'
        self._headerStopwatchBoard = 'array'
        self._headerButton = 'Button'
        self._headerButtonLabel = 'Label'
        self._headerButtonImg = 'Pixmap'
        self._headerTitle = 'Label'

        self._posX = 750
        self._posY = 150
        self._width = 450
        self._height = 450
        self._menuHeight = 30


        self._headerHeight = 0

        self._headerBoardAlignV = 0
        self._headerBoardLabelMargin = 0
        self._headerBoardLabelHeight = 0
        self._headerBoardLabelWidth = 0

        self._headerBoardWidth = 0
        self._headerBoardHeight = 0


        self.title = 'Minesweeper';
        self.resized.connect(self._change_size)
        self.setWindowTitle(self.title)
        self.setGeometry(self._posX, self._posY, self._width, self._height)

        self._createMenu()
        self._createBody()
        self._createHeader()

    def _change_size(self):

        self._width = self.size().width();
        self._height = self.size().height();

        self._adjustment_size()
        self.game.cell_change_size()

    def _adjustment_size(self):

        bodyWidth = self._width
        bodyHeight = self._height - self._menuHeight;
        fieldHeight = int(bodyHeight / 1.15)

        self.body.setGeometry(0, self._menuHeight, bodyWidth, bodyHeight)
        self.field.setGeometry(0, bodyHeight - fieldHeight, bodyWidth, fieldHeight)

    def _adjustment_size_header(self, alignHCenter):

        self._headerHeight = int(self.game.get_cells_general_size() * 0.15)
        headerWidth = (self.body.size().width() - (alignHCenter * 2))
        self.header.setGeometry(alignHCenter, 0, headerWidth, self._headerHeight)

        self._headerBoardHeight = int(self._headerHeight * 0.8)
        self._headerBoardAlignV = int(self._headerHeight * 0.1)
        self._headerBoardPadding = int(self._headerBoardHeight * 0.1)

        self._headerBoardLabelMargin = 5
        self._headerBoardLabelHeight = int(self._headerBoardHeight * 0.8)
        self._headerBoardLabelWidth = int(self._headerBoardLabelHeight / 2)

        self._headerBoardWidth = (self._headerBoardLabelWidth * 3) + (self._headerBoardLabelMargin * 2) + (self._headerBoardPadding * 2)


        boardCountAlignV = self._headerBoardAlignV
        boardStopwatchAlignV = headerWidth - self._headerBoardWidth - boardCountAlignV
        headerBtnX = int((headerWidth / 2) - (self._headerBoardHeight / 2))

        self._adjustment_size_header_board(self._headerCountMarkedBoard, boardCountAlignV)
        self._adjustment_size_header_board(self._headerStopwatchBoard, boardStopwatchAlignV)
        self._headerButton.setGeometry(headerBtnX, self._headerBoardAlignV, self._headerBoardHeight, self._headerBoardHeight)
        self._headerButtonLabel.setFixedSize(self._headerBoardHeight, self._headerBoardHeight)
        self._headerButtonLabel.setPixmap(self._headerButtonImg.scaled(self._headerBoardHeight, self._headerBoardHeight))

        try:
            self._headerTitle.setFixedSize(headerWidth, self._headerHeight)
            fontSize = int(self._headerHeight * 0.5)
            self._headerTitle.setFont(QtGui.QFont('SAIBA-45', fontSize))
        except:
            pass

    def _adjustment_size_header_board(self, board, alignVCenter):

        board[0].setGeometry(alignVCenter, self._headerBoardAlignV, self._headerBoardWidth, self._headerBoardHeight)

        boardLabel_pos = self._headerBoardLabelWidth + self._headerBoardLabelMargin
        for i in range(3):
            board[1][i].setGeometry((boardLabel_pos * i) + self._headerBoardPadding, self._headerBoardPadding, self._headerBoardLabelWidth, self._headerBoardLabelHeight)

        for i in range(3):
            board[1][i].setPixmap(board[2][i].scaled(self._headerBoardLabelWidth, self._headerBoardLabelHeight))

    def _createMenu(self):

        menu = self.menuBar()
        game = menu.addMenu('Игра')
        settings = menu.addMenu('Настройки')
        aboud = menu.addMenu('Oб проекте')

        play = game.addAction(QtWidgets.QAction('Играть', self))
        game.addAction(QtWidgets.QAction('Заново', self))
        game.addAction(QtWidgets.QAction('Новый уровень', self))

        self._menuHeight = int(menu.size().height())

    def _createBody(self):

        self.body = QtWidgets.QWidget(self)
        self.field = QtWidgets.QWidget(self.body)

        self._adjustment_size()

    def _createHeader(self):

        self.header = QtWidgets.QWidget(self.body)
        self.header.setStyleSheet('background-color: grey; ')

        self._headerCountMarkedBoard = self._create_board()
        self._headerStopwatchBoard = self._create_board()

        self._headerButton = HeaderButton(self, self.header)
        # self._headerButton.setStyleSheet('border: 2px inset #929292')
        self._headerButton.setCursor(QtCore.Qt.PointingHandCursor)
        self._headerButtonLabel = QtWidgets.QLabel(self._headerButton)


    def _create_board(self):
        board = QtWidgets.QWidget(self.header)
        board.setStyleSheet('background:black;border-radius:3px;')
        boardFull = [
            board,
            [
                QtWidgets.QLabel(board),
                QtWidgets.QLabel(board),
                QtWidgets.QLabel(board)
            ],
            [
                QtGui.QPixmap('./image/digital_tube/dt_0.png'),
                QtGui.QPixmap('./image/digital_tube/dt_0.png'),
                QtGui.QPixmap('./image/digital_tube/dt_0.png'),
            ]
        ]

        return boardFull

    def set_header_btn_image(self, src):

        self._headerButtonImg = QtGui.QPixmap(f'./image/smiley/{src}.png')
        self._headerButtonLabel.setPixmap(self._headerButtonImg.scaled(self._headerBoardHeight, self._headerBoardHeight))

    def _board_convert_number(self, number):
        x = number % 10
        y = number % 100
        numbers = [
            int((number - y) / 100),
            int((y - x) / 10),
            x
        ]

        return numbers

    def _set_header_board(self, board, number):

        numbers = self._board_convert_number(number)

        for i in range(3):
            board[2][i] = QtGui.QPixmap(f'image/digital_tube/dt_{numbers[i]}.png')

        for i in range(3):
            board[1][i].setPixmap(board[2][i].scaled(self._headerBoardLabelWidth, self._headerBoardLabelHeight))


    def set_field_alignHCenter(self, alignHCenter):

        self._adjustment_size_header(alignHCenter)

    def set_field_min_size(self, w, h):

        h += self._menuHeight + self._headerHeight
        self.setMinimumSize(w, h)

    def set_header_stopwatch(self, number):

        # self.setWindowTitle(f'{self.title} : {number}s')
        self._set_header_board(self._headerStopwatchBoard, number)

    def set_header_count_marked(self, number):

        self._set_header_board(self._headerCountMarkedBoard, number)

    def setGame(self, game):

        self.game = game
        self._headerButton.clicked.connect(self.game.restart)


class HeaderButton(QtWidgets.QPushButton):

    def __init__(self, window, parrent):
        super(HeaderButton, self).__init__(parrent)
        self.window = window

    def enterEvent(self, QEvent):

        if (self.window.game.game):
            self.window.set_header_btn_image('hover')

    def leaveEvent(self, QEvent):

        if (self.window.game.game):
            self.window.set_header_btn_image('default')


def application():

    app = QApplication(sys.argv)
    # QtGui.QFontDatabase.addApplicationFont('./font/SAIBA-45.otf')
    window = Window()
    game = Game(window)
    window.setGame(game)

    window.show()
    sys.exit(app.exec_())

if (__name__ == '__main__'):
    application()
