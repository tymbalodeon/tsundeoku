from datetime import datetime, time
from pathlib import Path
from shutil import which
from subprocess import run

from cyclopts import App
from rich import print
from xmltodict import parse
from yagmail import SMTP

from .config.config import APP_NAME, get_loaded_config
from .style import StyleLevel, print_with_theme, stylize

PLIST_LABEL = f"com.{APP_NAME}.import.plist"
LAUNCHCTL = "launchctl"

schedule = App(help="Schedule import command to run automatically.")


def get_format_reference_link() -> str:
    time_format_refence = (
        "https://docs.python.org/3/library/"
        "datetime.html#strftime-and-strptime-format-codes"
    )
    return f"link={time_format_refence}"


def get_schedule_help_message():
    format_reference_link = get_format_reference_link()
    here = stylize("here", styles=[format_reference_link, "underline"])
    return (
        "Schedule import to run at specified time, using the format %I:%M%p"
        f" for daily, **:%M for hourly. See {here} for more info."
    )


def get_tmp_path() -> Path:
    return Path("/tmp")


def get_log_path() -> Path:
    log_path = get_tmp_path() / f"{APP_NAME}.log"
    if not log_path.exists():
        log_path.touch()
    return log_path


def launchctl(command: str, path: Path | None = None) -> bytes:
    args: list[Path | str] = [LAUNCHCTL, command]
    if path:
        args.append(path)
    return run(args, capture_output=True).stdout


def load_rotate_logs_plist():
    rotate_logs_plist_label = f"com.{APP_NAME}.rotatelogs.plist"
    off(rotate_logs_plist_label)
    truncate_command = "truncate -s 0"
    log_path = get_log_path()
    plist = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"'
        ' "http://www.apple.com/DTDs/PropertyList-1.0.dtd">\n'
        '<plist version="1.0">\n'
        "\t<dict>\n"
        "\t\t<key>Label</key>\n"
        f"\t\t<string>{rotate_logs_plist_label}</string>\n"
        "\t\t<key>StartCalendarInterval</key>\n"
        "\t\t<dict>\n"
        "\t\t\t<key>Hour</key>\n"
        "\t\t\t<integer>0</integer>\n"
        "\t\t</dict>\n"
        "\t\t<key>ProgramArguments</key>\n"
        "\t\t<array>\n"
        f"\t\t<string>{truncate_command} {log_path}</string>\n"
        "\t\t</array>\n"
        "\t</dict>\n"
        "</plist>\n"
    )
    plist_path = get_plist_path(rotate_logs_plist_label)
    plist_path.write_text(plist)
    launchctl("load", plist_path)


def get_plist_path(label=PLIST_LABEL) -> Path:
    launch_agents = Path.home() / "library/LaunchAgents"
    return launch_agents / label


def get_calendar_interval(hour: int | None, minute: int | None) -> str:
    hour_key = minute_key = ""
    if hour is not None:
        hour_key = f"\t\t\t<key>Hour</key>\n\t\t\t<integer>{hour}</integer>\n"
    if minute is not None:
        minute_key = (
            f"\t\t\t<key>Minute</key>\n\t\t\t<integer>{minute}</integer>\n"
        )
    return (
        "\t\t<key>StartCalendarInterval</key>\n"
        f"\t\t<dict>\n{hour_key}{minute_key}\t\t</dict>\n"
    )


def get_command_args():
    command = which(APP_NAME)
    command_args = [
        "zsh",
        "-lc",
        f"{command} import --scheduled-run",
    ]
    strings = ""
    for arg in command_args:
        strings = f"{strings}\t\t\t<string>{arg}</string>\n"
    return strings


def get_plist_text(hour: int | None, minute: int | None) -> str:
    log_path = get_log_path()
    calendar_interval = get_calendar_interval(hour, minute)
    command_args = get_command_args()
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"'
        ' "http://www.apple.com/DTDs/PropertyList-1.0.dtd">\n'
        '<plist version="1.0">\n'
        "\t<dict>\n"
        "\t\t<key>Label</key>\n"
        f"\t\t<string>{PLIST_LABEL}</string>\n"
        "\t\t<key>StandardOutPath</key>\n"
        f"\t\t<string>{log_path}</string>\n"
        "\t\t<key>StandardErrorPath</key>\n"
        f"\t\t<string>{log_path}</string>\n"
        f"{calendar_interval}"
        "\t\t<key>ProgramArguments</key>\n"
        "\t\t<array>\n"
        f"{command_args}"
        "\t\t</array>\n"
        "\t</dict>\n"
        "</plist>\n"
    )


