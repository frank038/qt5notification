# qt5notification
A python desktop notification server.

This is a linux desktop notification server. It doesn't require installation, just execute it at login (as user). Do not use this program while another notification server is running/installed.

Requirements:
- python3
- pyqt5
- dbus
- DBusQtMainLoop
- xdg

Optional, for sounds:
- QtMultimedia (the default)
- GSound + freedesktop sounds (for full sound event support)
- an external audio player


Features

- options in its config file
- sounds: many options for enabling or disabling sounds for different kind of events
- almost a complete support of freedesktop notification specs: actions, markup, hyperlink, etc.
- volume style compatibility (see the config file for more)
- notifications will be saved, if properly configured

Do not let any window manager to manage the notification position.
