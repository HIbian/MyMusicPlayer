import configparser
import os.path
import sys

from PyQt5.QtWidgets import QApplication, QMainWindow, QListWidgetItem, QFileDialog
from PyQt5.QtMultimedia import QMediaPlayer, QMediaResource, QMediaContent, QMediaPlaylist
from PyQt5.QtCore import QTimer, QUrl
from PyQt5.QtGui import QIcon
import pyui
from enum import Enum
import qtawesome as qta


def secend2timelabel(second):
    if not second:
        return "00:00"
    second = int(second / 1000)
    min = int(second / 60)
    sec = second % 60
    return '{:0>2d}:{:0>2d}'.format(min, sec)


class UiFromAddLogic(pyui.Ui_MyMusicPlayer):
    def __init__(self, mainWindow):
        super().__init__()
        self.setupUi(mainWindow)
        self.settingname = 'setting.music'
        self.format_list = ('mp3', 'flac', 'm4a', 'wav')
        self.play_list = []
        self.playlist = QMediaPlaylist()
        self.jump = False
        self.press_go_to_next = False
        self.player = QMediaPlayer()  # 使用解码器支持更多格式 http://www.codecguide.com/download_kl.htm
        self.timer = QTimer()
        self.initLogic()

    def initLogic(self):
        # 初始化配置文件
        self.initSetting()
        # 初始化播放列表
        self.initPlayList()
        # 初始化音量
        self.initVolume()
        # 初始化播放模式
        self.initPlayMode()
        # 计时器
        self.timer.start(200)
        self.timer.timeout.connect(self.update)
        # 进度条
        self.horizontalSlider.sliderPressed.connect(self.jump_start)
        self.horizontalSlider.sliderReleased.connect(self.jump_finish)
        # 播放按钮
        self.play_btn.clicked.connect(self.playorpause)
        # 播放列表
        self.listWidget.itemDoubleClicked.connect(self.doubleClickedPlay)
        # 下一首/上一首
        self.next_btn.clicked.connect(self.next)
        self.before_btn.clicked.connect(self.before)
        # 音量按钮
        self.voice.valueChanged.connect(self.voiceChange)
        # 导入播放列表
        self.input_btn.clicked.connect(self.importMusic)
        # 更改播放模式
        self.order_list.currentIndexChanged.connect(self.modeChange)

        self.play_btn.setIcon(qta.icon('fa5s.play'))

    def initSetting(self):
        if os.path.isfile(self.settingname):
            return
        config = configparser.ConfigParser()
        config.read(self.settingname, encoding='utf-8')
        config.add_section('MUSIC')
        config.set('MUSIC', 'PLAY_MODE', str(QMediaPlaylist.Sequential.real))
        config.write(open(self.settingname, 'w', encoding='utf-8'))

    def initPlayMode(self):
        config = configparser.ConfigParser()
        config.read(self.settingname, encoding='utf-8')
        play_mode = int(config.get('MUSIC', 'PLAY_MODE'))
        self.playlist.setPlaybackMode(play_mode)
        self.order_list.setCurrentIndex(play_mode)

    def modeChange(self):
        self.playlist.setPlaybackMode(self.order_list.currentIndex())
        config = configparser.ConfigParser()
        config.read(self.settingname, encoding='utf-8')
        config.set('MUSIC', 'PLAY_MODE', str(self.playlist.playbackMode().real))
        config.write(open(self.settingname, 'w', encoding='utf-8'))

    def voiceChange(self):
        self.player.setVolume(self.voice.value())

    def initPlayList(self):
        if not os.path.exists(self.settingname):
            return []
        if not os.path.isfile(self.settingname):
            return []
        config = configparser.ConfigParser()
        config.read(self.settingname, encoding='utf-8')
        try:
            music_dir = config.get('MUSIC', 'PATH_DIR')
        except configparser.NoOptionError:
            return
        self.setMusicList(music_dir)
        self.showPlayList()

    '''根据路径获取音乐'''

    def setMusicList(self, music_dir):
        self.playlist.clear()
        self.play_list.clear()
        for music in os.listdir(music_dir):
            if music.split('.')[-1] in self.format_list:
                self.play_list.append(music_dir + '/' + music)
                self.playlist.addMedia(QMediaContent(QMediaResource(QUrl(music_dir + '/' + music))))
        self.playlist.setCurrentIndex(0)

    '''刷新播放列表'''

    def showPlayList(self):
        self.listWidget.clear()
        order = 0
        for i in range(0, self.playlist.mediaCount()):
            item = QListWidgetItem()
            item.setText(self.playlist.media(i).resources()[0].url().url().split('/')[-1])
            self.listWidget.addItem(item)

    def update(self):

        if self.jump:
            # 进度条快进
            self.player.setPosition(self.horizontalSlider.value())
        if self.player.position() != 0 and self.player.position() == self.player.duration():
            # 当前歌曲播放完毕执行next()
            self.next()
        if self.play_btn.text() == 'pause' and not self.jump and not self.press_go_to_next:
            # 播放状态:更新进度条
            self.horizontalSlider.setMinimum(0)
            self.horizontalSlider.setMaximum(self.player.duration())
            self.horizontalSlider.setValue(self.player.position())
            # 更新时间
            # if self.player.state() == QMediaPlayer.PlayingState:
            self.len_time_lab.setText(secend2timelabel(self.player.duration()))
            self.played_time_lab.setText(secend2timelabel(self.player.position()))
        # print('------------------------')
        # print(datetime.datetime.today())
        # print(self.jump)
        # print(self.press_go_to_next)

    '''双击播放列表播放'''

    def doubleClickedPlay(self):
        # 初始化进度条，时间，播放暂停按钮
        self.resetPlayWith()
        selected = self.listWidget.selectedIndexes()[0].row()
        self.playlist.setCurrentIndex(selected)
        self.player.setMedia(self.playlist.currentMedia())
        self.player.play()
        self.play_btn.setText('pause')

    '''初始化进度条，时间，播放暂停按钮'''

    def resetPlayWith(self):
        self.player.stop()
        self.horizontalSlider.setMinimum(0)
        self.horizontalSlider.setValue(0)
        self.play_btn.setText('play')

    def playorpause(self):
        if self.player.state() == QMediaPlayer.PausedState:
            self.player.play()
            self.play_btn.setText('pause')
        else:
            self.player.pause()
            self.play_btn.setText('play')

    def jump_start(self):
        self.jump = True

    def jump_finish(self):
        self.jump = False

    # todo 使用偏函数合并next和before
    def next(self):
        self.playlist.next()
        self.listWidget.setCurrentRow(self.playlist.currentIndex())
        self.player.setMedia(self.playlist.currentMedia())
        self.player.play()

    def before(self):
        cindex = self.playlist.currentIndex()
        if cindex == 0:
            return
        self.listWidget.setCurrentRow(cindex - 1)
        self.playlist.setCurrentIndex(cindex - 1)
        self.player.setMedia(self.playlist.currentMedia())
        self.player.play()

    def importMusic(self):
        path = QFileDialog.getExistingDirectory()
        if path:
            self.setMusicList(path)
            self.showPlayList()
            config = configparser.ConfigParser()
            config.read(self.settingname, encoding='utf-8')
            config.set('MUSIC', 'PATH_DIR', path)
            config.write(open(self.settingname, 'w', encoding='utf-8'))

    def initVolume(self):
        self.voice.setValue(self.player.volume())


if __name__ == '__main__':
    app = QApplication(sys.argv)
    mainWindow = QMainWindow()
    form = UiFromAddLogic(mainWindow)
    mainWindow.show()
    sys.exit(app.exec_())
