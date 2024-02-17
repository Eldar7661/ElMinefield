# from PyQt5 import QtWidgets, QtGui, QtCore, QtWebEngineWidgets, QtMultimedia

from PyQt5.QtWidgets import QApplication, QMainWindow, QDialog, QWidget, QGroupBox, QHBoxLayout, QFormLayout, QLabel, QAction, QPushButton, QSlider, QRadioButton, QMessageBox, QScrollArea
from PyQt5.QtCore import Qt, QUrl, QTimer
from PyQt5.QtGui import QPixmap, QIcon, QCursor
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent, QSound
from PyQt5.QtWebEngineWidgets import QWebEngineView

from random import randint
from pathlib import Path
import os, sys, json, pkgutil


class Cell(QPushButton):

    def mousePressEvent(self, QMouseEvent):

        if not game.started:
            game.start()

        if not self._opened and game.game:
            if QMouseEvent.button() == Qt.LeftButton:
                self.opening()
            elif QMouseEvent.button() == Qt.RightButton:
                self._set_mark()

    def __init__(self, field, size):
        super(Cell, self).__init__(field)

        self._size = size

        self._amountBombAround = 0
        self._opened = False
        self._markedFlag = False
        self._markedSupposed = False
        self._role = 'empty'
        self.img = QPixmap(getUrl('./image/cell/cell_11.bmp'))
        self.imgLabel = QLabel(self)
        self.setCursor(cursorShovel)

        self._image_adjustment()

    def _set_mark(self):

        if self._markedFlag:
            self._markedFlag = False
            self._markedSupposed = True
            game.set_amount_marked(False)
            sound.play('flag_take_off')
            self._set_image(10)

        elif self._markedSupposed:
            self._markedSupposed = False
            self._set_image(11)

        elif not game.is_amount_marked():
            self._markedFlag = True
            game.set_amount_marked(True)
            sound.play('flag_put')
            self._set_image(9)

    def _set_image(self, id):

        self.img = QPixmap(getUrl(f'./image/cell/cell_{id}.bmp'))
        self._image_adjustment()

    def _image_adjustment(self):

        self.imgLabel.resize(self._size, self._size)
        self.imgLabel.setPixmap(self.img.scaled(self._size, self._size))

    def set_role(self, role):

        if settings_game.params['mode_cheat']:
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

        sound.play('cell_open')
        self._opened = True
        self.setCursor(cursorMetalDetector)

        if (self._markedFlag):
            game.set_amount_marked(False)

        if self._role == 'empty':
            self._set_image(self._amountBombAround)
            if self._amountBombAround == 0:
                game.opening_around_cells(self)
        elif game.game:
            blackout = QWidget(self)
            blackout.setStyleSheet('background: rgba(255,0,0,0.4);')
            blackout.resize(self._size, self._size)
            blackout.show()

        game.cell_opening(self._role)

    def set_cursor_default(self):

        self.setCursor(cursorDefault)

    def explode(self):

        self._set_image(12)


class Game:

    def __init__(self):
        self._cellMinSize = 35
        self._cellMaxAmountX = 0
        self._cellMaxAmountY = 0
        self._cellSize = 35
        self.game = False
        self.level_update()

        self._stopwatch = QTimer()
        self._stopwatch.setInterval(1000)
        self._stopwatch.timeout.connect(self._tick)

    def level_update(self):

        self.level = [
            settings_game.params['level_h'],
            settings_game.params['level_v'],
            settings_game.params['level_b']
        ]
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
            window.headerButton.set_image('defeat')
            sound.play('defeat')
            for bomb in self._bombs:
                bomb.explode()
        else:
            window.headerButton.set_image('win')
            sound.play('win')

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

        if settings_game.params['mode_endless_marking']:
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

    def get_cells_general_height(self):

        return self._cellSize * self.level[1]

    def get_cells_max_amount(self):

        return [self._cellMaxAmountX, self._cellMaxAmountY]


