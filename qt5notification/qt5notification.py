#!/usr/bin/python3

# v. 2.2.0

import shutil,time
from cfg import *
if SOUND_PLAYER == 2:
    import gi
    gi.require_version('GSound', '1.0')
    from gi.repository import GSound
if DO_NOT_SHOW > 0:
    import glob
import dbus.service as Service
import dbus 
from PyQt5.QtWidgets import QApplication, qApp, QWidget, QPushButton, QVBoxLayout, QHBoxLayout, QLabel, QSizePolicy
if SOUND_PLAYER == 1:
    from PyQt5.QtMultimedia import QSound
if VOLUME_STYLE:
    from PyQt5.QtWidgets import QProgressBar
from PyQt5.QtGui import QIcon, QPixmap, QScreen, QPalette, QFont
from PyQt5.QtCore import QCoreApplication, Qt, QTimer, QSize
from dbus.mainloop.pyqt5 import DBusQtMainLoop
mainloop = DBusQtMainLoop(set_as_default=True)
import sys, os
USE_XDG = 1
if USE_XDG:
    from xdg import DesktopEntry
    from xdg import IconTheme

if ICON_THEME:
    QIcon.setThemeName(ICON_THEME)

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

class NotSave():
    nname = None
    appname = None
    summary = None
    body = None
    icon = None

