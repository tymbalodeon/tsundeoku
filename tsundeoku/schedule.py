from datetime import datetime, time
from pathlib import Path
from shutil import which
from subprocess import run

from rich.console import Console
from xmltodict import parse

from tsundeoku.style import stylize

from .config.config import APP_NAME

PLIST_LABEL = f"com.{APP_NAME}.import.plist"
LAUNCHCTL = "launchctl"


def get_format_reference_link() -> str:
    time_format_refence = (
        "https://docs.python.org/3/library/"
        "datetime.html#strftime-and-strptime-format-codes"
    )
    return f"link={time_format_refence}"


def get_schedule_help_message():
    format_reference_link = get_format_reference_link()
    return (
        "Schedule import to run at specified time, using the format %I:%M%p for daily,"
        " **:%M"
        " for hourly. See"
        f" {stylize('here', [format_reference_link, 'underline'])} for more info."
    )


def get_plist_path() -> Path:
    launch_agents = Path.home() / "library/launchagents"
    return launch_agents / PLIST_LABEL


def remove_schedule():
    plist_path = get_plist_path()
    run([LAUNCHCTL, "unload", plist_path], capture_output=True)
    if plist_path.is_file():
        plist_path.unlink()
    print("Turned off scheduled import.")


def get_calendar_interval(hour: int | None, minute: int | None) -> str:
    hour_key = minute_key = ""
    if hour:
        hour_key = f"\t\t\t<key>Hour</key>\n\t\t\t<integer>{hour}</integer>\n"
    if minute:
        minute_key = f"\t\t\t<key>Minute</key>\n\t\t\t<integer>{minute}</integer>\n"
    return (
        "\t\t<key>StartCalendarInterval</key>\n"
        f"\t\t<dict>\n{hour_key}{minute_key}\t\t</dict>\n"
    )


def get_command_args():
    local_bin = Path.home() / ".local/bin"
    tsundeoku_app = which(APP_NAME, path=local_bin)
    command_args = [tsundeoku_app, "import", "--disallow-prompt", "--scheduled-run"]
    strings = ""
    for arg in command_args:
        strings = f"{strings}\t\t\t<string>{arg}</string>\n"
    return strings


def get_plist_text(hour: int | None, minute: int | None) -> str:
    calendar_interval = get_calendar_interval(hour, minute)
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"'
        ' "http://www.apple.com/DTDs/PropertyList-1.0.dtd">\n'
        '<plist version="1.0">\n'
        "\t<dict>\n"
        "\t\t<key>Label</key>\n"
        f"\t\t<string>{PLIST_LABEL}</string>\n"
        f"{calendar_interval}"
        "\t\t<array>\n"
        f"{get_command_args}"
        "\t\t</array>\n"
        "\t\t</dict>\n"
        "</plist>\n"
    )


def load_plist(hour: int | None, minute: int | None):
    remove_schedule()
    plist = get_plist_text(hour, minute)
    plist_path = get_plist_path()
    plist_path.write_text(plist)
    run([LAUNCHCTL, "load", plist_path])


def schedule_import(schedule_time: str) -> str:
    message = "Schedule import for every"
    hour = None
    if "*" in schedule_time:
        schedule_type = "hour"
        time_format = "%M"
        scheduled_time = datetime.strptime(schedule_time, f"**:{time_format}")
        padded_minute = scheduled_time.strftime(time_format)
        display_time = f"**:{padded_minute} minutes"
    else:
        schedule_type = "day"
        time_format = "%I:%M%p"
        scheduled_time = datetime.strptime(schedule_time, time_format)
        hour = scheduled_time.hour
        display_time = scheduled_time.strftime(time_format)
    minute = scheduled_time.minute
    load_plist(hour=hour, minute=minute)
    return f"{message} {schedule_type} at {display_time}."


def get_log_paths() -> tuple[Path, Path]:
    log_path = Path("/tmp/")
    stdout = log_path / f"{APP_NAME}.stdout"
    stderr = log_path / f"{APP_NAME}.stderr"
    for log_file in [stdout, stderr]:
        if not log_file.exists():
            log_file.touch()
    return stdout, stderr


def rotate_logs():
    current_day_of_week = datetime.today().weekday()
    print(current_day_of_week)
    if current_day_of_week == 0:
        log_paths = get_log_paths()
        for path in log_paths:
            path.write_text("")


def stamp_logs():
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_paths = get_log_paths()
    for path in log_paths:
        with path.open("a") as log:
            log.write(f"---- {current_time} ----")


def show_logs():
    stdout, stderr = get_log_paths()
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
