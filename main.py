from PyQt5 import QtWidgets, QtGui, QtCore, QtWebEngineWidgets

from random import randint
from pathlib import Path
import os, sys, json


class Cell(QtWidgets.QPushButton):

    def mousePressEvent(self, QMouseEvent):

        if not game.started:
            game.start()

        if not self._opened and game.game:
            if QMouseEvent.button() == QtCore.Qt.LeftButton:
                self.opening()
            elif QMouseEvent.button() == QtCore.Qt.RightButton:
                self._set_mark()

    def __init__(self, field, size):
        super(Cell, self).__init__(field)

        self._size = size

        self._amountBombAround = 0
        self._opened = False
        self._markedFlag = False
        self._markedSupposed = False
        self._role = 'empty'
        self.img = QtGui.QPixmap(getUrl('./image/cell/cell_11.bmp'))
        self.imgLabel = QtWidgets.QLabel(self)

        self.setCursor(cursorShovel)

        self._image_adjustment()

    def _set_mark(self):

        if self._markedFlag:
            self._markedFlag = False
            self._markedSupposed = True
            game.set_amount_marked(False)
            self._set_image(10)

        elif self._markedSupposed:
            self._markedSupposed = False
            self._set_image(11)

        elif not game.is_amount_marked():
            self._markedFlag = True
            game.set_amount_marked(True)
            self._set_image(9)

    def _set_image(self, id):

        self.img = QtGui.QPixmap(getUrl(f'./image/cell/cell_{id}.bmp'))
        self._image_adjustment()

    def _image_adjustment(self):

        self.imgLabel.resize(self._size, self._size)
        self.imgLabel.setPixmap(self.img.scaled(self._size, self._size))

    def set_role(self, role):

        if game.get_modeCheat():
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
        self.setCursor(cursorMetalDetector)
        game.cell_opening(self._role)

        if (self._markedFlag):
            game.set_amount_marked(False)

        if self._role == 'empty':
            self._set_image(self._amountBombAround)
            if self._amountBombAround == 0:
                game.opening_around_cells(self)

    def set_cursor_default(self):

        self.setCursor(cursorDefault)

    def explode(self):

            self._set_image(12)


