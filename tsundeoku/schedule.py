from datetime import datetime, time
from pathlib import Path
from subprocess import run

from rich.console import Console
from xmltodict import parse
from yagmail import SMTP

from .config.config import APP_NAME, get_loaded_config
from .style import StyleLevel, print_with_theme, stylize

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


def get_log_paths() -> tuple[Path, Path]:
    log_path = Path("/tmp/")
    stdout = log_path / f"{APP_NAME}.stdout"
    stderr = log_path / f"{APP_NAME}.stderr"
    for log_file in [stdout, stderr]:
        if not log_file.exists():
            log_file.touch()
    return stdout, stderr


def load_rotate_logs_plist():
    rotate_logs_plist_label = f"com.{APP_NAME}.rotatelogs.plist"
    remove_plist(rotate_logs_plist_label)
    truncate_command = "truncate -s 0"
    stdout, stderr = get_log_paths()
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
        "\t\t\t<key>Weekday</key>\n"
        "\t\t\t<integer>0</integer>\n"
        "\t\t</dict>\n"
        "\t\t<key>ProgramArguments</key>\n"
        "\t\t<array>\n"
        f"\t\t<string>{truncate_command} {stdout}</string>\n"
        f"\t\t<string>{truncate_command} {stderr}</string>\n"
        "\t\t</array>\n"
        "\t</dict>\n"
        "</plist>\n"
    )
    plist_path = get_plist_path(rotate_logs_plist_label)
    plist_path.write_text(plist)
    run([LAUNCHCTL, "load", plist_path])


def get_plist_path(label=PLIST_LABEL) -> Path:
    launch_agents = Path.home() / "library/LaunchAgents"
    return launch_agents / label


def remove_plist(label=PLIST_LABEL):
    plist_path = get_plist_path(label)
    run([LAUNCHCTL, "unload", plist_path], capture_output=True)
    if plist_path.is_file():
        plist_path.unlink()


def get_calendar_interval(hour: int | None, minute: int | None) -> str:
    hour_key = minute_key = ""
    if hour is not None:
        hour_key = f"\t\t\t<key>Hour</key>\n\t\t\t<integer>{hour}</integer>\n"
    if minute is not None:
        minute_key = f"\t\t\t<key>Minute</key>\n\t\t\t<integer>{minute}</integer>\n"
    return (
        "\t\t<key>StartCalendarInterval</key>\n"
        f"\t\t<dict>\n{hour_key}{minute_key}\t\t</dict>\n"
    )


def get_command_args():
    command_args = [
        "zsh",
        "-lc",
        f"{APP_NAME} import --disallow-prompt --scheduled-run",
    ]
    strings = ""
    for arg in command_args:
        strings = f"{strings}\t\t\t<string>{arg}</string>\n"
    return strings


def get_plist_text(hour: int | None, minute: int | None) -> str:
    stdout, stderr = get_log_paths()
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
        f"\t\t<string>{stdout}</string>\n"
        "\t\t<key>StandardErrorPath</key>\n"
        f"\t\t<string>{stderr}</string>\n"
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
    remove_plist()
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


def tail(text: str, number_of_lines=10):
    lines = text.splitlines()
    for line in lines[-number_of_lines:]:
        print(line)


def show_logs():
    stdout, stderr = get_log_paths()
    console = Console()
    console.rule("STDOUT")
    tail(stdout.read_text())
    console.rule("STDERR")
    tail(stderr.read_text())


def show_currently_scheduled():
    loaded_plists = str(run([LAUNCHCTL, "list"], capture_output=True).stdout)
    currently_scheduled = PLIST_LABEL in loaded_plists
    if not currently_scheduled:
        print("Import is not currently scheduled.")
        return
    plist_path = get_plist_path()
    plist = parse(plist_path.read_bytes())
    if plist:
        hour_and_minute = plist["plist"]["dict"]["dict"]["integer"]
    else:
        print_with_theme("Error retrieving schedule information.", StyleLevel.ERROR)
        return
    hour = "**"
    message = "Import is currently scheduled for every"
    if isinstance(hour_and_minute, list):
        hour, minute = (int(value) for value in hour_and_minute)
        scheduled_time = time(hour, minute).strftime("%I:%M%p")
        message = f"{message} day at {scheduled_time}."
    else:
        minute = time(int(hour_and_minute)).strftime("%M")
        scheduled_time = f"**:{minute}"
        message = f"{message} hour at {scheduled_time} minutes."
    print(message)


def stamp_logs():
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_paths = get_log_paths()
    for path in log_paths:
        with path.open("a") as log:
            log.write(f"---- {current_time} ----\n")


def send_email(contents: str):
    config = get_loaded_config()
    username = config.notifications.username
    password = config.notifications.password
    email = SMTP(username, password)
    subject = f"{APP_NAME}"
    email.send(subject=subject, contents=contents)
