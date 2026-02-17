use std::env::var;
use std::fs::File;
use std::path::{absolute, PathBuf};
use std::process::Command;

use anyhow::{anyhow, Result};
use bat::PrettyPrinter;
use clap::{Subcommand, ValueEnum};
use cron_descriptor::cronparser::cron_expression_descriptor::get_description_cron;

use crate::config::{get_config, get_config_path, Config};
use crate::log;
use crate::LogLevel;

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
pub enum ConfigCommand {
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

fn get_cron_description(expression: &str) -> Result<String> {
    get_description_cron(expression)
        .map_or_else(|_| Err(anyhow!("invalid cron expression")), Ok)
}

pub fn get_config_value<'a, T>(
    override_value: Option<&'a T>,
    config_value: Option<&'a T>,
) -> Option<&'a T> {
    override_value.map_or_else(|| config_value, Some)
}

fn get_path_vector_display(vector: &[PathBuf]) -> String {
    vector
        .iter()
        .map(|path| path.display().to_string())
        .collect::<Vec<String>>()
        .join("\n")
}

pub fn get_config_value_display(
    config: &Config,
    key: &ConfigKey,
) -> Result<String> {
    Ok(match key {
        ConfigKey::SharedDirectories => {
            get_path_vector_display(&config.shared_directories)
        }

        ConfigKey::IgnoredPaths => {
            get_path_vector_display(&config.ignored_paths)
        }

        ConfigKey::LocalDirectory => config
            .local_directory
            .as_ref()
            .map_or_else(String::new, |local_directory| {
                local_directory.display().to_string()
            }),

        ConfigKey::ScheduleInterval => config
            .schedule_interval
            .as_ref()
            .map_or_else(String::new, |schedule_interval| {
                schedule_interval.source().to_string()
            }),

        ConfigKey::ScheduleIntervalDescription => get_cron_description(
            config.schedule_interval.as_ref().map_or_else(
                || "",
                |schedule_interval| schedule_interval.source(),
            ),
        )?,
    })
}

pub fn print_config(pretty_printer: &mut PrettyPrinter) -> Result<bool> {
    Ok(pretty_printer.theme("ansi").language("toml").print()?)
}

pub fn show(
    config_file: Option<&PathBuf>,
    log_file: Option<&File>,
    key: Option<&ConfigKey>,
) -> Result<()> {
    let config = get_config(config_file)?;

    if let Some(key) = key {
        let display = get_config_value_display(&config, key)?;

        if !display.is_empty() {
            println!("{display}");
        }
    } else {
        let toml = config.to_toml()?.into_bytes();
        let mut pretty_printer = PrettyPrinter::new();

        pretty_printer.input_from_bytes(&toml);

        if let Err(error) = print_config(&mut pretty_printer) {
            log(&error.to_string(), &LogLevel::Warning, log_file, false);

            println!("{config:#?}");
        }
    }

    Ok(())
}

pub fn config(
    config_file: Option<&PathBuf>,
    command: &ConfigCommand,
    log_file: Option<&File>,
) -> Result<()> {
    let config_path = get_config_path();

    match command {
        ConfigCommand::Edit => {
            if let Some(config_path) = config_path {
                Command::new(
                    var("EDITOR").unwrap_or_else(|_| "vim".to_string()),
                )
                .arg(config_path)
                .status()?;
            }
        }

        ConfigCommand::Path => {
            if let Some(config_path) = config_path {
                println!("{}", absolute(&config_path)?.display());
            }
        }

        ConfigCommand::Show { key } => {
            show(config_file, log_file, key.as_ref())?;
        }
    }

    Ok(())
}
