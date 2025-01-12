use std::env::var;
use std::fs::{read_to_string, OpenOptions};
use std::path::{absolute, Path, PathBuf};
use std::process::Command;
use std::str::FromStr;

use anyhow::Result;
use bat::PrettyPrinter;
use clap::{Subcommand, ValueEnum};
use serde::{Deserialize, Serialize};

use crate::commands::import::get_log_path;
use crate::log;
use crate::LogLevel;

#[derive(Debug, Deserialize, Serialize)]
pub struct ConfigFile {
    pub shared_directories: Vec<PathBuf>,
    pub ignored_paths: Vec<PathBuf>,
    pub local_directory: PathBuf,
    pub schedule_interval: Option<cron::Schedule>,
}

fn expand_str_to_path(path: &str) -> PathBuf {
    PathBuf::from(shellexpand::tilde(path).into_owned())
}

impl Default for ConfigFile {
    fn default() -> Self {
        Self {
            // TODO don't use a default shared in case it contains tons of files that shouldn't be imported
            shared_directories: vec![expand_str_to_path("~/Dropbox")],
            ignored_paths: vec![],
            local_directory: expand_str_to_path("~/Music"),
            schedule_interval: cron::Schedule::from_str("0 0 * * * *")
                .ok()
                .or(None),
        }
    }
}

fn expand_path(path: &Path) -> PathBuf {
    shellexpand::tilde(&path.display().to_string())
        .to_string()
        .into()
}

fn expand_paths(paths: &[PathBuf]) -> Vec<PathBuf> {
    paths
        .iter()
        .map(|path| expand_path(path.as_path()))
        .collect::<Vec<PathBuf>>()
}

impl ConfigFile {
    pub fn from_file(config_path: &Path) -> Result<Self> {
        let file = read_to_string(config_path)?;

        let mut config_items =
            toml::from_str::<Self>(&file).unwrap_or_default();

        config_items.shared_directories =
            expand_paths(&config_items.shared_directories);

        config_items.ignored_paths = expand_paths(&config_items.ignored_paths);

        config_items.local_directory =
            expand_path(&config_items.local_directory);

        Ok(config_items)
    }
}

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

        ConfigKey::ScheduleInterval => config
            .schedule_interval.clone()
            .map_or(String::new(), |interval| interval.to_string()),
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
