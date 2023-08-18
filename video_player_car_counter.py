from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QHBoxLayout, QVBoxLayout, QLabel, \
    QSlider, QStyle, QSizePolicy, QFileDialog, QComboBox, QRadioButton, QShortcut, QMessageBox
import sys
import csv
import os
import locale
import socket
import getpass
locale.setlocale(locale.LC_ALL, '')
from datetime import datetime
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtMultimediaWidgets import QVideoWidget
from PyQt5.QtGui import QIcon, QPalette, QKeySequence
from PyQt5.QtCore import Qt, QUrl, QTimer

"""
Author: Diyi Liu (www.diyi93.com) (https://github.com/thefriedbee/)

v1.01: add delete last entry function to delete last wrong inputs
v1.02: add negative play speed to rewind videos
v1.03: create different filename for different user
v1.04: force font size (18), color (black), bolded, Arial text. 
        set black button bolders
        Fullscreened after opened.
"""


class Window(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("UTK Car Counter v1.05, based on PyQt5 mdeia player")
        self.setGeometry(350, 100, 700, 500)
        # self.setWindowIcon(QIcon('player.png'))

        self.p = self.palette()
        self.p.setColor(QPalette.Window, Qt.white)
        self.setPalette(self.p)

        self.init_ui()
        self.init_shortcuts()
        self.csv_path = None

        self.show()

    def init_shortcuts(self):  # init shortcuts for fast recordings
        self.sc_truck = QShortcut(
            QKeySequence('t'),
            self.veh_cb, activated=lambda: self.change_veh_input('t'))
        self.sc_car = QShortcut(
            QKeySequence('c'),
            self.veh_cb, activated=lambda: self.change_veh_input('c'))
        self.sc_lane1 = QShortcut(
            QKeySequence('1'),
            self.lane_cb, activated=lambda: self.change_lane_input('1'))
        self.sc_lane2 = QShortcut(
            QKeySequence('2'),
            self.lane_cb, activated=lambda: self.change_lane_input('2'))
        self.sc_lane3 = QShortcut(
            QKeySequence('3'),
            self.lane_cb, activated=lambda: self.change_lane_input('3'))
        self.sc_lane4 = QShortcut(
            QKeySequence('4'),
            self.lane_cb, activated=lambda: self.change_lane_input('4'))
        self.sc_lane5 = QShortcut(
            QKeySequence('5'),
            self.lane_cb, activated=lambda: self.change_lane_input('5'))
        self.sc_lane6 = QShortcut(
            QKeySequence('6'),
            self.lane_cb, activated=lambda: self.change_lane_input('6'))
        self.submitBtn.setShortcut("Return")
        self.withdrawBtn.setShortcut("d")
        # option: frame by frame player shortcuts

    def change_veh_input(self, veh_type):
        if veh_type == 't':
            self.veh_cb.setCurrentText('Truck')
        if veh_type == 'c':
            self.veh_cb.setCurrentText('Car')

    def change_lane_input(self, lane_n):
        if lane_n in ['1', '2', '3', '4', '5']:
            self.lane_cb.setCurrentText(lane_n)

    def init_ui(self):
        self.filename = None
        # create media player object
        self.mediaPlayer = QMediaPlayer(None, QMediaPlayer.VideoSurface)

        # create videowidget object
        videowidget = QVideoWidget()

        # create open button
        openBtn = QPushButton('Open Video')
        openBtn.setStyleSheet("""
            QPushButton {
                font: bold;
                font-family: Arial;
                color: black;
                font-size: 18pt;
            }
            """)
        openBtn.clicked.connect(self.open_file)

        # store my font settings
        my_font = """
        {   font: bold; 
            font-family: Arial;
            color: black;
            font-size: 18pt;
        }
        """
        # create button for playing
        self.playBtn = QPushButton()
        self.playBtn.setEnabled(False)
        self.playBtn.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        self.playBtn.clicked.connect(self.play_video)
        # create a set of buttons for entering data (lane number, vehicle type, submit)
        self.veh_cb = QComboBox()
        self.veh_cb.addItems(["Car", 'Truck'])
        self.veh_cb.setStyleSheet("QComboBox {}".format(my_font))
        self.lane_cb = QComboBox()
        self.lane_cb.addItems(["1", '2', '3', '4', '5', '6'])
        self.lane_cb.setStyleSheet("QComboBox {}".format(my_font))
        self.submitBtn = QPushButton('Enter')
        self.submitBtn.setStyleSheet("QPushButton {}".format(my_font))

        self.submitBtn.clicked.connect(self.update_submit)
        self.withdrawBtn = QPushButton('Delete Last Entry')
        self.withdrawBtn.setStyleSheet("QPushButton {}".format(my_font))
        self.withdrawBtn.clicked.connect(self.withdraw_record)
        # create slider
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setStyleSheet("QSlider {}".format(my_font))
        self.slider.setRange(0, 0)
        self.slider.sliderMoved.connect(self.set_position)
        # play speed slider
        self.speed_cb = QComboBox()
        self.speed_cb.addItems(["1.0", '0.75', '0.5', '0.25',
                                '-1.0', '-0.75', '-0.5', '-0.25', "1.5", "2.0"])
        self.speed_cb.setStyleSheet("QComboBox {}".format(my_font))
        self.speed_cb.currentIndexChanged.connect(self.selectionchangeSpeed)

        # create label
        self.label = QLabel()
        self.label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        self.label.setText('Milliseconds:')
        self.label.setStyleSheet("QLabel {}".format(my_font))
        # create speed label
        speed_label = QLabel()
        speed_label.setText('Play Speed:')
        speed_label.setStyleSheet("QLabel {}".format(my_font))
        speed_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        veh_label = QLabel()
        veh_label.setText('Car Type:')
        veh_label.setStyleSheet("QLabel {}".format(my_font))
        veh_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        lane_label = QLabel()
        lane_label.setText('Lane #:')
        lane_label.setStyleSheet("QLabel {}".format(my_font))
        lane_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        # create hbox layout
        hboxLayout1 = QHBoxLayout()
        hboxLayout1.setContentsMargins(0, 0, 0, 0)
        hboxLayout2 = QHBoxLayout()
        hboxLayout2.setContentsMargins(0, 0, 0, 0)

        # set widgets to the hbox layout
        hboxLayout1.addWidget(openBtn)
        hboxLayout1.addWidget(speed_label)
        hboxLayout1.addWidget(self.speed_cb)
        hboxLayout1.addWidget(self.playBtn)
        hboxLayout1.addWidget(self.slider)
        # set second row of widgets
        hboxLayout2.addWidget(lane_label)
        hboxLayout2.addWidget(self.lane_cb)
        hboxLayout2.addWidget(veh_label)
        hboxLayout2.addWidget(self.veh_cb)
        hboxLayout2.addWidget(self.submitBtn)
        hboxLayout2.addWidget(self.withdrawBtn)

        # create vbox layout
        vboxLayout = QVBoxLayout()
        vboxLayout.addWidget(videowidget)
        vboxLayout.addLayout(hboxLayout1)
        vboxLayout.addLayout(hboxLayout2)
        vboxLayout.addWidget(self.label)

        self.setLayout(vboxLayout)

        self.mediaPlayer.setVideoOutput(videowidget)

        # media player signals
        self.mediaPlayer.stateChanged.connect(self.mediastate_changed)
        self.mediaPlayer.positionChanged.connect(self.position_changed)
        self.mediaPlayer.durationChanged.connect(self.duration_changed)

    def open_file(self):
        filepath, _ = QFileDialog.getOpenFileName(self, "Open Video")

        if filepath != '':
            self.mediaPlayer.setMedia(
                QMediaContent(QUrl.fromLocalFile(filepath)))
            self.playBtn.setEnabled(True)
            self.filename = filepath.split(os.sep)[-1].split('.')[0]
            sys_name = socket.gethostname()
            user_name = getpass.getuser()
            self.csv_path = '{}_vehicle_counts_{}_{}.csv'.format(
                filepath.split('.')[0], sys_name, user_name)
            # print(self.csv_path)

    def play_video(self):
        # print position here
        print('current media postiion:', self.mediaPlayer.position())
        self.update_label()
        if self.mediaPlayer.state() == QMediaPlayer.PlayingState:
            self.mediaPlayer.pause()
        else:
            self.mediaPlayer.play()

    def mediastate_changed(self, state):
        if self.mediaPlayer.state() == QMediaPlayer.PlayingState:
            self.playBtn.setIcon(
                self.style().standardIcon(QStyle.SP_MediaPause)
            )

        else:
            self.playBtn.setIcon(
                self.style().standardIcon(QStyle.SP_MediaPlay)
            )

    def position_changed(self, position):
        self.update_label()
        self.slider.setValue(position)

    def duration_changed(self, duration):
        self.slider.setRange(0, duration)

    def set_position(self, position):
        self.update_label()
        self.mediaPlayer.setPosition(position)

    def handle_errors(self):
        self.playBtn.setEnabled(False)
        self.label.setText("Error: " + self.mediaPlayer.errorString())

    # update information box at bottom left
    def update_label(self):
        self.label.setText('Mili-seconds: {}; Play Rate {}'.format(
            self.mediaPlayer.position(), self.mediaPlayer.playbackRate()))

    # update player speed
    def selectionchangeSpeed(self, i):
        curr_speed = round(float(self.speed_cb.currentText()), 2)
        self.mediaPlayer.setPlaybackRate(curr_speed)
        self.update_label()

    # open video checker
    def check_video_opened(self):
        if not self.csv_path:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setText("No video opened! Should open a video before collecting data")
            msg.setWindowTitle("Warning: Video not loaded in the media player")
            msg.exec_()
            return False
        return True

    # submit data, gather milliseconds number, lane # and vehicle type
    def update_submit(self):
        if not self.check_video_opened():
            return None
        now = datetime.now()
        # dd/mm/YY H:M:S
        dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
        # get milliseconds of video
        pos = self.mediaPlayer.position()
        ln = int(self.lane_cb.currentText())
        car_type = self.veh_cb.currentText()
        file_exists = os.path.isfile(self.csv_path)
        with open(self.csv_path, 'a') as f:
            writer = csv.writer(f, lineterminator='\n')
            if not file_exists:
                writer.writerow(['milliseconds', 'lane_number',
                                 'veh_type', 'add_dt'])
            writer.writerow([pos, ln, car_type, dt_string])
        print('A row is written to csv: Ms {:n}, lane {}, type {}, record_str {}'.format(
            pos, ln, car_type, dt_string))
        # change background color for 0.3 second for indication that
        self.change_background(Qt.green)
        self.my_timer = QTimer(self)
        self.my_timer.setInterval(300)
        self.my_timer.timeout.connect(lambda: self.change_background(Qt.white))
        self.my_timer.start()

    def withdraw_record(self):
        if not self.check_video_opened():
            return None
        lines = []
        with open(self.csv_path, 'r') as f:
            lines = f.readlines()
            # delete '\n' character
            lines = [line[:-1] for line in lines]
            lines = lines[:-1]
            print(lines)
        with open(self.csv_path, 'w', newline='') as f:
            if len(lines) == 0:
                return
            writer = csv.writer(f, lineterminator='\n')
            for line in lines:
                writer.writerow(line.split(','))
            print('A row is deleted')
            print(lines)
        self.change_background(Qt.red)
        self.my_timer = QTimer(self)
        self.my_timer.setInterval(300)
        self.my_timer.timeout.connect(lambda: self.change_background(Qt.white))
        self.my_timer.start()

    def change_background(self, color):
        self.p.setColor(QPalette.Window, color)
        self.setPalette(self.p)


app = QApplication(sys.argv)
window = Window()
window.showMaximized()
sys.exit(app.exec_())