class Notifier(Service.Object):
    
    def __init__(self, conn, bus):
        Service.Object.__init__(self, object_path = "/org/freedesktop/Notifications", bus_name = Service.BusName(bus, conn))
        self.message = 0
        self.widget = None
        # win - replacesId - only with replaceId > 0
        self.win_notifications = {}
        # y position of the next notification
        self.y = 0
        # window - replacesId
        self.list_notifications = []
        # list of NotSave
        self.list_not_save = []
    
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
        # 1 is reserved to x-canonical-private-synchronous
        if replacesId == 1:
            replacesId = 2
        # custom hint: x-canonical-private-synchronous
        if "x-canonical-private-synchronous" in hints:
            replacesId = 1
        #
        if not dbus_to_python(appIcon):
            appIcon = ""
        if action_1:
            if expireTimeout == -1:
                expireTimeout = 10000
            self._qw(appName, summary, body, replacesId, action_1, hints, expireTimeout, appIcon)
        else:
            action_1 = []
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
        #
        for el in self.list_notifications:
            if el[0] == ww:
                self.list_notifications.remove(el)
                break
        #
        if self.list_notifications == []:
            self.y = 0
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
        #
        for el in self.list_notifications:
            if el[0] == ww:
                self.list_notifications.remove(el)
                break
        #
        if self.list_notifications == []:
            self.y = 0
        #
        if SKIP_CLOSED_BY_USER == 0 and hasattr(ww, "notname"):
            self._on_save_notification(ww.notname)
        #
        ww.destroy()
    
    def _timer(self, tww, _replaceid):
        self.NotificationClosed(_replaceid, 3)
        if tww in self.win_notifications:
            del self.win_notifications[tww]
        #
        for el in self.list_notifications:
            if el[0] == tww:
                self.list_notifications.remove(el)
                break
        #
        if self.list_notifications == []:
            self.y = 0
        #
        if hasattr(tww, "notname"):
            self._on_save_notification(tww.notname)
        #
        tww.hide()
        tww.destroy()
    
    #
    def _on_not_save(self, _appname, _summ, _body, _hints, _icon):
        _to_save = 0
        _not_name = None
        p_icon = None
        #
        if SAVE_NOTIFICATION == 1:
            if _appname not in SKIP_APPS2:
                _to_save = 1
        elif SAVE_NOTIFICATION == 2:
            if _appname in ONLY_APPS:
                _to_save = 1
        if "x-canonical-private-synchronous" in _hints:
            _to_save = 0
        #
        if _to_save == 1:
            if PATH_TO_STORE:
                if os.access(PATH_TO_STORE, os.W_OK):
                    _not_name =  str(int(time.time()))
                    _not_path = os.path.join(PATH_TO_STORE, _not_name)
                else:
                    return None
        #
        if _to_save == 1:
            _desktop_entry = self._on_hints(_hints, "desktop-entry")
            ret_icon = None
            if _desktop_entry and USE_XDG:
                ret_icon = self._on_desktop_entry(os.path.basename(_desktop_entry))
            #
            p_icon = self._find_icon(ret_icon, _icon, _hints, 64)
            #
        _not_data = NotSave()
        _not_data.nname = _not_name
        _not_data.appname = _appname
        _not_data.summary = _summ
        _not_data.body = _body
        if p_icon and not p_icon.isNull():
            _not_data.icon = p_icon
        #
        self.list_not_save.append(_not_data)
        #
        return _not_name
    
    # save the notification data
    def _on_save_notification(self, _not_name):
        ell = None
        for elll in self.list_not_save[:]:
            if elll.nname == _not_name:
                ell = elll
                break
        if ell:
            #
            _not_path = os.path.join(PATH_TO_STORE, _not_name)
            try:
                os.makedirs(_not_path)
            except:
                return -111
            #
            if not os.access(_not_path, os.W_OK):
                return -112
            #
            _appname = ell.appname
            _summ = ell.summary
            _body = ell.body
            # notification text
            try:
                ff = open(os.path.join(_not_path, "notification"), "w")
                ff.write(_appname+"\n\n\n@\n\n\n"+_summ+"\n\n\n@\n\n\n"+_body)
                ff.close()
                # notification icon
                _pix = ell.icon
                if _pix:
                    _pix.save(os.path.join(_not_path, "icon"), "PNG")
            except:
                return -113
            #
            self.list_not_save.remove(ell)
    
    def _find_icon(self, ret_icon, _icon, _hints, p_lbl_size):
        wicon = None
        # icon - image-data image-path appIcon
        if ret_icon:
            if QIcon.hasThemeIcon(ret_icon):
                qicn = QIcon.fromTheme(ret_icon)
                wicon = qicn.pixmap(p_lbl_size)
        # else:
        if not wicon or wicon.isNull():
            _image_path = self._on_hints(_hints, "image-path")
            if _image_path:
                wicon = QPixmap(_image_path)
                if wicon.isNull():
                    if QIcon.hasThemeIcon(_image_path):
                        qicn = QIcon.fromTheme(_image_path)
                        wicon = qicn.pixmap(p_lbl_size)
                    else:
                        wicon = QPixmap("icons/wicon.png")
            #
            else:
                if not _icon:
                    wicon = QPixmap("icons/wicon.png")
                else:
                    if QIcon.hasThemeIcon(_icon):
                        qicn = QIcon.fromTheme(_icon)
                        wicon = qicn.pixmap(p_lbl_size)
                    elif QIcon.hasThemeIcon(_icon.strip("-symbolic")):
                        qicn = QIcon.fromTheme(_icon)
                        wicon = qicn.pixmap(p_lbl_size)
                    else:
                        wicon = QPixmap(_icon)
                        if wicon.isNull():
                            wicon = QPixmap("icons/wicon.png")
        #
        return wicon
    
    def _qw(self, _appname, _summ, _body, _replaceid, _action, _hints, _timeout, _icon):
        # notification folder name in which to save itself
        _not_name = None
        if SAVE_NOTIFICATION != 0:
            # do not save if this property is setted
            d_transient = self._on_hints(_hints, "transient")
            if d_transient == None or d_transient == 0:
                _not_name = self._on_not_save(_appname, _summ, _body, _hints, _icon)
        # do not show the notification
        _do_not_show = 0
        if DO_NOT_SHOW > 0:
            try:
                _dfile = glob.glob("notificationdonotuse_*")[0].split("_")[-1]
            except:
                _dfile = 0
            if _dfile in ["1","2","3"]:
                _do_not_show = int(_dfile)
        if DO_NOT_SHOW > 0 and _do_not_show != 0:
            d_urgency = self._on_hints(_hints, "urgency")
            if d_urgency == None:
                d_urgency = 1
            if _do_not_show > int(d_urgency):
                if _not_name:
                    self._on_save_notification(_not_name)
                return
        # for replacing the previous notification with same id
        ww = self._find_notification(_replaceid)
        _is_volume_style_notification = None
        if ww and _replaceid == 1:
            _is_volume_style_notification = ww
            if ww.timer.isActive():
                ww.timer.stop()
                _timer = ww.timer
                _timer.deleteLater()
        if  _is_volume_style_notification != None:
            try:
                # widgets in ww: QHBoxLayout QLabel_icon QLabel_value QProgressBar
                label_icon = None
                label_value = None
                progress_bar = None
                for child in ww.children():
                    if isinstance(child, QLabel):
                        if child.pixmap():
                            label_icon = child
                        else:
                            if SHOW_VALUE == 1:
                                label_value = child
                    elif isinstance(child, QProgressBar):
                        progress_bar = child
                #
                if progress_bar == None:
                    if ww in self.win_notifications:
                        del self.win_notifications[ww]
                    #
                    for el in self.list_notifications:
                        if el[0] == ww:
                            self.list_notifications.remove(el)
                            break
                    try:
                        ww.destroy()
                    except:
                        pass
                    return
                #
                _value = None
                if _replaceid == 1:
                    _value = self._on_hints(_hints, "value")
                #
                if not _icon:
                    wicon = QPixmap("icons/audio-volume-default.png")
                else:
                    if QIcon.hasThemeIcon(_icon):
                        qicn = QIcon.fromTheme(_icon)
                        wicon = qicn.pixmap(label_icon.size())
                    elif QIcon.hasThemeIcon(_icon.strip("-symbolic")):
                        qicn = QIcon.fromTheme(_icon)
                        wicon = qicn.pixmap(label_icon.size())
                    else:
                        wicon = QPixmap(_icon)
                        if wicon.isNull():
                            wicon = QPixmap("icons/audio-volume-default.png")
                #
                label_icon.setPixmap(wicon.scaled(label_icon.size(),Qt.IgnoreAspectRatio))
                if SHOW_VALUE == 1:
                    if _body:
                        label_value.setText(str(_body))
                    else:
                        label_value.setText(str(_value))
                progress_bar.setValue(int(_value))
                if _timeout == -1:
                    _timeout = TIMEOUT
                if TIMEOUT_MAX:
                    if _timeout > TIMEOUT_MAX:
                        _timeout = TIMEOUT_MAX
                #
                timer = QTimer()
                timer.setSingleShot(True)
                timer.timeout.connect(lambda:self._timer(ww, _replaceid))
                ww.timer = None
                ww.timer = timer
                ww.timer.start(_timeout)
            except:
                return
        else:
            # to not overlay notifications
            old_wgeom = None
            if ww:
                old_wgeom = ww.geometry()
                if ww.timer:
                    ww.timer.stop()
                    if ww in self.win_notifications:
                        del self.win_notifications[ww]
                    #
                    for el in self.list_notifications:
                        if el[0] == ww:
                            self.list_notifications.remove(el)
                            break
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
            # wnotification.setWindowFlags(wnotification.windowFlags() | Qt.FramelessWindowHint)
            # wnotification.setWindowFlags(wnotification.windowFlags() | Qt.SplashScreen)
            wnotification.setWindowFlags(wnotification.windowFlags() | Qt.WindowDoesNotAcceptFocus | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
            #
            if old_wgeom:
                wnotification.setGeometry(old_wgeom)
            else:
                if self.y == 0 or self.list_notifications == []:
                    yy = YPAD
                else:
                    yy = self.y+4
                #
                wnotification.setGeometry(SCREEN_WIDTH-MIN_WIDTH-XPAD, yy, MIN_WIDTH, 10)
            #
            self.list_notifications.append([wnotification, _replaceid])
            #
            hbox1 = QHBoxLayout()
            hbox1.setContentsMargins(0,0,0,0)
            wnotification.setLayout(hbox1)
            #
            vbox = QVBoxLayout()
            vbox.setContentsMargins(0,0,0,0)
            #
            _desktop_entry = self._on_hints(_hints, "desktop-entry")
            ret_icon = None
            if _desktop_entry and USE_XDG:
                ret_icon = self._on_desktop_entry(os.path.basename(_desktop_entry))
            # 
            if VOLUME_STYLE:
                global USE_APP_NAME
                _OLD_APP_NAME = USE_APP_NAME
                _value = None
                if _replaceid == 1:
                    _value = self._on_hints(_hints, "value")
                    if _value and _value >= 0:
                        USE_APP_NAME = 2
            # not volume style
            if USE_APP_NAME != 2:
                # application name
                if USE_APP_NAME == 1:
                    appname_lbl = QLabel(_appname)
                    appname_lbl.setContentsMargins(0,0,0,0)
                    vbox.addWidget(appname_lbl, stretch=1, alignment=Qt.AlignCenter)
                #
                hbox2 = QHBoxLayout()
                hbox2.setContentsMargins(0,0,0,0)
                vbox.addLayout(hbox2)
                # icon label
                p_lbl = QLabel()
                p_lbl.setContentsMargins(0,0,0,0)
                #
                wicon = self._find_icon(ret_icon, _icon, _hints, QSize(ICON_SIZE, ICON_SIZE))
                #
                _i_size = wicon.size()
                _i_size_w, _i_size_h = _i_size.width(), _i_size.height()
                # width doesnt double height
                if (_i_size_w > _i_size_h and round(_i_size_w/_i_size_h,1) < 2):
                    _i_h = min(_i_size_h, ICON_SIZE)
                    p_lbl.setPixmap(wicon.scaledToHeight(_i_h))
                # # height doesnt double width
                else:
                    _i_w = min(_i_size_w, ICON_SIZE)
                    p_lbl.setPixmap(wicon.scaledToWidth(_i_w))
                #
                hbox1.addWidget(p_lbl)
                #
                hbox1.addLayout(vbox)
                # summary
                summary_lbl = QLabel(_summ)
                summary_lbl.setContentsMargins(0,0,0,0)
                if summary_lbl.size().width() > MAX_WIDTH:
                    summary_lbl.setWordWrap(True)
                    summary_lbl.resize(summary_lbl.sizeHint())
                    summary_lbl.update()
                #
                summary_lbl.setStyleSheet("font-weight: bold")
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
                if _not_name:
                    wnotification.notname = _not_name
            # volume style
            elif USE_APP_NAME == 2:
                hbox2 = QHBoxLayout()
                hbox2.setContentsMargins(10,0,10,0)
                # vbox.addLayout(hbox2)
                hbox1.addLayout(hbox2)
                #
                # icon label
                p_lbl = QLabel()
                p_lbl.setContentsMargins(0,0,0,0)
                p_lbl.resize(ICON_SIZE, ICON_SIZE)
                #
                if not _icon:
                    wicon = QPixmap("icons/audio-volume-default.png")
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
                            wicon = QPixmap("icons/audio-volume-default.png")
                #
                p_lbl.setPixmap(wicon.scaled(p_lbl.size(),Qt.IgnoreAspectRatio))
                hbox2.addWidget(p_lbl)
                # numeric value
                if SHOW_VALUE == 1:
                    if _body:
                        vlabel = QLabel(str(_body))
                    else:
                        vlabel = QLabel(str(_value))
                    hbox2.addWidget(vlabel)
                # progress bar
                pbar = QProgressBar()
                pbar.setContentsMargins(0,0,0,0)
                pbar.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Expanding)
                pbar.setOrientation(Qt.Horizontal) 
                pbar.setTextVisible(False)
                if PBAR_COLOR:
                    pbar.setStyleSheet("::chunk {0}background-color:{1}; {2}".format("{",PBAR_COLOR,"}"))
                pbar.setMaximumSize(16777215, PBAR_WIDTH)
                pbar.setRange(0, 100)
                hbox2.addWidget(pbar, stretch=1)
                #
                pbar.setValue(int(_value))
                #
                _body = ""
                _action = None
                USE_APP_NAME = _OLD_APP_NAME
            #
            ### body
            if _body:
                hbox3 = QHBoxLayout()
                hbox3.setContentsMargins(0,0,0,0)
                #
                vbox.addLayout(hbox3)
                body_lbl = QLabel(_body)
                body_lbl.setContentsMargins(0,0,0,0)
                #
                body_lbl.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Expanding)
                body_lbl.resize(body_lbl.sizeHint())
                body_lbl.update()
                if body_lbl.size().width() > MAX_WIDTH:
                    body_lbl.setWordWrap(True)
                    body_lbl.resize(body_lbl.sizeHint())
                    body_lbl.update()
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
            if 1:
                timer=QTimer()
                if _timeout == -1:
                    _timeout = TIMEOUT
                if TIMEOUT_MAX:
                    if _timeout > TIMEOUT_MAX:
                        _timeout = TIMEOUT_MAX
                timer.setSingleShot(True)
                timer.timeout.connect(lambda:self._timer(wnotification, _replaceid))
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
                        _MAX_WIDTH = max(MAX_WIDTH, body_lbl.size().width(), wnotification.sizeHint().width())
                        wnotification.resize(_MAX_WIDTH, wnotification.sizeHint().height())
                        wnotification.move(SCREEN_WIDTH-_MAX_WIDTH-XPAD,wnotification.geometry().y())
                    else:
                        _MIN_WIDTH = max(MIN_WIDTH, body_lbl.size().width(), wnotification.sizeHint().width())
                        wnotification.resize(_MIN_WIDTH, wnotification.sizeHint().height())
                        wnotification.move(SCREEN_WIDTH-_MIN_WIDTH-XPAD,wnotification.geometry().y())
                else:
                    wnotification.resize(max(wnotification.sizeHint().width(), MIN_WIDTH), wnotification.sizeHint().height())
                    wnotification.move(SCREEN_WIDTH-MIN_WIDTH-XPAD,wnotification.geometry().y())
                wnotification.update()
            # remove old window
            else:
                ww.hide()
                ww.destroy()
            #
            wgeom = wnotification.geometry()
            if not ww:
                self.y = (wgeom.y()+wgeom.height())
            if self.y > SCREEN_HEIGHT-ICON_SIZE*2:
                self.y = 0
            #
            if 1:
                timer.start(_timeout)
        #
        _no_sound = self._on_hints(_hints, "suppress-sound")
        _soundfile = self._on_hints(_hints, "sound-file")
        _urgency = self._on_hints(_hints, "urgency")
        #
        if not _soundfile:
            _soundfile = self._on_hints(_hints, "sound-name")
        if _no_sound and _soundfile:
            self._play_sound(_soundfile)
        else:
            if PLAY_STANDARD_SOUND:
                if _replaceid == 1:
                    if VOLUME_NO_AUDIO == 0:
                        self._play_sound("sounds/volume-sound.wav")
                elif _urgency == 1 or _urgency == None:
                    if PLAY_STANDARD_SOUND == 1:
                        self._play_sound("sounds/urgency-normal.wav")
                elif _urgency == 2:
                    if PLAY_STANDARD_SOUND in [1,2]:
                        self._play_sound("sounds/urgency-critical.wav")

    # sound event player
    def _play_sound(self, _sound):
        if SOUND_PLAYER == 1:
            QSound.play(_sound)
            return
        elif SOUND_PLAYER == 2:
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