def load_plist(hour: int | None, minute: int | None):
    load_rotate_logs_plist()
    off()
    plist = get_plist_text(hour, minute)
    plist_path = get_plist_path()
    plist_path.write_text(plist)
    launchctl("load", plist_path)


def is_currently_scheduled() -> bool:
    loaded_plists = str(launchctl("list"))
    return PLIST_LABEL in loaded_plists


def print_show_schedule_error():
    print_with_theme(
        "Error retrieving schedule information.", StyleLevel.ERROR
    )


def stamp_logs() -> str:
    current_time = datetime.now().strftime("%Y-%m-%d %I:%M %p")
    log_path = get_log_path()
    with open(log_path, "a") as log:
        log.write(f"---- {current_time} ----\n")
    return current_time


def send_email(subject: str, contents: str):
    config = get_loaded_config()
    username = config.notifications.username
    password = config.notifications.password
    email = SMTP(username, password)
    subject = f"{APP_NAME}: {subject}"
    email.send(subject=subject, contents=contents)


def get_most_recent_log(text: str) -> list[str]:
    lines = text.splitlines()
    lines.reverse()
    for index, line in enumerate(lines):
        if line.startswith("---- "):
            index = index + 1
            lines = lines[:index]
    lines.reverse()
    return lines


def print_lines(lines: list[str]):
    for line in lines:
        print(line)


@schedule.command()
def logs(all=False):
    """Show import logs"""
    log_path = get_log_path()
    text = log_path.read_text()
    if all:
        lines = text.splitlines()
    else:
        lines = get_most_recent_log(text)
    print_lines(lines)


@schedule.command()
def off(label=PLIST_LABEL):
    """Turn off scheduling of import command"""
    plist_path = get_plist_path(label)
    launchctl("unload", plist_path)
    if plist_path.is_file():
        plist_path.unlink()
    print("Turned off scheduled import.")


@schedule.command()
def on(time: str) -> str:
    """Schedule import to run at specified time, using the format %I:%M%p for daily, \\*\\*:%M for hourly. See here for more info"""
    message = "Scheduled import for every"
    hour = None
    if "*" in time:
        schedule_type = "hour"
        time_format = "%M"
        scheduled_time = datetime.strptime(time, f"**:{time_format}")
        padded_minute = scheduled_time.strftime(time_format)
        display_time = f"**:{padded_minute} minutes"
    else:
        schedule_type = "day"
        time_format = "%I:%M%p"
        scheduled_time = datetime.strptime(time, time_format)
        hour = scheduled_time.hour
        display_time = scheduled_time.strftime(time_format)
    minute = scheduled_time.minute
    load_plist(hour=hour, minute=minute)
    return f"{message} {schedule_type} at {display_time}."


@schedule.command()
def show():
    """Show active schedule"""
    plist_path = get_plist_path()
    if not is_currently_scheduled():
        print("Import is not currently scheduled.")
        return
    if not plist_path.exists():
        print_show_schedule_error()
        return
    try:
        plist = parse(plist_path.read_bytes())
    except Exception:
        plist = None
    if not plist:
        print_show_schedule_error()
        return
    try:
        hour_and_minute = plist["plist"]["dict"]["dict"]["integer"]
    except Exception:
        print_show_schedule_error()
        return
    hour = "**"
    message = "Import is currently scheduled for every"
    if isinstance(hour_and_minute, list):
        hour, minute = (int(value) for value in hour_and_minute)
        scheduled_time = time(hour, minute).strftime("%I:%M%p")
        message = f"{message} day at {scheduled_time}."
    else:
        minute = int(hour_and_minute)
        minute = time(minute=minute).strftime("%M")
        scheduled_time = f"**:{minute}"
        message = f"{message} hour at {scheduled_time} minutes."
    print(message)