class Game:

    def __init__(self):
        self._cellMinSize = 35
        self._modeCheat = settings_game.params['mode_cheat']
        self._modeEndlessMarking = settings_game.params['mode_endless_marking']
        self._cellMaxAmountX = 0
        self._cellMaxAmountY = 0
        self._cellSize = 35
        self.game = False
        self.set_level(settings_game.params['level'])

        self._stopwatch = QtCore.QTimer()
        self._stopwatch.setInterval(1000)
        self._stopwatch.timeout.connect(self._tick)

    def set_level(self, level):

        self.level = level
        settings_game.params['level'] = level
        self.victoryAmountCellOpened = (self.level[0] * self.level[1]) - self.level[2]

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
            window.headerButton.set_image('defeat')
        else:
            window.headerButton.set_image('win')

    def restart(self):

        self.started = False

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

        window.set_header_stopwatch(0)
        window.set_header_count_marked(0)
        window.headerButton.set_image('default')

        if self._cell_create():
            self.game = True
            self._bomb_create()
            self.cell_change_size()
            self._calc_min_size_field()
        else:
            print(f'Error: maximum amount cells\nx: {self._cellMaxAmountX}, y: {self._cellMaxAmountY}')

    def _cell_create(self):

        if not self._chec_level():
            return False

        for i in range(self.level[1]):
            self._cells.append([])
            for j in range(self.level[0]):

                cell = Cell(window.field, self._cellSize)
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

        cellWidth = window.field.size().width() / self.level[0]
        cellHeight = window.field.size().height() / self.level[1]
        cellFitsToBodyX = (self.level[0] * self._cellSize) < (window.field.size().width() + 1)
        cellFitsToBodyY = (self.level[1] * self._cellSize) < (window.field.size().height() + 1)

        if cellFitsToBodyX and cellFitsToBodyY:
            if (cellWidth <= cellHeight):
                self._cellSize = int(cellWidth)
            else:
                self._cellSize = int(cellHeight)
        if not cellFitsToBodyY:
            self._cellSize = int(cellHeight)
        if not cellFitsToBodyX:
            self._cellSize = int(cellWidth)

    def _cell_set_geometry(self):

        countX = 0
        countY = 0
        cellsGeneralWidth = self._cellSize * self.level[0]
        alignHCenter = int((window.field.size().width() / 2) - (cellsGeneralWidth / 2))

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

        self._cellMaxAmountX = int(window.field.size().width() / self._cellMinSize)
        self._cellMaxAmountY = int(window.field.size().height() / self._cellMinSize)
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

    def cell_change_size(self):

        self._cell_calc_max_amount()
        if self.game:
            self._cell_calc_size()
            alignHCenter = self._cell_set_geometry()
            window.set_field_alignHCenter(alignHCenter)

    def opening_around_cells(self, cell):

        position = self._cell_calc_position(cell)
        aroundCell = self._cell_calc_around_cells(position)
        for cell in aroundCell:
            cell.opening()

    def cell_opening(self, role):

        if role == 'bomb':
            self.end('defeat')
        else:
            self._cellAmountOpened += 1

            if self._cellAmountOpened == self.victoryAmountCellOpened:
                self.end('victory')

    def _chec_level(self):

        x = self.level[0] > self._cellMaxAmountX
        y = self.level[1] > self._cellMaxAmountY
        bomb = self.level[2] >= (self.level[0] * self.level[1])

        if x or y or bomb:
            return False
        else:
            return True

    def _tick(self):

        self._time += 1
        window.set_header_stopwatch(self._time)
        if (self._time == 999):
            self._stopwatch.stop()

    def _calc_min_size_field(self):

        min_width = self._cellMinSize * self.level[0]
        min_height = self._cellMinSize * self.level[1]
        window.set_field_min_size(min_width, min_height)

    def is_amount_marked(self):

        if self._modeEndlessMarking:
            return False

        if self._amountMarked >= self.level[2]:
            return True
        return False

    def set_amount_marked(self, adding):

        if adding:
            self._amountMarked += 1
        else:
            self._amountMarked -= 1

        window.set_header_count_marked(self._amountMarked)

    def set_modeCheat(self, status):

        self._modeCheat = status
        settings_game.params['mode_cheat'] = status

    def set_modeEndlessMarking(self, status):

        self._modeEndlessMarking = status
        settings_game.params['mode_endless_marking'] = status

    def get_modeCheat(self):

        return self._modeCheat

    def get_modeEndlessMarking(self):

        return self._modeEndlessMarking

    def get_cells_general_height(self):

        return self._cellSize * self.level[1]

    def get_cells_max_amount(self):

        return [self._cellMaxAmountX, self._cellMaxAmountY]


