use std::env::var;
use std::fs::{read_to_string, File};
use std::path::{absolute, Path, PathBuf};
use std::process::Command;
use std::str::FromStr;

use anyhow::{anyhow, Context, Result};
use bat::PrettyPrinter;
use clap::{Subcommand, ValueEnum};
use cron_descriptor::cronparser::cron_expression_descriptor::get_description_cron;
use english_to_cron::str_cron_syntax;
use serde::{Deserialize, Serialize};
use toml::{Table, Value};

use crate::{get_home_directory, log};
use crate::{warn_about_missing_shared_directories, LogLevel};

#[derive(Clone, Debug, ValueEnum)]
pub enum ConfigKey {
    SharedDirectories,
    IgnoredPaths,
    LocalDirectory,
    ScheduleInterval,
    ScheduleIntervalDescription,
}

#[derive(Subcommand, Debug)]
// #[command(arg_required_else_help = true)]
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
                .context(format!("failed to parse {key} values"))?
                .iter()
                .filter_map(|path| expand_path(path).ok())
                .collect::<Vec<PathBuf>>(),
        ))
    } else {
        Ok(None)
    }
}

fn get_cron_expression(description: &str) -> Result<String> {
    str_cron_syntax(description.to_string().as_str())
        .map_or_else(|_| Err(anyhow!("invalid cron description")), Ok)
}

fn get_cron_description(expression: &str) -> Result<String> {
    get_description_cron(expression)
        .map_or_else(|_| Err(anyhow!("invalid cron expression")), Ok)
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
            if let Ok(schedule_interval) = cron::Schedule::from_str(
                schedule_interval
                    .as_str()
                    .context("failed to get 'schedule_interval' value")?,
            ) {
                schedule_interval
            } else {
                cron::Schedule::from_str(&get_cron_expression(
                    &schedule_interval.to_string(),
                )?)?
            }
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

    fn to_toml(&self) -> Result<String> {
        Ok(toml::to_string(&self)?)
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
) -> Result<String> {
    Ok(match key {
        ConfigKey::SharedDirectories => {
            get_path_vector_display(&config.shared_directories)
        }

        ConfigKey::IgnoredPaths => {
            get_path_vector_display(&config.ignored_paths)
        }

        ConfigKey::LocalDirectory => {
            config.local_directory.display().to_string()
        }

        ConfigKey::ScheduleInterval => {
            config.schedule_interval.source().to_string()
        }

        ConfigKey::ScheduleIntervalDescription => {
            get_cron_description(config.schedule_interval.source())?
        }
    })
}

pub fn print_config(pretty_printer: &mut PrettyPrinter) -> Result<bool> {
    Ok(pretty_printer.theme("ansi").language("toml").print()?)
}

pub fn show(
    config_values: &ConfigFile,
    log_file: Option<&File>,
    key: Option<&ConfigKey>,
) -> Result<()> {
    if let Some(key) = key {
        let display = get_config_value_display(config_values, key)?;

        if !display.is_empty() {
            println!("{display}");
        };
    } else {
        let toml = config_values.to_toml()?.into_bytes();
        let mut pretty_printer = PrettyPrinter::new();

        pretty_printer.input_from_bytes(&toml);

        if let Err(error) = print_config(&mut pretty_printer) {
            log(&error.to_string(), &LogLevel::Warning, log_file, false);

            println!("{config_values:#?}");
        }
    }

    Ok(())
}

pub fn config(
    command: &Config,
    config_path: &Path,
    config_values: &ConfigFile,
    log_file: Option<&File>,
    is_scheduled: bool,
) -> Result<()> {
    warn_about_missing_shared_directories(config_values, is_scheduled);

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

        Config::Show { key } => show(config_values, log_file, key.as_ref())?,
    }

    Ok(())
}
