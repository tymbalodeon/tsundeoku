use std::fs::File;
use std::process::{Command, Stdio};
use std::{fs, str};
use std::{fs::remove_file, path::PathBuf};

use anyhow::{Context, Result};
use chrono::{Local, Timelike};
use clap::Subcommand;
use cron::TimeUnitSpec;
use cron_descriptor::cronparser::cron_expression_descriptor::get_description_cron;
use serde::Deserialize;

use crate::commands::config::{get_config_value, ConfigFile};
use crate::{
    get_app_name, get_binary_path, get_home_directory, get_log_path, log,
    warn_about_missing_shared_directories, LogLevel,
};

#[derive(Subcommand, Debug)]
#[command(arg_required_else_help = true)]
pub enum Schedule {
    /// Enable scheduled imports
    On {
        #[arg(long)]
        interval: Option<cron::Schedule>,
    },

    /// Disable scheduled imports
    Off,

    /// Show schedule status
    Status,

    /// Show next scheduled import
    Next {
        #[arg(long)]
        interval: Option<cron::Schedule>,
    },
}

fn get_plist_path(file_name: &str) -> Result<PathBuf> {
    Ok(get_home_directory()?
        .join("Library/LaunchAgents")
        .join(file_name))
}

fn get_plist_file_name(name: &str) -> String {
    format!("com.{}.{}.plist", get_app_name(), name)
}

fn get_app_plist_file_name() -> String {
    get_plist_file_name("import")
}

fn get_rotate_plist_file_name() -> String {
    get_plist_file_name("rotatelogs")
}

fn is_scheduled(file_name: &str, plist_contents: &str) -> bool {
    plist_contents
        .lines()
        .filter(|line| line.contains(file_name))
        .filter_map(|line| line.split_whitespace().last())
        .count()
        == 1
}

#[derive(Debug)]
enum CalendarInterval {
    Minute,
    Hour,
    Day,
    Weekday,
    Month,
}

fn get_time_unit_values(
    time_units: &impl TimeUnitSpec,
    name: &CalendarInterval,
) -> Option<String> {
    if time_units.is_all() {
        None
    } else {
        Some(format!(
            "<key>{:?}</key>
      <integer>{}</integer>",
            name,
            time_units
                .iter()
                .map(|unit| unit.to_string())
                .collect::<Vec<String>>()
                .join(",")
        ))
    }
}