class Window(QtWidgets.QMainWindow):

    def moveEvent(self, event):

        settings_game.params['pos_x'] = event.pos().x();
        settings_game.params['pos_y'] = event.pos().y();

        return super(Window, self).moveEvent(event)

    def resizeEvent(self, event):

        self._width = self.size().width();
        self._height = self.size().height();

        settings_game.params['width'] = self._width
        settings_game.params['height'] = self._height

        self._adjustment_size()
        return super(Window, self).resizeEvent(event)

    def closeEvent(self, event):

        if self._window_exit():
            event.accept()
            return super(Window, self).closeEvent(event)
        else:
            event.ignore()

    def __init__(self):
        super(Window, self).__init__()

        self._menu = self.menuBar()
        self._menuGame = self._menu.addMenu('Game')
        self.body = QtWidgets.QWidget(self)
        self.header = QtWidgets.QWidget(self.body)
        self.field = QtWidgets.QWidget(self.body)
        self.headerButton = HeaderButton(self.header)
        self._headerCountMarkedBoard = self._create_board()
        self._headerStopwatchBoard = self._create_board()


        posX = settings_game.params['pos_x']
        posY = settings_game.params['pos_y']
        self._width = settings_game.params['width']
        self._height = settings_game.params['height']
        self._menuHeight = int(self._menu.size().height())

        self.header.setStyleSheet('background-color: grey;')


        self._headerHeight = 0

        self._headerBoardAlignV = 0
        self._headerBoardLabelMargin = 0
        self._headerBoardLabelHeight = 0
        self._headerBoardLabelWidth = 0

        self._headerBoardWidth = 0
        self._headerBoardHeight = 0


        self.title = 'Minesweeper';
        self.setWindowIcon(QtGui.QIcon(getUrl('./image/icon.ico')))
        self.setWindowTitle(self.title)
        self.setGeometry(posX, posY, self._width, self._height)
        self.setCursor(cursorDefault)

        self._create_menu_action()

    def _adjustment_size(self):

        bodyWidth = self._width
        bodyHeight = self._height - self._menuHeight;
        fieldHeight = int(bodyHeight / 1.15)

        self.body.setGeometry(0, self._menuHeight, bodyWidth, bodyHeight)
        self.field.setGeometry(0, bodyHeight - fieldHeight, bodyWidth, fieldHeight)

        game.cell_change_size()

    def _adjustment_size_header(self, alignHCenter):

        self._headerHeight = int(game.get_cells_general_height() * 0.15)
        # self._headerHeight = int(self.field.size().height() * 0.15)
        headerWidth = (self.body.size().width() - (alignHCenter * 2))

        k = 4.5 # Коэфициент сооотношение сторон header
        if headerWidth / self._headerHeight < k:
            headerWidth = int(self._headerHeight * k)
            alignHCenter = int((self.body.size().width() / 2) - (headerWidth / 2))
            self.header.setGeometry(alignHCenter, 0, headerWidth, self._headerHeight)
        else:
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
        self.headerButton.setGeometry(headerBtnX, self._headerBoardAlignV, self._headerBoardHeight)

    def _adjustment_size_header_board(self, board, alignVCenter):

        board[0].setGeometry(alignVCenter, self._headerBoardAlignV, self._headerBoardWidth, self._headerBoardHeight)

        boardLabel_pos = self._headerBoardLabelWidth + self._headerBoardLabelMargin
        for i in range(3):
            board[1][i].setGeometry((boardLabel_pos * i) + self._headerBoardPadding, self._headerBoardPadding, self._headerBoardLabelWidth, self._headerBoardLabelHeight)

        for i in range(3):
            board[1][i].setPixmap(board[2][i].scaled(self._headerBoardLabelWidth, self._headerBoardLabelHeight))

    def _create_menu_action(self):

        manuRestart = QtWidgets.QAction(QtGui.QIcon(getUrl('./image/menu/restart.bmp')), '&Restart', self)
        manuNewLevel = QtWidgets.QAction(QtGui.QIcon(getUrl('./image/menu/new_level.bmp')), '&New Level', self)
        manuExit = QtWidgets.QAction(QtGui.QIcon(getUrl('./image/menu/exit.bmp')), '&Exit', self)
        manuSettings = QtWidgets.QAction('&Settings', self)
        manuAbout = QtWidgets.QAction('&About the project', self)

        manuRestart.setShortcut('Ctrl+R')
        manuNewLevel.setShortcut('Ctrl+N')
        manuExit.setShortcut('Ctrl+Q')
        manuSettings.setShortcut('Ctrl+S')
        manuAbout.setShortcut('Ctrl+H')

        self.headerButton.clicked.connect(game.restart)
        manuRestart.triggered.connect(game.restart)
        manuNewLevel.triggered.connect(lambda: WindowLevel())
        manuExit.triggered.connect(self._menu_exit)
        manuSettings.triggered.connect(lambda: WindowSettings())
        manuAbout.triggered.connect(lambda: WindowAbout())

        self._menu.setCursor(cursorHover)
        self._menuGame.setCursor(cursorHover)

        self._menu.addAction(manuSettings)
        self._menu.addAction(manuAbout)
        self._menuGame.addAction(manuRestart)
        self._menuGame.addAction(manuNewLevel)
        self._menuGame.addAction(manuExit)

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
                QtGui.QPixmap(getUrl('./image/board/digit_0.bmp')),
                QtGui.QPixmap(getUrl('./image/board/digit_0.bmp')),
                QtGui.QPixmap(getUrl('./image/board/digit_0.bmp')),
            ]
        ]

        return boardFull

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
            board[2][i] = QtGui.QPixmap(getUrl(f'./image/board/digit_{numbers[i]}.bmp'))

        for i in range(3):
            board[1][i].setPixmap(board[2][i].scaled(self._headerBoardLabelWidth, self._headerBoardLabelHeight))

    def _menu_exit(self):

        if self._window_exit():
            sys.exit(app.exec_())

    def _window_exit(self):

        title = 'exit'
        text = 'gondon'
        yes = QtWidgets.QMessageBox.Yes
        no = QtWidgets.QMessageBox.No
        result = QtWidgets.QMessageBox.question(self, title, text, yes | no, no)

        if result == yes:
            settings_game.save()
            return True
        else:
            return False

    def set_field_alignHCenter(self, alignHCenter):

        self._adjustment_size_header(alignHCenter)

    def set_field_min_size(self, w, h):

        h += self._menuHeight + self._headerHeight
        self.setMinimumSize(w, h)

    def set_header_stopwatch(self, number):

        self._set_header_board(self._headerStopwatchBoard, number)
        # self.setWindowTitle(f'{self.title} : {number}s')

    def set_header_count_marked(self, number):

        self._set_header_board(self._headerCountMarkedBoard, number)


