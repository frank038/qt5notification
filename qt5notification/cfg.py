########
# the notifications timeout (ms) - default value 3000
TIMEOUT=3000
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
# play sound at any notification appearance: 1 yes - 0 no
PLAY_STANDARD_SOUND=1
# PLAYER: 2 use canberra (GSound) - "PROGRAM_NAME" use a custom command e.g. aplay (between quotes)
# use canberra (2) for a complete sound support
SOUND_PLAYER=2
# notification position indent from right and from top
XPAD=10
YPAD=10
# icon theme e.g. "Adwaita" or "" for using the default
ICON_THEME="Adwaita"
# applications to skip - between quotes and comma separated
SKIP_APPS=[]
# border width and colour
BORDER_SIZE=2
BORDER_COLOR="#7F7F7F"
# action button border colour
BTN_BORDER_COLOR="#D4CACA"
# do not show: 0 do not use this - 1 only urgency low - 2 only urgency normal and low - 3 none
# a file named notificationdonotuse_THE_VALUE_ABOVE should exist in this program directory
DO_NOT_SHOW=0
# volume style - use a progress bar instead of text: 1 yes - 0 no
# e.g.: notify-send some_not_used_summary NORMALIZED/NOT_NORMALIZED_VALUE --hint=string:x-canonical-private-synchronous:None --hint=int:value:NORMALIZED_VALUE
# NORMALIZED_VALUE: between 0 and 100, or 0 or 100
# not a standard method
VOLUME_STYLE=1
# the size of the progress bar
PBAR_WIDTH=12
# the colour of the progress bar: "" for using the default
PBAR_COLOR="#6A6A6A"
# show also the numeric value
SHOW_VALUE=0
########
