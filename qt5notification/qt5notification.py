#!/usr/bin/python3

# v. 1.3

from cfg import *
if SOUND_PLAYER == 2:
    import gi
    gi.require_version('GSound', '1.0')
    from gi.repository import GSound
import dbus.service as Service
import dbus 
from PyQt5.QtWidgets import QApplication, qApp, QWidget, QPushButton, QVBoxLayout, QHBoxLayout, QLabel, QSizePolicy
# if VOLUME_STYLE:
    # from PyQt5.QtWidgets import QProgressBar
from PyQt5.QtGui import QIcon, QPixmap, QScreen, QPalette
from PyQt5.QtCore import QCoreApplication, Qt, QTimer
from dbus.mainloop.pyqt5 import DBusQtMainLoop
mainloop = DBusQtMainLoop(set_as_default=True)
import sys, os
USE_XDG = 1
if USE_XDG:
    from xdg import DesktopEntry
    from xdg import IconTheme

if ICON_THEME:
    QIcon.setThemeName(ICON_THEME)

# VOL_DIFF = 0
# if VOLUME_WIDTH < MIN_WIDTH:
    # VOL_DIFF = (MIN_WIDTH-VOLUME_WIDTH)

screen = None
SCREEN_WIDTH = 0
SCREEN_HEIGHT = 0

import signal
signal.signal(signal.SIGINT, signal.SIG_DFL)

# this program manages the notification position: 1 yes - 0 no
SELF_POSITIONING=1

def dbus_to_python(data):
    if isinstance(data, dbus.String):
        data = str(data)
    elif isinstance(data, dbus.Boolean):
        data = bool(data)
    elif isinstance(data, dbus.Int64):
        data = int(data)
    elif isinstance(data, dbus.Double):
        data = float(data)
    elif isinstance(data, dbus.Byte):
        data = int(data)
    elif isinstance(data, dbus.UInt32):
        data = int(data)
    elif isinstance(data, dbus.Array):
        data = [dbus_to_python(value) for value in data]
    elif isinstance(data, dbus.Dictionary):
        new_data = dict()
        for key in data.keys():
            new_data[dbus_to_python(key)] = dbus_to_python(data[key])
        data = new_data
    return data


