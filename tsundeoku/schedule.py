from pathlib import Path
from shutil import which
from subprocess import run

from .config.config import APP_NAME

LABEL = f"com.{APP_NAME}.import.plist"
LAUNCHCTL = "launchctl"


def get_plist_path() -> Path:
    launch_agents = Path.home() / "library/launchagents"
    return launch_agents / LABEL


def unload_plist():
    plist_path = get_plist_path()
    run([LAUNCHCTL, "unload", plist_path], capture_output=True)
    if plist_path.is_file():
        plist_path.unlink()


def get_calendar_interval(**kwargs: int) -> str:
    hour_key = minute_key = ""
    if "hour" in kwargs:
        hour = kwargs["hour"]
        hour_key = f"\t\t\t<key>Hour</key>\n\t\t\t<integer>{hour}</integer>\n"
    if "minute" in kwargs:
        minute = kwargs["minute"]
        minute_key = f"\t\t\t<key>Minute</key>\n\t\t\t<integer>{minute}</integer>\n"
    return (
        "\t\t<key>StartCalendarInterval</key>\n"
        f"\t\t<dict>\n{hour_key}{minute_key}\t\t</dict>\n"
    )


def load_plist(**kwargs: int):
    unload_plist()
    local_bin = Path.home() / ".local/bin"
    tsundeoku_app = which(APP_NAME, path=local_bin)
    tsundeoku_command = "import"
    tsundeoku_option = "--disallow-prompt"
    calendar_interval = get_calendar_interval(**kwargs)
    plist = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"'
        ' "http://www.apple.com/DTDs/PropertyList-1.0.dtd">\n'
        '<plist version="1.0">\n'
        "\t<dict>\n"
        "\t\t<key>Label</key>\n"
        f"\t\t<string>{LABEL}</string>\n"
        f"{calendar_interval}"
        "\t\t<key>StandardErrorPath</key>\n"
        f"\t\t<string>/tmp/{APP_NAME}.stderr</string>\n"
        "\t\t<key>StandardOutPath</key>\n"
        f"\t\t<string>/tmp/{APP_NAME}.stdout</string>\n"
        "\t\t<key>ProgramArguments</key>\n"
        "\t\t<array>\n"
        f"\t\t\t<string>{tsundeoku_app}</string>\n"
        f"\t\t\t<string>{tsundeoku_command}</string>\n"
        f"\t\t\t<string>{tsundeoku_option}</string>\n"
        "\t\t</array>\n"
        "\t\t</dict>\n"
        "</plist>\n"
    )
    plist_path = get_plist_path()
    plist_path.write_text(plist)
    run([LAUNCHCTL, "load", plist_path])