class Window(QMainWindow):

    def moveEvent(self, event):

        if settings_game.params['mode_save_wind_pos']:
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
        self.body = QWidget(self)
        self.header = QWidget(self.body)
        self.field = QWidget(self.body)
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
        self.setWindowIcon(QIcon(getUrl('./image/icon_minesweeper.ico')))
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

        manuRestart = QAction(QIcon(getUrl('./image/menu/restart.bmp')), '&Restart', self)
        manuNewLevel = QAction(QIcon(getUrl('./image/menu/new_level.bmp')), '&New Level', self)
        manuExit = QAction(QIcon(getUrl('./image/menu/exit.bmp')), '&Exit', self)
        manuSettings = QAction('&Settings', self)
        manuAbout = QAction('&About the project', self)

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

        board = QWidget(self.header)
        board.setStyleSheet('background:black;border-radius:3px;')
        boardFull = [
            board,
            [
                QLabel(board),
                QLabel(board),
                QLabel(board)
            ],
            [
                QPixmap(getUrl('./image/board/digit_0.bmp')),
                QPixmap(getUrl('./image/board/digit_0.bmp')),
                QPixmap(getUrl('./image/board/digit_0.bmp')),
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
            board[2][i] = QPixmap(getUrl(f'./image/board/digit_{numbers[i]}.bmp'))

        for i in range(3):
            board[1][i].setPixmap(board[2][i].scaled(self._headerBoardLabelWidth, self._headerBoardLabelHeight))

    def _menu_exit(self):

        if self._window_exit():
            sys.exit(app.exec_())

    def _window_exit(self):

        title = 'Confirmation'
        text = 'close the application ?'
        yes = QMessageBox.Yes
        no = QMessageBox.No
        result = QMessageBox.question(self, title, text, yes | no, no)

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

        if settings_game.params['mode_inversion_marking']:
            number = game.level[2] - number

        if number > 999:
            number = 999
        elif number < 0:
            number = 0

        self._set_header_board(self._headerCountMarkedBoard, number)


class HeaderButton(QPushButton):

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
        self._label = QLabel(self)
        self._img = QPixmap(getUrl('./image/smiley/default.bmp'))
        self._size = 0

    def set_image(self, src):

        self._img = QPixmap(getUrl(f'./image/smiley/{src}.bmp'))
        self._label.setPixmap(self._img.scaled(self._size, self._size))

    def _change_size(self, size):

        self._size = size
        self._label.setFixedSize(self._size, self._size)
        self._label.setPixmap(self._img.scaled(self._size, self._size))


class WindowAbout(QDialog):

    def __init__(self):
        super(WindowAbout, self).__init__(window, Qt.Window)

        self.setWindowFlags(Qt.Dialog)
        self.setWindowModality(Qt.WindowModal)
        self._width = 420
        self._height = 360

        self.setWindowTitle('About the project')
        self.setCursor(cursorDefault)
        self.setStyleSheet('background-color: grey;')
        self.setFixedSize(self._width, self._height)
        self.move(settings_game.params['pos_x'] + 20, settings_game.params['pos_y'] + 20)

        actionExit = QAction(self)
        actionExit.setShortcut('Ctrl+Q')
        actionExit.triggered.connect(self.deleteLater)
        self.addAction(actionExit)

        view = QWebEngineView(self)
        view.setGeometry(0, 0, self._width, self._height)
        html = Path(getUrl('./about.html')).read_text(encoding="utf8")
        css = str(Path(getUrl('./about.css')).resolve())
        view.setHtml(html, baseUrl=QUrl.fromLocalFile(css))

        self.show()


class WindowSettings(QDialog):

    def __init__(self):
        super(WindowSettings, self).__init__(window, Qt.Window)

        self.setWindowFlags(Qt.Dialog)
        self.setWindowModality(Qt.WindowModal)

        self._width = 320
        self._height = 300

        self.setWindowTitle('Settings')
        self.setFixedSize(self._width, self._height)
        self.move(settings_game.params['pos_x'] + 20, settings_game.params['pos_y'] + 20)
        self.setCursor(cursorDefault)
        self.setStyleSheet('background-color: grey;')

        actionExit = QAction(self)
        actionExit.setShortcut('Ctrl+Q')
        actionExit.triggered.connect(self.deleteLater)
        self.addAction(actionExit)


        self._body = QWidget()
        self._body.setGeometry(0, 0, self._width, 650)

        self._form = QFormLayout(self._body)
        self._form.setFormAlignment(Qt.AlignHCenter)
        self._form.setLabelAlignment(Qt.AlignLeft)

        self._scroll = QScrollArea(self)
        self._scroll.setObjectName('window_sett_scroll')
        self._scroll.setStyleSheet('#window_sett_scroll { border: none; }')
        self._scroll.setAlignment(Qt.AlignRight)
        self._scrollBar = self._scroll.verticalScrollBar()
        self._scrollBar.setFixedHeight(self._height)
        self._scroll.setWidget(self._body)

        self._btnReset = QPushButton(self)
        self._btnReset.setText('Reset')
        self._btnReset.setCursor(cursorHover)
        self._btnReset.clicked.connect(self._reset_settings)
        self._btnReset.resize(80, 30)

        self._boxRange = BoxRange('sound_valume', 0, 100, 1)
        self._boxRange.setFixedWidth(122)
        self._boxRange.event_connect(sound.change_volume)


        self._inputWindPos = self._formAddRadio('Save last window\n position', 'mode_save_wind_pos')
        self._inputMarkEndls = self._formAddRadio('Endless marking ', 'mode_endless_marking')
        self._inputMarkInver= self._formAddRadio('Inversion marking', 'mode_inversion_marking')
        self._inputSound = self._formAddRadio('Sound', 'mode_sound')
        self._form.addRow('Sound volume : ', self._boxRange)
        self._inputSoundCellOpen = self._formAddRadio('Sound cell open', 'sound_cell_open')
        self._inputSoundDefeat = self._formAddRadio('Sound defeat', 'sound_defeat')
        self._inputSoundWIn = self._formAddRadio('Sound win', 'sound_win')
        self._inputSoundPut = self._formAddRadio('Sound flag put', 'sound_flag_put')
        self._inputSoundTake = self._formAddRadio('Sound flag take off', 'sound_flag_take_off')
        self._inputCheat = self._formAddRadio('Mode cheat', 'mode_cheat')
        self._form.addRow('Settings : ', self._btnReset)

        self.show()

    def _formAddRadio(self, title, param):

        radio = BoxRadio(param)
        self._form.addRow(f'{title} : ', radio)

        return radio

    def _reset_settings(self):

        self._inputWindPos.set_status(True)
        self._inputMarkEndls.set_status(True)
        self._inputMarkInver.set_status(False)
        self._inputSound.set_status(True)
        self._boxRange.set_value(100)
        self._inputSoundCellOpen.set_status(True)
        self._inputSoundDefeat.set_status(True)
        self._inputSoundWIn.set_status(True)
        self._inputSoundPut.set_status(True)
        self._inputSoundTake.set_status(True)
        self._inputCheat.set_status(False)


class WindowLevel(QDialog):

    def closeEvent(self, event):

        self._recovery_level()
        event.accept()
        return super(WindowLevel, self).closeEvent(event)

    def __init__(self):
        super(WindowLevel, self).__init__(window, Qt.Window)

        self.setWindowFlags(Qt.Dialog)
        self.setWindowModality(Qt.WindowModal)
        self._width = 320
        self._height = 300
        self._formHeight = 200

        self.setWindowTitle('New Level')
        self.setCursor(cursorDefault)
        self.setStyleSheet('background-color: grey;')
        self.setFixedSize(self._width, self._height)
        self.move(settings_game.params['pos_x'] + 20, settings_game.params['pos_y'] + 20)

        actionExit = QAction(self)
        actionExit.setShortcut('Ctrl+Q')
        actionExit.triggered.connect(self._recovery_level)
        self.addAction(actionExit)

        self._body = QWidget(self)
        self._body.setGeometry(0, 0, self._width, self._height)
        self._main = QWidget(self._body)
        self._main.resize(self._width, self._formHeight)

        self._form = QFormLayout(self._main)
        self._form.setFormAlignment(Qt.AlignHCenter)
        self._form.setLabelAlignment(Qt.AlignLeft)


        self._old_level = game.level
        self._cells_max_amount = game.get_cells_max_amount()

        self._boxRangeH = BoxRange('level_h', 2, self._cells_max_amount[0], 1)
        self._boxRangeV = BoxRange('level_v', 2, self._cells_max_amount[1], 1)
        self._boxRangeB = BoxRange('level_b', 1, self._boxRangeB_calc_max(), 1)

        self._boxRangeH.setFixedWidth(122)
        self._boxRangeV.setFixedWidth(122)
        self._boxRangeB.setFixedWidth(122)
        self._boxRangeH.event_connect(self._change_level)
        self._boxRangeV.event_connect(self._change_level)

        self._btnPlay = QPushButton()
        self._btnPlay.setCursor(cursorHover)
        self._btnPlay.setText('Play')
        self._btnPlay.clicked.connect(self._play)

        self._form.addRow('Amount Cells in H : ', self._boxRangeH)
        self._form.addRow('Amount Cells in V : ', self._boxRangeV)
        self._form.addRow('Amount Bomb : ', self._boxRangeB)
        self._form.addRow('Level : ', self._btnPlay)


        self._description = QLabel(self._body)
        self._description.setGeometry(0, self._formHeight, self._width, 50)
        self._description.setAlignment(Qt.AlignCenter)
        self._description.setText(f'Cells max amount with width({window.size().width()})/height({window.size().height()}).\nInput range can move with helping (←, →, ↑, ↓),\n and mouse scroll.')


        self.show()

    def _recovery_level(self):

        settings_game.params['level_h'] = self._old_level[0]
        settings_game.params['level_v'] = self._old_level[1]
        settings_game.params['level_b'] = self._old_level[2]
        self.deleteLater()

    def _boxRangeB_calc_max(self):

        return (settings_game.params['level_h'] * settings_game.params['level_v']) - 1

    def _change_level(self, value):

        self._boxRangeB.set_max(self._boxRangeB_calc_max())

    def _play(self):

        game.level_update()
        game.restart()
        self.deleteLater()


class BoxRange(QGroupBox):

    def __init__(self, param, valueMin, valueMax, valueStep, parent=None):
        super(BoxRange, self).__init__(parent)
        self._parametr = param
        self._is_func = False
        self._func = None

        self._valueMin = valueMin
        self._valueMax = valueMax
        value = settings_game.params[self._parametr]

        self._rInput = QSlider()
        self._rInput.setOrientation(Qt.Horizontal)
        self._rInput.setCursor(cursorHover)
        self._rInput.setRange(self._valueMin, self._valueMax)
        self._rInput.setSingleStep(valueStep)
        self._rInput.setSliderPosition(value)
        self._rInput.valueChanged.connect(self._changeRange)

        self._label = QLabel()
        self._label.setText(str(value))

        layout = QHBoxLayout()
        layout.addWidget(self._label)
        layout.addWidget(self._rInput)
        self.setLayout(layout)

    def _changeRange(self):

        settings_game.params[self._parametr] = self._rInput.value()
        self._label.setText(str(self._rInput.value()))

        if self._is_func:
            self._func(self._rInput.value())

    def set_value(self, value):

        settings_game.params[self._parametr] = value
        self._rInput.setSliderPosition(value)

    def set_min(self, value):

        self._valueMin = value
        self._rInput.setRange(self._valueMin, self._valueMax)

    def set_max(self, value):

        self._valueMax = value
        self._rInput.setRange(self._valueMin, self._valueMax)

    def event_connect(self, func):

        self._func = func
        self._is_func = True


class BoxRadio(QGroupBox):

    def __init__(self, param, parent=None):
        super(BoxRadio, self).__init__(parent)
        self._parametr = param

        self._radioOff = QRadioButton('OFF')
        self._radioOn = QRadioButton('ON')
        self._radioOff.setCursor(cursorHover)
        self._radioOn.setCursor(cursorHover)
        self._update_status()

        self._radioOn.toggled.connect(self._chengeRadio)

        layout = QHBoxLayout()
        layout.addWidget(self._radioOff)
        layout.addWidget(self._radioOn)
        self.setLayout(layout)

    def _chengeRadio(self, status):

        settings_game.params[self._parametr] = status

    def set_status(self, status):

        settings_game.params[self._parametr] = status
        self._update_status()

    def _update_status(self):

        self._radioOff.setChecked(not settings_game.params[self._parametr])
        self._radioOn.setChecked(settings_game.params[self._parametr])


class Settings():

    def __init__(self):

        self._file = open(getUrl('./sfg.json'), 'r')
        self.params = json.loads(self._file.read())
        self._file.close()

    def save(self):

        self._file = open(getUrl('./sfg.json'), 'w')
        self._file.write(json.dumps(self.params))
        self._file.close()


class Sounds():

    def play(self, name):

        if settings_game.params['mode_sound'] and settings_game.params[f'sound_{name}']:
            return self._sounds[name].play()
        else:
            return False

    def __init__(self):
        self._is_gstreamer = False

        if check_gstreamer():
            self._is_gstreamer = True
            self._sounds = {
                'cell_open': QMediaPlayer(),
                'defeat': QMediaPlayer(),
                'win': QMediaPlayer(),
                'flag_put': QMediaPlayer(),
                'flag_take_off': QMediaPlayer()
            }

            self._sounds['cell_open'].setMedia(QMediaContent(QUrl.fromLocalFile(getUrl('./sounds/cell_open.wav'))))
            self._sounds['defeat'].setMedia(QMediaContent(QUrl.fromLocalFile(getUrl('./sounds/cell_explode.wav'))))
            self._sounds['win'].setMedia(QMediaContent(QUrl.fromLocalFile(getUrl('./sounds/win.wav'))))
            self._sounds['flag_put'].setMedia(QMediaContent(QUrl.fromLocalFile(getUrl('./sounds/flag_put.wav'))))
            self._sounds['flag_take_off'].setMedia(QMediaContent(QUrl.fromLocalFile(getUrl('./sounds/flag_take_off.wav'))))
        else:
            self._sounds = {
                'cell_open': QSound(getUrl('./sounds/cell_open.wav')),
                'defeat': QSound(getUrl('./sounds/cell_explode.wav')),
                'win': QSound(getUrl('./sounds/win.wav')),
                'flag_put': QSound(getUrl('./sounds/flag_put.wav')),
                'flag_take_off': QSound(getUrl('./sounds/flag_take_off.wav'))
            }

    def change_volume(self, value):

        if self._is_gstreamer:
            for key in self._sounds:
                self._sounds[key].setVolume(value * 0.01)
        else:
            return False


def make_cursor(url, size=60):

    pixmap = QPixmap(url)
    pixmap = pixmap.scaled(size, size)
    return QCursor(pixmap)

def getUrl(url):

    return os.path.join(basedir, url)

def check_gstreamer():

    return 'gi.repository.Gst' in [modname for _, modname, _ in pkgutil.iter_modules()]


if (__name__ == '__main__'):

    basedir = os.path.dirname(__file__)
    app = QApplication(sys.argv)

    cursorShovel = make_cursor(getUrl('./image/cursor/shovel.bmp'))
    cursorMetalDetector = make_cursor(getUrl('./image/cursor/metalDetector.bmp'))
    cursorDefault = make_cursor(getUrl('./image/cursor/default.bmp'))
    cursorHover = make_cursor(getUrl('./image/cursor/hover.bmp'))


    settings_game = Settings()
    sound = Sounds()
    game = Game()
    window = Window()

    window.show()
    game.restart()

    sys.exit(app.exec_())