class HeaderButton(QtWidgets.QPushButton):

    def setGeometry(self, posX, posY, size):

        self._change_size(size)
        return super(HeaderButton, self).setGeometry(posX, posY, size, size)

    def enterEvent(self, QEvent):

        if (game.game):
            self.set_image('hover')

    def leaveEvent(self, QEvent):

        if (game.game):
            self.set_image('default')

    def __init__(self, parrent):
        super(HeaderButton, self).__init__(parrent)

        self.setCursor(cursorHover)
        self._label = QtWidgets.QLabel(self)
        self._img = QtGui.QPixmap(getUrl('./image/smiley/default.bmp'))
        self.size = 0

    def set_image(self, src):

        self._img = QtGui.QPixmap(getUrl(f'./image/smiley/{src}.bmp'))
        self._label.setPixmap(self._img.scaled(self.size, self.size))

    def _change_size(self, size):

        self.size = size
        self._label.setFixedSize(self.size, self.size)
        self._label.setPixmap(self._img.scaled(self.size, self.size))


class WindowAbout(QtWidgets.QDialog):

    def __init__(self):
        super(WindowAbout, self).__init__(window, QtCore.Qt.Window)

        self.setWindowFlags(QtCore.Qt.Dialog)
        self.setWindowModality(QtCore.Qt.WindowModal)
        self._width = 420
        self._height = 360

        self.setWindowTitle('About the project')
        self.setCursor(cursorDefault)
        self.setStyleSheet('background-color: grey;')
        self.setFixedSize(self._width, self._height)
        self.move(settings_game.params['pos_x'] + 20, settings_game.params['pos_y'] + 20)

        actionExit = QtWidgets.QAction(self)
        actionExit.setShortcut('Ctrl+Q')
        actionExit.triggered.connect(lambda: self.deleteLater())
        self.addAction(actionExit)

        view = QtWebEngineWidgets.QWebEngineView(self)
        view.setGeometry(0, 0, self._width, self._height)
        html = Path(getUrl('./about.html')).read_text(encoding="utf8")
        css = str(Path(getUrl('./about.css')).resolve())
        view.setHtml(html, baseUrl=QtCore.QUrl.fromLocalFile(css))

        self.show()


