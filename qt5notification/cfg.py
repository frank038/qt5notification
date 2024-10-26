########
# the notifications timeout (ms) - default value 3000
TIMEOUT=6000
# MAXIMUM_TIMEOUT: 0 to disable or number (ms)
TIMEOUT_MAX=20000
# application name in the notification
USE_APP_NAME=0
# minimal width of the notification
MIN_WIDTH=500
# maximum width of the notification: body text will be divided in lines
MAX_WIDTH=600
# icon size
ICON_SIZE=64
# notification colour: "" to disable - or e.g. "#000000" (black)
NOT_COLOR=""
# font colour: "" default colour - or e.g. "#ffffff" (white)
WIDGETS_FONT_COLOR=""
# play sound at any notification appearance: 1 yes - 0 no - 2 only urgent
PLAY_STANDARD_SOUND=1
# PLAYER: 1 use QtMultimedia - 2 use canberra (GSound) - "PROGRAM_NAME" use a custom command e.g. aplay (between quotes)
# use canberra (2) for a complete sound support
SOUND_PLAYER=1
# notification position indent from right and from top
XPAD=10
YPAD=10
# icon theme e.g. "Adwaita" or "" for using the default
ICON_THEME=""
# applications to skip - between quotes and comma separated
SKIP_APPS=[]
# border width and colour
BORDER_SIZE=2
BORDER_COLOR="#7F7F7F"
# action button border colour
BTN_BORDER_COLOR="#D4CACA"
# do not show: 0 do not use this - any value: 1 only urgency low - 2 only urgency normal and low - 3 always
# a file named notificationdonotuse_THE_VALUE_ABOVE should exist in this program directory
DO_NOT_SHOW=3
# volume style - use a progress bar instead of text: 1 yes - 0 no
# e.g.: notify-send some_not_used_summary NORMALIZED/NOT_NORMALIZED_VALUE -i AN_ICON --hint=string:x-canonical-private-synchronous:None --hint=int:value:NORMALIZED_VALUE
# NORMALIZED_VALUE: between 0 and 100, or 0 or 100
# not a standard method
VOLUME_STYLE=1
# the size of the progress bar
PBAR_WIDTH=12
# the colour of the progress bar: "" for using the default
PBAR_COLOR="#6A6A6A"
# show also the numeric value
SHOW_VALUE=0
# skip audio notification: 0 play sound - 1 do not play
VOLUME_NO_AUDIO=0
###
# save notifications: 0 no - 1 yes - 2 yes and only for known apps
SAVE_NOTIFICATION=1
# do not save if from these applications (application name)
SKIP_APPS2=["Applet NetworkManager"]
# save only from these applications
ONLY_APPS=[]
# do not save notifications closed by the user: 0 no - 1 yes
SKIP_CLOSED_BY_USER=0
# full path to store notifications (folder)
PATH_TO_STORE="/tmp/mynots"
########
