# qt5notification
A python desktop notification server.

This is a linux desktop notification server. It doesn't require installation, just execute it at login (as user). Do not use this program while another notification server is running/installed.

Requirements:
- python3
- pyqt5
- dbus
- xdg
- GSound (optional, but recommended for full sound support)
- freedesktop sounds (optional, but recommended for full sound support)


Features

- options in its config file
- sounds (throu GSound or a custom player)
- almost a complete support of freedesktop notification specs: actions, markup, hyperlink, etc.

Do not let any window manager to manage the notification position.

May have issues.