class WindowSettings(QtWidgets.QDialog):

    def __init__(self):
        super(WindowSettings, self).__init__(window, QtCore.Qt.Window)

        self.setWindowFlags(QtCore.Qt.Dialog)
        self.setWindowModality(QtCore.Qt.WindowModal)
        self._width = 220
        self._height = 180

        self.setWindowTitle('Settings')
        self.setCursor(cursorDefault)
        self.setStyleSheet('background-color: grey;')
        self.setFixedSize(self._width, self._height)
        self.move(settings_game.params['pos_x'] + 20, settings_game.params['pos_y'] + 20)

        actionExit = QtWidgets.QAction(self)
        actionExit.setShortcut('Ctrl+Q')
        actionExit.triggered.connect(lambda: self.deleteLater())
        self.addAction(actionExit)

        self._boxCheat = self._create_box_radio('Mode cheat', game.get_modeCheat(), game.set_modeCheat)
        self._boxMarking = self._create_box_radio('Endless marking', game.get_modeEndlessMarking(), game.set_modeEndlessMarking)

        self._boxWidth = 160
        self._boxHeight = 60
        alignHCenter = int(self._width / 2) - int(self._boxWidth / 2)
        self._boxMarking[0].move(alignHCenter, 10)
        self._boxMarking[0].resize(self._boxWidth, self._boxHeight)
        self._boxCheat[0].move(alignHCenter, 80)
        self._boxCheat[0].resize(self._boxWidth, self._boxHeight)

        self.show()

    def _create_box_radio(self, title, status, func):

        radio1 = QtWidgets.QRadioButton('OFF')
        radio2 = QtWidgets.QRadioButton('ON')

        radio1.setCursor(cursorHover)
        radio2.setCursor(cursorHover)

        radio1.setChecked(not status)
        radio2.setChecked(status)

        radio2.toggled.connect(func)

        box = QtWidgets.QGroupBox(title, self)
        hbox = QtWidgets.QHBoxLayout()
        hbox.addWidget(radio1)
        hbox.addWidget(radio2)
        box.setLayout(hbox)

        return [box, hbox, radio1, radio2]