fn get_plist(
    label: &str,
    calendar_interval: &str,
    program_arguments: &[&str],
) -> String {
    let program_arguments = program_arguments
        .iter()
        .map(|argument| format!("<string>{argument}</string>"))
        .collect::<Vec<String>>()
        .join("\n      ");

    format!("<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<!DOCTYPE plist PUBLIC \"-//Apple//DTD PLIST 1.0//EN\" \"http://www.apple.com/DTDs/PropertyList-1.0.dtd\">
<plist version=\"1.0\">
  <dict>
    <key>Label</key>
    <string>{label}</string>

    <key>StartCalendarInterval</key>
    <dict>
      {calendar_interval}
    </dict>

    <key>ProgramArguments</key>
    <array>
      {program_arguments}
    </array>
  </dict>
</plist>")
}

fn on(
    config_values: &ConfigFile,
    schedule_interval: Option<&cron::Schedule>,
    log_file: Option<&File>,
) -> Result<()> {
    let schedule =
        get_config_value(schedule_interval, &config_values.schedule_interval);

    let minutes =
        get_time_unit_values(schedule.minutes(), &CalendarInterval::Minute);

    let hours =
        get_time_unit_values(schedule.hours(), &CalendarInterval::Hour);

    let days_of_month =
        get_time_unit_values(schedule.days_of_month(), &CalendarInterval::Day);

    let days_of_week = get_time_unit_values(
        schedule.days_of_week(),
        &CalendarInterval::Weekday,
    );

    let months =
        get_time_unit_values(schedule.months(), &CalendarInterval::Month);

    let calendar_interval =
        [minutes, hours, days_of_month, days_of_week, months]
            .iter()
            .filter_map(|value| {
                value.as_ref().map(std::string::ToString::to_string)
            })
            .collect::<Vec<String>>()
            .join("\n\n      ");

    let app_plist_file_name = get_app_plist_file_name();
    let rotate_plist_file_name = get_rotate_plist_file_name();

    let app_plist = get_plist(
        &app_plist_file_name,
        &calendar_interval,
        &[
            &get_binary_path()?.display().to_string(),
            "import",
            "--is-scheduled",
        ],
    );

    let rotate_plist = get_plist(
        &rotate_plist_file_name,
        "<key>Day</key>
    <integer>1</integer>",
        &[
            "truncate",
            "-s",
            "0",
            get_log_path()?.to_str().context("failed to get log path")?,
        ],
    );

    let app_plist_file = &get_plist_path(&app_plist_file_name)?;
    let rotate_plist_file = &get_plist_path(&rotate_plist_file_name)?;

    off()?;

    for (file, contents) in [
        (app_plist_file, app_plist),
        (rotate_plist_file, rotate_plist),
    ] {
        fs::write(
            file.to_str().context("failed to get plist path")?,
            &contents,
        )?;

        Command::new("launchctl").arg("load").arg(file).status()?;
    }

    match get_description_cron(schedule.source()) {
        Ok(schedule_description) => println!(
            "import schedule for {}",
            schedule_description.to_lowercase()
        ),

        Err(error) => log(&error.s, &LogLevel::Error, log_file, false),
    }

    Ok(())
}

fn off() -> Result<()> {
    let app_plist_file_name = &get_app_plist_file_name();
    let app_plist_file = &get_plist_path(app_plist_file_name)?;
    let rotate_plist_file_name = &get_rotate_plist_file_name();
    let rotate_plist_file = &get_plist_path(rotate_plist_file_name)?;

    for (file_name, file) in [
        (app_plist_file_name, app_plist_file),
        (rotate_plist_file_name, rotate_plist_file),
    ] {
        if let Some(exit_code) = Command::new("launchctl")
            .arg("list")
            .arg(file_name)
            .stdout(Stdio::null())
            .stderr(Stdio::null())
            .status()?
            .code()
        {
            if exit_code == 0 {
                Command::new("launchctl").arg("unload").arg(file).status()?;
            }
        }

        if file.exists() {
            remove_file(file)?;
        }
    }

    Ok(())
}

#[derive(Deserialize)]
#[serde(rename_all = "PascalCase")]
struct StartCalendarInterval {
    minute: Option<u8>,
    hour: Option<u8>,
}

#[derive(Deserialize)]
#[serde(rename_all = "PascalCase")]
struct ScheduledImport {
    start_calendar_interval: StartCalendarInterval,
}

fn next(config_values: &ConfigFile, schedule: Option<&cron::Schedule>) {
    let schedule =
        get_config_value(schedule, &config_values.schedule_interval);

    if let Some(next) = schedule.upcoming(Local::now().timezone()).next() {
        let period = if next.hour12().0 { "pm" } else { "am" };

        println!("{:02}:{:02}{}", next.hour12().1, next.minute(), period);
    }
}

fn status() -> Result<()> {
    let launchctl_list =
        &Command::new("launchctl").arg("list").output()?.stdout;

    let plist_contents = str::from_utf8(launchctl_list)?;
    let app_plist_file_name = get_app_plist_file_name();
    let app_plist_file = get_plist_path(&app_plist_file_name)?;

    if !app_plist_file.exists()
        || !is_scheduled(&app_plist_file_name, plist_contents)
    {
        println!("not scheduled");
    } else {
        // TODO convert startcalendarinterval to cron
        let scheduled_import: ScheduledImport =
            plist::from_file(app_plist_file.display().to_string())?;

        if let Some(hour) = scheduled_import.start_calendar_interval.hour {
            let minute = scheduled_import
                .start_calendar_interval
                .minute
                .unwrap_or_default();

            println!("import is scheduled for {hour:02}:{minute:02}");
        } else if scheduled_import.start_calendar_interval.minute.is_some() {
            println!("import is scheduled for every hour");
        }
    }

    Ok(())
}

pub fn schedule(
    config_values: &ConfigFile,
    command: Option<&Schedule>,
    log_file: Option<&File>,
    is_scheduled: bool,
) -> Result<()> {
    warn_about_missing_shared_directories(config_values, is_scheduled);

    match command {
        Some(Schedule::On { interval }) => {
            on(config_values, interval.as_ref(), log_file)?;
        }

        Some(Schedule::Off) => off()?,
        Some(Schedule::Status) | None => status()?,

        Some(Schedule::Next { interval }) => {
            next(config_values, interval.as_ref());
        }
    };

    Ok(())
}
