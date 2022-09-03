from pathlib import Path
from shutil import which

from tsundeoku.config.config import APP_NAME

HOME = Path.home()
LOCAL_BIN = HOME / ".local/bin"
LAUNCH_AGENTS = HOME / "Library/LaunchAgents"
TSUNDEOKU_APP = which(APP_NAME, path=LOCAL_BIN)
TSUNDEOKU_COMMAND = "import"
TSUNDEOKU_OPTION = "--disallow-prompt"
HOUR = 17
LABEL = f"com.{APP_NAME}.import.plist"
PLIST = (
    '<?xml version="1.0" encoding="UTF-8"?>\n'
    '<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">\n'
    '<plist version="1.0">\n'
    "\t<dict>\n"
    "\t\t<key>Label</key>\n"
    f"\t\t<string>{LABEL}</string>\n"
    "\t\t<key>StartCalendarInterval</key>\n"
    "\t\t<dict>\n"
    "\t\t\t<key>Hour</key>\n"
    f"\t\t\t<integer>{HOUR}</integer>\n"
    "\t\t\t<key>Minute</key>\n"
    f"\t\t\t<integer>13</integer>\n"
    "\t\t</dict>\n"
    "\t\t<key>StandardErrorPath</key>\n"
    f"\t\t<string>/tmp/{APP_NAME}.stderr</string>\n"
    "\t\t<key>StandardOutPath</key>\n"
    f"\t\t<string>/tmp/{APP_NAME}.stdout</string>\n"
    # "\t\t<key>EnvironmentVariables</key>\n"
    # "\t\t<dict>\n"
    # "\t\t\t<key>PATH</key>\n"
    # "\t\t\t<string>/.local/bin</string>\n"
    # "\t\t</dict>\n"
    "\t\t<key>ProgramArguments</key>\n"
    "\t\t<array>\n"
    f"\t\t\t<string>{TSUNDEOKU_APP}</string>\n"
    f"\t\t\t<string>{TSUNDEOKU_COMMAND}</string>\n"
    f"\t\t\t<string>{TSUNDEOKU_OPTION}</string>\n"
    "\t\t</array>\n"
    "\t\t</dict>\n"
    "</plist>\n"
)

PLIST_FILE = LAUNCH_AGENTS / LABEL
PLIST_FILE.touch()
PLIST_FILE.write_text(PLIST)
