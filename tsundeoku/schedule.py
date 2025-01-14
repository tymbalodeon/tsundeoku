from datetime import datetime, time
from pathlib import Path
from shutil import which
from subprocess import run
from typing import Annotated

import xmltodict
from cyclopts import App, Parameter
from rich import print
from yagmail import SMTP

from tsundeoku.config import Config, get_app_name

from .style import stylize


def get_format_reference_link() -> str:
    return (
        "link="
        "https://docs.python.org/3/library/"
        "datetime.html#strftime-and-strptime-format-codes"
    )


def get_schedule_help_message():
    here = stylize("here", styles=[get_format_reference_link(), "underline"])
    return (
        "Schedule import to run at specified time, using the format %I:%M%p"
        f" for daily, **:%M for hourly. See {here} for more info."
    )


schedule_app = App(name="schedule", help=get_schedule_help_message())


def launchctl(command: str, path: Path | None = None) -> bytes:
    args: list[Path | str] = ["launchctl", command]
    if path:
        args.append(path)
    return run(args, capture_output=True).stdout


def load_rotate_logs_plist():
    rotate_logs_plist_label = f"com.{get_app_name()}.rotatelogs.plist"
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


def get_plist_path(label: str) -> Path:
    return Path.home() / "library/LaunchAgents" / label


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
    command = which(get_app_name())
    command_args = [
        "zsh",
        "-lc",
        f"{command} import --disallow-prompt",
    ]
    strings = ""
    for arg in command_args:
        strings = f"{strings}\t\t\t<string>{arg}</string>\n"
    return strings


def get_app_plist_label() -> str:
    return f"com.{get_app_name()}.import.plist"


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
        f"\t\t<string>{get_app_plist_label()}</string>\n"
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
    off(get_app_plist_label())
    plist = get_plist_text(hour, minute)
    plist_path = get_plist_path(get_app_plist_label())
    plist_path.write_text(plist)
    launchctl("load", plist_path)


def stamp_logs() -> None:
    with open(get_log_path(), "a") as log:
        log.write(
            f"---- {datetime.now().strftime('%Y-%m-%d %I:%M %p')} ----\n"
        )


def send_email(subject: str, contents: str):
    config = Config.from_toml()
    email = SMTP(
        config.items.schedule.username, config.items.schedule.password
    )
    subject = f"{get_app_name()}: {subject}"
    email.send(subject=subject, contents=contents)


def get_log_path() -> Path:
    return Path("/tmp") / f"{get_app_name()}.log"


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


@schedule_app.command()
def logs():
    """Show import logs."""
    with open(get_log_path()) as log_file:
        print("".join(log_file.readlines()[-30:]))


@schedule_app.command()
def off(label: Annotated[str | None, Parameter(show=False)] = None):
    """Disable scheduled imports."""
    if label is None:
        label = get_app_plist_label()
    plist_path = get_plist_path(label)
    launchctl("unload", plist_path)
    if plist_path.is_file():
        plist_path.unlink()


@schedule_app.command()
def on(time: str = "**:00", /) -> str:
    """Enable scheduled imports

    Parameters
    ----------
    time
        [cyan]%I:%M%p[/] for daily, [cyan]**:%M[/] for hourly.
    """
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


def is_currently_scheduled() -> bool:
    return get_app_plist_label() in str(launchctl("list"))


@schedule_app.command()
def show():
    """Show active schedule."""
    plist_path = get_plist_path(get_app_plist_label())
    if not is_currently_scheduled() or not plist_path.exists():
        print("[yellow]Import is not currently scheduled.[/]")
        return
    plist = xmltodict.parse(plist_path.read_bytes())
    hour_and_minute = plist["plist"]["dict"]["dict"]["integer"]
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
        message = f"{message} hour at [cyan]{scheduled_time}[/] minutes."
    print(message)
