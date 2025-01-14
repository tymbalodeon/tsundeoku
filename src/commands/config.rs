use std::env::var;
use std::fs::{read_to_string, OpenOptions};
use std::path::{absolute, Path, PathBuf};
use std::process::Command;
use std::str::FromStr;

use anyhow::{Context, Result};
use bat::PrettyPrinter;
use clap::{Subcommand, ValueEnum};
use serde::{Deserialize, Serialize};
use toml::{Table, Value};

use crate::{get_home_directory, log};
use crate::{get_log_path, LogLevel};

#[derive(Clone, Debug, ValueEnum)]
pub enum ConfigKey {
    SharedDirectories,
    IgnoredPaths,
    LocalDirectory,
    ScheduleInterval,
}

#[derive(Subcommand, Debug)]
#[command(arg_required_else_help = true)]
pub enum Config {
    /// Open config file in $EDITOR
    Edit,

    /// Show config file path
    Path,

    /// Show config values
    Show {
        // Show the value for a particular key
        key: Option<ConfigKey>,
    },
}

#[derive(Debug, Deserialize, Serialize)]
pub struct ConfigFile {
    pub shared_directories: Vec<PathBuf>,
    pub ignored_paths: Vec<PathBuf>,
    pub local_directory: PathBuf,
    pub schedule_interval: cron::Schedule,
}

fn expand_path(path: &Value) -> Result<PathBuf> {
    Ok(PathBuf::from_str(&shellexpand::tilde(
        path.as_str()
            .context(format!("failed to parse path {path}"))?,
    ))?)
}

fn get_paths(config_items: &Table, key: &str) -> Result<Option<Vec<PathBuf>>> {
    if let Some(paths) = config_items.get(key) {
        Ok(Some(
            paths
                .as_array()
                .context("YO")?
                .iter()
                .filter_map(|path| expand_path(path).ok())
                .collect::<Vec<PathBuf>>(),
        ))
    } else {
        Ok(None)
    }
}

impl ConfigFile {
    pub fn from_file(config_path: &Path) -> Result<Self> {
        let file = read_to_string(config_path)?;
        let config_items: Table = toml::from_str(&file)?;

        let shared_directories =
            (get_paths(&config_items, "shared_directories")?)
                .unwrap_or_default();

        let ignored_paths =
            (get_paths(&config_items, "ignored_paths")?).unwrap_or_default();

        let local_directory = if let Some(local_directory) =
            config_items.get("local_directory")
        {
            PathBuf::from(
                local_directory
                    .as_str()
                    .context("failed to get 'local_directory' value")?,
            )
        } else {
            get_home_directory()?.join("Music")
        };

        let schedule_interval = if let Some(schedule_interval) =
            config_items.get("schedule_interval")
        {
            cron::Schedule::from_str(
                schedule_interval
                    .as_str()
                    .context("failed to get 'schedule_interval' value")?,
            )?
        } else {
            cron::Schedule::from_str("0 0 * * * *")?
        };

        Ok(Self {
            shared_directories,
            ignored_paths,
            local_directory,
            schedule_interval,
        })
    }
}

pub fn get_config_value<'a, T>(
    override_value: Option<&'a T>,
    config_value: &'a T,
) -> &'a T {
    override_value.map_or(config_value, |value| value)
}

fn get_path_vector_display(vector: &[PathBuf]) -> String {
    vector
        .iter()
        .map(|path| path.display().to_string())
        .collect::<Vec<String>>()
        .join("\n")
}

pub fn get_config_value_display(
    config: &ConfigFile,
    key: &ConfigKey,
) -> String {
    match key {
        ConfigKey::SharedDirectories => {
            get_path_vector_display(&config.shared_directories)
        }

        ConfigKey::IgnoredPaths => {
            get_path_vector_display(&config.ignored_paths)
        }

        ConfigKey::LocalDirectory => {
            config.local_directory.display().to_string()
        }

        ConfigKey::ScheduleInterval => config.schedule_interval.to_string(),
    }
}

pub fn print_config(pretty_printer: &mut PrettyPrinter) -> Result<bool> {
    Ok(pretty_printer.theme("ansi").language("toml").print()?)
}

pub fn config(
    command: &Config,
    config_path: &Path,
    config_values: &ConfigFile,
) -> Result<()> {
    match command {
        Config::Edit => {
            Command::new(
                var("EDITOR").map_or("vim".to_string(), |editor| editor),
            )
            .arg(config_path)
            .status()?;
        }

        Config::Path => {
            println!("{}", absolute(config_path)?.display());
        }

        Config::Show { key } => {
            if let Some(key) = key {
                println!("{}", get_config_value_display(config_values, key));
            } else if let Err(error) =
                print_config(PrettyPrinter::new().input_file(config_path))
            {
                let mut log_file = OpenOptions::new()
                    .create(true)
                    .append(true)
                    .open(get_log_path()?)?;

                log(error.to_string(), &LogLevel::Warning, &mut log_file)?;
                println!("{config_values:#?}");
            }
        }
    }

    Ok(())
}