class Notifier(Service.Object):
    
    def __init__(self, conn, bus):
        Service.Object.__init__(self, object_path = "/org/freedesktop/Notifications", bus_name = Service.BusName(bus, conn))
        self.message = 0
        self.widget = None
        # win - replacesId
        self.win_notifications = {}
        # y position of the next notification
        self.y = 0
        # window - replacesId
        self.list_notifications = {}
        #

    @Service.method("org.freedesktop.Notifications", out_signature="as")
    def GetCapabilities(self):
        return ["actions", "action-icons", "body", "body-markup", "body-hyperlinks", "body-images", "icon-static", "sound"]
        
    @Service.method("org.freedesktop.Notifications", in_signature="susssasa{sv}i", out_signature="u")
    def Notify(self, appName, replacesId, appIcon, summary, body, actions, hints, expireTimeout):
        # skip these applications
        if appName in SKIP_APPS:
            return replacesId
        #
        action_1 = dbus_to_python(actions)
        #
        replacesId = dbus_to_python(replacesId)
        if not replacesId:
            replacesdId = 0
        # # 1 is reserved to x-canonical-private-synchronous
        # if replacesId == 1:
            # replacesId = 2
        # # custom hint: x-canonical-private-synchronous
        # if "x-canonical-private-synchronous" in hints:
            # replacesId = 1
        #
        if not dbus_to_python(appIcon):
            appIcon = ""
        if action_1:
            if expireTimeout == -1:
                expireTimeout = 10000
            self._qw(appName, summary, body, replacesId, action_1, hints, expireTimeout, appIcon)
        else:
            action = []
            self._qw(appName, summary, body, replacesId, action_1, hints, expireTimeout, appIcon)
        #
        self.message += 1
        return replacesId

    @Service.method("org.freedesktop.Notifications", in_signature="u")
    def CloseNotification(self, id):
        # reasons: 1 expired - 2 dismissed by the user - 3 from here - 4 other
        self.NotificationClosed(id, 3)

    @Service.method("org.freedesktop.Notifications", out_signature="ssss")
    def GetServerInformation(self):
        return ("qt5notification-server", "Homebrew", "1.0", "0.1")

    @Service.signal("org.freedesktop.Notifications", signature="uu")
    def NotificationClosed(self, id, reason):
        pass

    @Service.signal("org.freedesktop.Notifications", signature="us")
    def ActionInvoked(self, id, actionKey):
        pass
    
    @Service.signal("org.freedesktop.Notifications", signature="us")
    def ActivationToken(self, id, actionKey):
        pass
    
    # find the notification from its replacesId
    def _find_notification(self, rid):
        if rid == 0:
            return None
        if self.win_notifications == {}:
            return None
        for ww in self.win_notifications:
            if self.win_notifications[ww] == rid:
                if not ww.isHidden():
                    return ww
        return None
    
    # action button pressed
    def _on_button_callback(self, ww, _replaceid, _aa):
        self.ActionInvoked(_replaceid, _aa)
        #
        if ww in self.win_notifications:
            del self.win_notifications[ww]
        if ww in self.list_notifications:
            del self.list_notifications[ww]
        #
        ww.destroy()
    

    # find and return the hint
    def _on_hints(self, _hints, _value):
        if _value in _hints:
            return _hints[_value]
        return None
    
    # find the icon from the desktop file
    def _on_desktop_entry(self, _desktop):
        app_dirs_user = [os.path.join(os.path.expanduser("~"), ".local/share/applications")]
        app_dirs_system = ["/usr/share/applications", "/usr/local/share/applications"]
        _ddir = app_dirs_user+app_dirs_system
        for dd in _ddir:
            if not os.path.exists(dd):
                continue
            for ff in os.listdir(dd):
                if ff == _desktop:
                    entry = DesktopEntry.DesktopEntry(os.path.join(dd, _desktop))
                    icon = entry.getIcon()
                    return icon
        return None
    
    # close button pressed
    def _on_btn_close(self, ww, id):
        self.NotificationClosed(id, 3)
        #
        if ww in self.win_notifications:
            del self.win_notifications[ww]
        if ww in self.list_notifications:
            del self.list_notifications[ww]
        #
        ww.destroy()
    

    def _qw(self, _appname, _summ, _body, _replaceid, _action, _hints, _timeout, _icon):
        ww = self._find_notification(_replaceid)
        #
        old_wgeom = None
        if ww:
            old_wgeom = ww.geometry()
            if ww.timer:
                ww.timer.stop()
                if ww in self.win_notifications:
                    del self.win_notifications[ww]
                if ww in self.list_notifications:
                    del self.list_notifications[ww]
        #
        if NOT_COLOR != "":
            qApp.setStyleSheet("#mainwin {0} background-color:{4}; border:{1}px solid {2} {3}".format("{", BORDER_SIZE, BORDER_COLOR, "}", NOT_COLOR))
        else:
            qApp.setStyleSheet("#mainwin {0} border:{1}px solid {2} {3}".format("{", BORDER_SIZE, BORDER_COLOR, "}"))
        #
        wnotification = QWidget()
        wnotification.setContentsMargins(4,4,4,4)
        wnotification.setFocusPolicy(0)
        wnotification.setObjectName("mainwin")
        if WIDGETS_FONT_COLOR != "":
            wnotification.setStyleSheet("QLabel, QPushButton {0}color:{1};{2}".format("{", WIDGETS_FONT_COLOR, "}"))
        wnotification.timer = None
        wnotification.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Expanding)
        wnotification.setAttribute(Qt.WA_X11NetWmWindowTypeNotification)
        wnotification.setWindowFlags(wnotification.windowFlags() | Qt.FramelessWindowHint)
        #
        if old_wgeom:
            wnotification.setGeometry(old_wgeom)
        else:
            if self.y == 0 or self.list_notifications == {}:
                yy = YPAD
            else:
                yy = self.y+4
            # #
            # if _replaceid == 1:
                # wnotification.setGeometry(SCREEN_WIDTH-MIN_WIDTH+VOL_DIFF-XPAD, yy, MIN_WIDTH, 10)
            # else:
            wnotification.setGeometry(SCREEN_WIDTH-MIN_WIDTH-XPAD, yy, MIN_WIDTH, 10)
        #
        _is_found = 0
        for ewin in self.list_notifications:
            if self.list_notifications[ewin] == _replaceid:
                _is_found = 1
                break
        if _is_found == 0:
            self.list_notifications[wnotification] = _replaceid
        #
        vbox = QVBoxLayout()
        vbox.setContentsMargins(0,0,0,0)
        wnotification.setLayout(vbox)
        #
        _desktop_entry = self._on_hints(_hints, "desktop-entry")
        ret_icon = None
        if _desktop_entry and USE_XDG:
            ret_icon = self._on_desktop_entry(os.path.basename(_desktop_entry))
        # 
        # if VOLUME_STYLE:
            # global USE_APP_NAME
            # _OLD_APP_NAME = USE_APP_NAME
            # _value = None
            # if _replaceid == 1:
                # if "%" in _summ:
                    # _value = _summ.split(" ")[-1].strip("%")
                    # try:
                        # _value = int(_value)
                    # except:
                        # # guess a muted state
                        # _value = 0
                    # #
                    # if _value >= 0:
                        # USE_APP_NAME = 2
        #
        if USE_APP_NAME == 1:
            hbox1 = QHBoxLayout()
            hbox1.setContentsMargins(0,0,0,0)
            vbox.addLayout(hbox1)
            # icon
            if ret_icon:
                if QIcon.hasThemeIcon(ret_icon):
                    qicn = QIcon.fromTheme(ret_icon)
                    wicon = qicn.pixmap(p_lbl.size())
            else:
                _image_path = self._on_hints(_hints, "image-path")
                if _image_path:
                    wicon = QPixmap(_image_path)
                #
                else:
                    if not _icon:
                        wicon = QPixmap("icons/wicon.png")
                    else:
                        if QIcon.hasThemeIcon(_icon):
                            qicn = QIcon.fromTheme(_icon)
                            wicon = qicn.pixmap(p_lbl.size())
                        elif QIcon.hasThemeIcon(_icon.strip("-symbolic")):
                            qicn = QIcon.fromTheme(_icon)
                            wicon = qicn.pixmap(p_lbl.size())
                        else:
                            wicon = QPixmap(_icon)
                            if wicon.isNull():
                                wicon = QPixmap("icons/wicon.png")
            p_lbl.setPixmap(wicon.scaled(p_lbl.size(),Qt.IgnoreAspectRatio))
            hbox1.addWidget(p_lbl)
            # application name
            appname_lbl = QLabel(_appname)
            appname_lbl.setContentsMargins(0,0,0,0)
            hbox1.addWidget(appname_lbl, stretch=1, alignment=Qt.AlignHCenter)
            # close button
            if _replaceid == 0 or _replaceid > 1:
                cls_btn = QPushButton()
                cls_btn.setContentsMargins(0,0,0,0)
                cls_btn.setFlat(True)
                #
                if QIcon.hasThemeIcon("window-close"):
                    cls_btn.setIcon(QIcon.fromTheme("window-close"))
                else:
                    cls_btn.setIcon(QIcon("icons/window-close.png"))
                hbox2.addWidget(cls_btn)
                cls_btn.clicked.connect(lambda:self._on_btn_close(wnotification, _replaceid))
            ### summary
            hbox2 = QHBoxLayout()
            hbox2.setContentsMargins(0,0,0,0)
            vbox.addLayout(hbox2)
            p_lbl = QLabel()
            p_lbl.setContentsMargins(0,0,0,0)
            p_lbl.resize(ICON_SIZE, ICON_SIZE)
            # # icon
            # if ret_icon:
                # if QIcon.hasThemeIcon(ret_icon):
                    # qicn = QIcon.fromTheme(ret_icon)
                    # wicon = qicn.pixmap(p_lbl.size())
            # else:
                # _image_path = self._on_hints(_hints, "image-path")
                # if _image_path:
                    # wicon = QPixmap(_image_path)
                # #
                # else:
                    # if not _icon:
                        # wicon = QPixmap("icons/wicon.png")
                    # else:
                        # if QIcon.hasThemeIcon(_icon):
                            # qicn = QIcon.fromTheme(_icon)
                            # wicon = qicn.pixmap(p_lbl.size())
                        # elif QIcon.hasThemeIcon(_icon.strip("-symbolic")):
                            # qicn = QIcon.fromTheme(_icon)
                            # wicon = qicn.pixmap(p_lbl.size())
                        # else:
                            # wicon = QPixmap(_icon)
                            # if wicon.isNull():
                                # wicon = QPixmap("icons/wicon.png")
            # #
            # p_lbl.setPixmap(wicon.scaled(p_lbl.size(),Qt.IgnoreAspectRatio))
            # hbox2.addWidget(p_lbl)
            # summary
            summary_lbl = QLabel(_summ)
            hbox2.addWidget(summary_lbl, alignment=Qt.AlignLeft)
        #
        elif USE_APP_NAME == 0:
            hbox2 = QHBoxLayout()
            hbox2.setContentsMargins(0,0,0,0)
            vbox.addLayout(hbox2)
            # icon label
            p_lbl = QLabel()
            p_lbl.setContentsMargins(0,0,0,0)
            p_lbl.resize(ICON_SIZE, ICON_SIZE)
            # icon - image-data image-path appIcon
            if ret_icon:
                if QIcon.hasThemeIcon(ret_icon):
                    qicn = QIcon.fromTheme(ret_icon)
                    wicon = qicn.pixmap(p_lbl.size())
            else:
                _image_path = self._on_hints(_hints, "image-path")
                if _image_path:
                    wicon = QPixmap(_image_path)
                    if wicon.isNull():
                        if QIcon.hasThemeIcon(_image_path):
                            qicn = QIcon.fromTheme(_image_path)
                            wicon = qicn.pixmap(p_lbl.size())
                        else:
                            wicon = QPixmap("icons/wicon.png")
                #
                else:
                    if not _icon:
                        wicon = QPixmap("icons/wicon.png")
                    else:
                        if QIcon.hasThemeIcon(_icon):
                            qicn = QIcon.fromTheme(_icon)
                            wicon = qicn.pixmap(p_lbl.size())
                        elif QIcon.hasThemeIcon(_icon.strip("-symbolic")):
                            qicn = QIcon.fromTheme(_icon)
                            wicon = qicn.pixmap(p_lbl.size())
                        else:
                            wicon = QPixmap(_icon)
                            if wicon.isNull():
                                wicon = QPixmap("icons/wicon.png")
            #
            p_lbl.setPixmap(wicon.scaled(p_lbl.size(),Qt.IgnoreAspectRatio))
            hbox2.addWidget(p_lbl)
            # summary
            summary_lbl = QLabel(_summ)
            summary_lbl.setContentsMargins(0,0,0,0)
            hbox2.addWidget(summary_lbl, stretch=1, alignment=Qt.AlignLeft)
            # close button
            if _replaceid == 0 or _replaceid > 1:
                cls_btn = QPushButton()
                cls_btn.setContentsMargins(0,0,0,0)
                cls_btn.setFlat(True)
                #
                if QIcon.hasThemeIcon("window-close"):
                    cls_btn.setIcon(QIcon.fromTheme("window-close"))
                else:
                    # cls_btn.setText("x")
                    cls_btn.setIcon(QIcon("icons/window-close.png"))
                hbox2.addWidget(cls_btn)
                cls_btn.clicked.connect(lambda:self._on_btn_close(wnotification, _replaceid))
        #
        # elif USE_APP_NAME == 2:
            # hbox2 = QHBoxLayout()
            # hbox2.setContentsMargins(10,0,10,0)
            # vbox.addLayout(hbox2)
            # #
            # # icon label
            # p_lbl = QLabel()
            # p_lbl.setContentsMargins(0,0,0,0)
            # p_lbl.resize(ICON_SIZE, ICON_SIZE)
            # #
            # if not _icon:
                # wicon = QPixmap("icons/audio-volume-default.png")
            # else:
                # if QIcon.hasThemeIcon(_icon):
                    # qicn = QIcon.fromTheme(_icon)
                    # wicon = qicn.pixmap(p_lbl.size())
                # elif QIcon.hasThemeIcon(_icon.strip("-symbolic")):
                    # qicn = QIcon.fromTheme(_icon)
                    # wicon = qicn.pixmap(p_lbl.size())
                # else:
                    # wicon = QPixmap(_icon)
                    # if wicon.isNull():
                        # wicon = QPixmap("icons/audio-volume-default.png")
            # #
            # p_lbl.setPixmap(wicon.scaled(p_lbl.size(),Qt.IgnoreAspectRatio))
            # hbox2.addWidget(p_lbl)
            # # progress bar
            # pbar = QProgressBar()
            # pbar.setContentsMargins(0,0,0,0)
            # pbar.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Expanding)
            # pbar.setOrientation(Qt.Horizontal) 
            # pbar.setTextVisible(False)
            # if PBAR_COLOR:
                # pbar.setStyleSheet("::chunk {0}background-color:{1}; {2}".format("{",PBAR_COLOR,"}"))
            # pbar.setMaximumSize(16777215, PBAR_WIDTH)
            # pbar.setRange(0, 100)
            # hbox2.addWidget(pbar, stretch=1)
            # #
            # pbar.setValue(int(_value))
            # #
            # _body = ""
            # _action = None
            # USE_APP_NAME = _OLD_APP_NAME
            #
        #
        ### body
        if _body:
            hbox3 = QHBoxLayout()
            hbox3.setContentsMargins(0,0,0,0)
            #
            vbox.addLayout(hbox3)
            body_lbl = QLabel(_body)
            body_lbl.setContentsMargins(0,0,0,0)
            body_lbl.setIndent(20)
            #
            body_lbl.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Expanding)
            body_lbl.resize(body_lbl.sizeHint())
            body_lbl.update()
            if body_lbl.size().width() > MAX_WIDTH:
                body_lbl.setWordWrap(True)
                body_lbl.resize(body_lbl.sizeHint())
                body_lbl.update()
                # wnotification.resize(wnotification.sizeHint())
                # wnotification.update()
            #
            if Qt.mightBeRichText(_body):
                body_lbl.setTextFormat(Qt.RichText)
                body_lbl.setOpenExternalLinks(True)
            hbox3.addWidget(body_lbl)
        ### action buttons
        if _action:
            self.hbox_btn = QHBoxLayout()
            self.hbox_btn.setContentsMargins(0,0,0,0)
            self.hbox_btn.addStretch()
            vbox.addLayout(self.hbox_btn)
            for _ee in _action[::2]:
                btn_name = _action[_action.index(_ee)+1]
                self.act_btn = QPushButton(text=str(btn_name))
                self.act_btn.setContentsMargins(0,0,0,0)
                self.act_btn.setFlat(True)
                self.act_btn.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
                # border style of buttons
                # border_color = bcolor = self.act_btn.palette().color(QPalette.Text).name()
                border_color = BTN_BORDER_COLOR
                self.act_btn.setStyleSheet("border :2px solid ;"
                                         "border-color : {};".format(border_color))
                #
                self.act_btn.clicked.connect(lambda i,x=_ee:self._on_button_callback(wnotification, _replaceid, x))
                self.hbox_btn.addWidget(self.act_btn)
            self.hbox_btn.addStretch()
        #
        # if not _action:
        if 1:
            def _timer(tww):
                self.NotificationClosed(_replaceid, 3)
                if tww in self.win_notifications:
                    del self.win_notifications[tww]
                if tww in self.list_notifications:
                    del self.list_notifications[tww]
                #
                tww.hide()
                tww.destroy()
            #
            timer=QTimer()
            if _timeout == -1:
                _timeout = TIMEOUT
            timer.setSingleShot(True)
            timer.timeout.connect(lambda:_timer(wnotification))
            wnotification.timer = timer
        #
        if _replaceid > 0:
            self.win_notifications[wnotification] = _replaceid
        #
        wnotification.setWindowTitle("qt5notification")
        wnotification.show()
        if not ww:
            if _body:
                if body_lbl.wordWrap():
                    _MAX_WIDTH = max(MAX_WIDTH, body_lbl.size().width())
                    wnotification.resize(max(wnotification.sizeHint().width(), _MAX_WIDTH), wnotification.sizeHint().height())
                    wnotification.move(SCREEN_WIDTH-_MAX_WIDTH,wnotification.geometry().y())
                else:
                    # if _replaceid == 1:
                        # wnotification.resize(max(wnotification.sizeHint().width()-VOL_DIFF, MIN_WIDTH-VOL_DIFF), wnotification.sizeHint().height())
                    # else:
                    _MIN_WIDTH = max(MIN_WIDTH, body_lbl.size().width())
                    wnotification.resize(max(wnotification.sizeHint().width(), _MIN_WIDTH), wnotification.sizeHint().height())
                    wnotification.move(SCREEN_WIDTH-_MIN_WIDTH,wnotification.geometry().y())
            else:
                wnotification.resize(max(wnotification.sizeHint().width(), MIN_WIDTH), wnotification.sizeHint().height())
                wnotification.move(SCREEN_WIDTH-MIN_WIDTH,wnotification.geometry().y())
            wnotification.update()
        # remove old window
        else:
            ww.hide()
            ww.destroy()
        #
        wgeom = wnotification.geometry()
        if not ww:
            self.y = (wgeom.y()+wgeom.height())
        if self.y > SCREEN_HEIGHT:
            self.y = 0
        #
        # if not _action:
        if 1:
            timer.start(_timeout)
        #
        _no_sound = self._on_hints(_hints, "suppress-sound")
        _soundfile = self._on_hints(_hints, "sound-file")
        #
        if not _soundfile:
            _soundfile = self._on_hints(_hints, "sound-name")
        if _no_sound and _soundfile:
            self._play_sound(_soundfile)
        else:
            if PLAY_STANDARD_SOUND:
                _urgency = self._on_hints(_hints, "urgency")
                if _urgency == 1:
                    self._play_sound("sounds/urgency-normal.wav")
                elif _urgency == 2:
                    self._play_sound("sounds/urgency-critical.wav")

    # sound event player
    def _play_sound(self, _sound):
        if SOUND_PLAYER == 2:
            try:
                ctx = GSound.Context()
                ctx.init()
                ret = ctx.play_full({GSound.ATTR_EVENT_ID: _sound})
                if ret == None:
                    ret = ctx.play_full({GSound.ATTR_MEDIA_FILENAME: _sound})
            except:
                pass
        #
        elif isinstance(SOUND_PLAYER, str):
            try:
                os.system("{0} {1} &".format(SOUND_PLAYER, _sound))
            except:
                pass

if __name__ == '__main__':
    app = QApplication(sys.argv)
    screen = app.primaryScreen()
    SCREEN_WIDTH = screen.size().width()
    SCREEN_HEIGHT = screen.size().height()
    #
    def on_screen_changed(rect_data):
        SCREEN_WIDTH, SCREEN_HEIGHT = rect_data.width(), rect_data.height()
    screen.geometryChanged.connect(on_screen_changed)
    #
    conn = dbus.SessionBus(mainloop = mainloop)
    Notifier(conn, "org.freedesktop.Notifications")
    #
    ret = app.exec_()
    sys.exit(ret)