class WindowLevel(QtWidgets.QDialog):

    def __init__(self):
        super(WindowLevel, self).__init__(window, QtCore.Qt.Window)

        self.setWindowFlags(QtCore.Qt.Dialog)
        self.setWindowModality(QtCore.Qt.WindowModal)
        self._width = 320
        self._height = 240

        self.setWindowTitle('New Level')
        self.setCursor(cursorDefault)
        self.setStyleSheet('background-color: grey;')
        self.setFixedSize(self._width, self._height)
        self.move(settings_game.params['pos_x'] + 20, settings_game.params['pos_y'] + 20)

        actionExit = QtWidgets.QAction(self)
        actionExit.setShortcut('Ctrl+Q')
        actionExit.triggered.connect(lambda: self.deleteLater())
        self.addAction(actionExit)

        self.body = QtWidgets.QWidget(self)
        self.body.resize(self._width, self._height)

        self._level = game.level
        self._cells_max_amount = game.get_cells_max_amount()
        self._x = self._level[0]
        self._y = self._level[1]
        self._b = self._level[2]

        self.rangeH = self._create_range('h')
        self.rangeV = self._create_range('v')
        self.rangeB = self._create_range('b')

        self.btn = QtWidgets.QPushButton(self.body)
        self.btn.setText('Play')
        self.btn.setGeometry(int(self.body.size().width() / 2) - 30, 100, 60, 40)
        self.btn.setCursor(cursorHover)
        self.btn.clicked.connect(self._play)

        self.description = QtWidgets.QLabel(self.body)
        self.description.setGeometry(0, 150, self._width, 50)
        self.description.setAlignment(QtCore.Qt.AlignCenter)
        self.description.setText(f'''Cells max with width({window.size().width()}) and height({window.size().height()}).\nInput range can move with helping (←, →, ↑, ↓)''')

        self.show()

    def _create_range(self, isRange):

        rangeH = QtWidgets.QWidget(self.body)
        rangeHText = QtWidgets.QLabel(rangeH)
        rangeHInput = QtWidgets.QSlider(rangeH)

        if isRange == 'h':
            rangeH.move(5, 5)
            rangeHText.setText(f'Amount Cells in H: {self._level[0]}')
            rangeHInput.setRange(2, self._cells_max_amount[0])
            rangeHInput.setSliderPosition(self._x)
            rangeHInput.valueChanged.connect(self.changeAmountCellH)
        elif isRange == 'v':
            rangeH.move(5, 30)
            rangeHText.setText(f'Amount Cells in V: {self._level[1]}')
            rangeHInput.setRange(2, self._cells_max_amount[1])
            rangeHInput.setSliderPosition(self._y)
            rangeHInput.valueChanged.connect(self.changeAmountCellV)
        elif isRange == 'b':
            rangeH.move(5, 60)
            rangeHText.setText(f'Amount Bomb      : {self._level[2]}')
            rangeHInput.setRange(1, (self._x * self._y) - 1)
            rangeHInput.setSliderPosition(self._b)
            rangeHInput.valueChanged.connect(self.changeAmountCellBomb)

        rangeHText.adjustSize()

        rangeHInput.setSingleStep(1)
        rangeHInput.setOrientation(QtCore.Qt.Horizontal)
        rangeHInput.setGeometry(rangeHText.size().width() + 20, 0, 100, 30)
        rangeHInput.setCursor(cursorHover)

        rangeH.adjustSize()

        return [rangeH, rangeHText, rangeHInput]

    def changeAmountCellH(self):

        self._x = self.rangeH[2].value()
        self.rangeH[1].setText(f'Amount Cells in H: {self._x}')
        self.rangeH[1].adjustSize()

        self._set_bomb_max()

    def changeAmountCellV(self):

        self._y = self.rangeV[2].value()
        self.rangeV[1].setText(f'Amount Cells in V: {self._y}')
        self.rangeV[1].adjustSize()

        self._set_bomb_max()

    def changeAmountCellBomb(self):

        self._b = self.rangeB[2].value()
        self.rangeB[1].setText(f'Amount Bomb: {self._b}')
        self.rangeB[1].adjustSize()

    def _set_bomb_max(self):

        self.rangeB[2].setMaximum((self._x * self._y) - 1)

    def _play(self):

        game.set_level([self._x, self._y, self._b])
        game.restart()
        self.deleteLater()


class Settings():

    def __init__(self):

        self._file = open(getUrl('./sfg.json'), 'r')
        self.params = json.loads(self._file.read())
        self._file.close()

    def save(self):

        self._file = open(getUrl('./sfg.json'), 'w')
        self._file.write(json.dumps(self.params))
        self._file.close()


def make_cursor(url, size=60):

    pixmap = QtGui.QPixmap(url)
    pixmap = pixmap.scaled(size, size)
    return QtGui.QCursor(pixmap)

def getUrl(url):

    return os.path.join(basedir, url)

if (__name__ == '__main__'):

    basedir = os.path.dirname(__file__)
    app = QtWidgets.QApplication(sys.argv)

    cursorShovel = make_cursor(getUrl('./image/cursor/shovel.bmp'))
    cursorMetalDetector = make_cursor(getUrl('./image/cursor/metalDetector.bmp'))
    cursorDefault = make_cursor(getUrl('./image/cursor/default.bmp'))
    cursorHover = make_cursor(getUrl('./image/cursor/hover.bmp'))

    settings_game = Settings()
    game = Game()
    window = Window()

    window.show()
    game.restart()

    sys.exit(app.exec_())
