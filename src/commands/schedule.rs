use std::process::Command;
use std::str::{self};
use std::{fs::remove_file, path::PathBuf};

use anyhow::Result;
use chrono::{Local, Timelike};
use clap::Subcommand;
use serde::Deserialize;

use crate::commands::config::{get_config_value, ConfigFile};
use crate::{get_app_name, get_home_directory};

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

fn get_app_plist_file_name() -> String {
    format!("com.{}.import.plist", get_app_name())
}

// fn get_app_plist_file_name() -> String {
//     format!("com.{}.import.plist", get_app_name())
// }

fn is_scheduled(file_name: &str, plist_contents: &str) -> bool {
    plist_contents
        .lines()
        .filter(|line| line.contains(file_name))
        .filter_map(|line| line.split_whitespace().last())
        .count()
        == 1
}

// fn load_plist() {
//     Command::new("launchctl")
//         .arg("load")
//         .arg(&app_plist)
//         .status()?;
// }

fn on(config_values: &ConfigFile, interval: Option<&cron::Schedule>) {
    let interval =
        get_config_value(interval, &config_values.schedule_interval);

    println!("enabled scheduled imports for {interval:#?}.");
}

fn off() -> Result<()> {
    let app_plist = get_plist_path(&get_app_plist_file_name())?;

    Command::new("launchctl")
        .arg("unload")
        .arg(&app_plist)
        .status()?;

    remove_file(&app_plist)?;

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

fn next(config_values: &ConfigFile, interval: Option<&cron::Schedule>) {
    let interval =
        get_config_value(interval, &config_values.schedule_interval);

    if let Some(next) = interval.upcoming(Local::now().timezone()).next() {
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

    println!("[{}]", Local::now().format("%Y-%m-%d %H:%M:%S"));

    Ok(())
}

pub fn schedule(
    config_values: &ConfigFile,
    command: Option<&Schedule>,
) -> Result<()> {
    match command {
        Some(Schedule::On { interval }) => {
            on(config_values, interval.as_ref());
        }

        Some(Schedule::Off) => off()?,
        Some(Schedule::Status) | None => status()?,
        Some(Schedule::Next { interval }) => {
            next(config_values, interval.as_ref());
        }
    };

    Ok(())
}
