from datetime import datetime, time
from pathlib import Path
from shutil import which
from subprocess import run

from rich.console import Console
from xmltodict import parse

from .config.config import APP_NAME

PLIST_LABEL = f"com.{APP_NAME}.import.plist"
LAUNCHCTL = "launchctl"


def get_plist_path() -> Path:
    launch_agents = Path.home() / "library/launchagents"
    return launch_agents / PLIST_LABEL


def remove_schedule():
    plist_path = get_plist_path()
    run([LAUNCHCTL, "unload", plist_path], capture_output=True)
    if plist_path.is_file():
        plist_path.unlink()
    print("Turned off scheduled import.")


def get_calendar_interval(**hour_and_minute: int) -> str:
    hour_key = minute_key = ""
    if "hour" in hour_and_minute:
        hour = hour_and_minute["hour"]
        hour_key = f"\t\t\t<key>Hour</key>\n\t\t\t<integer>{hour}</integer>\n"
    if "minute" in hour_and_minute:
        minute = hour_and_minute["minute"]
        minute_key = f"\t\t\t<key>Minute</key>\n\t\t\t<integer>{minute}</integer>\n"
    return (
        "\t\t<key>StartCalendarInterval</key>\n"
        f"\t\t<dict>\n{hour_key}{minute_key}\t\t</dict>\n"
    )


def get_plist_text(**hour_and_minute: int) -> str:
    local_bin = Path.home() / ".local/bin"
    tsundeoku_app = which(APP_NAME, path=local_bin)
    tsundeoku_command = "import"
    tsundeoku_option = "--disallow-prompt"
    calendar_interval = get_calendar_interval(**hour_and_minute)
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"'
        ' "http://www.apple.com/DTDs/PropertyList-1.0.dtd">\n'
        '<plist version="1.0">\n'
        "\t<dict>\n"
        "\t\t<key>Label</key>\n"
        f"\t\t<string>{PLIST_LABEL}</string>\n"
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


def load_plist(**hour_and_minute: int):
    remove_schedule()
    plist = get_plist_text(**hour_and_minute)
    plist_path = get_plist_path()
    plist_path.write_text(plist)
    run([LAUNCHCTL, "load", plist_path])


def schedule_import(schedule_time: str) -> str:
    if "*" in schedule_time:
        scheduled_time = datetime.strptime(schedule_time, "**:%M")
        minute = scheduled_time.minute
        load_plist(minute=minute)
        padded_minute = scheduled_time.strftime("%M")
        display_time = f"**:{padded_minute}"
        return f"Scheduled import for every hour at {display_time} minutes."
    else:
        scheduled_time = datetime.strptime(schedule_time, "%I:%M%p")
        hour = scheduled_time.hour
        minute = scheduled_time.minute
        load_plist(hour=hour, minute=minute)
        display_time = scheduled_time.time().strftime("%I:%M%p")
        return f"Scheduled import for every day at {display_time}."


def print_schedule_logs():
    log_path = Path("/tmp/")
    stdout = log_path / f"{APP_NAME}.stdout"
    stderr = log_path / f"{APP_NAME}.stderr"
    for log_file in [stdout, stderr]:
        if not log_file.exists():
            log_file.touch()
    console = Console()
    console.rule("STDOUT")
    print(stdout.read_text())
    console.rule("STDERR")
    print(stderr.read_text())


def show_currently_scheduled():
    loaded_plists = str(run([LAUNCHCTL, "list"], capture_output=True).stdout)
    currently_scheduled = PLIST_LABEL in loaded_plists
    if not currently_scheduled:
        print("Import is not currently scheduled.")
        return
    plist_path = get_plist_path()
    plist = parse(plist_path.read_bytes())
    hour_and_minute = plist["plist"]["dict"]["dict"]["integer"]
    hour = "**"
    message = "Import is currently scheduled for every"
    if isinstance(hour_and_minute, list):
        hour, minute = (int(value) for value in hour_and_minute)
        scheduled_time = time(hour, minute).strftime("%I:%M%p")
        message = f"{message} day at {scheduled_time}."
    else:
        minute = hour_and_minute
        scheduled_time = f"**:{minute}"
        message = f"{message} hour at {scheduled_time} minutes."
    print(message)
