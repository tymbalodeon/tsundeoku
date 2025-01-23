mod commands;

use std::fs::{create_dir_all, File, OpenOptions};
use std::io::Write;
use std::path::{Path, PathBuf};
use std::str::FromStr;
use std::string::ToString;
use std::vec::Vec;

use anyhow::{Context, Error, Result};
use chrono::Local;
use clap::{Parser, Subcommand};
use colored::Colorize;
use home::home_dir;
use path_dedot::ParseDot;

use crate::commands::config::config;
use crate::commands::config::Config;
use crate::commands::config::ConfigFile;
use crate::commands::import::import;
use crate::commands::imported::imported;
use crate::commands::logs::logs;
use crate::commands::schedule::{schedule, Schedule};

#[derive(Subcommand)]
enum Commands {
    /// Show config values
    Config {
        #[command(subcommand)]
        command: Option<Config>,
    },

    /// Import newly added audio files from shared folders to a local folder
    Import {
        #[arg(long)]
        #[arg(num_args(0..))]
        #[arg(value_name = "DIR")]
        shared_directories: Option<Vec<PathBuf>>,

        // TODO allow wildcards
        #[arg(long)]
        #[arg(num_args(0..))]
        #[arg(value_name = "PATH")]
        ignored_paths: Option<Vec<PathBuf>>,

        #[arg(long)]
        #[arg(value_name = "DIR")]
        local_directory: Option<PathBuf>,

        #[arg(long)]
        dry_run: bool,

        #[arg(long)]
        no_reformat: bool,

        #[arg(long)]
        #[arg(short)]
        force: bool,
    },

    /// Show shared directory files that have been imported
    Imported,

    /// Show import logs
    Logs,

    /// Enable and disable scheduled imports
    Schedule {
        #[command(subcommand)]
        command: Option<Schedule>,
    },
}

/// Import audio files from a shared folder to a local folder
#[derive(Parser)]
#[command(arg_required_else_help = true)]
#[command(before_help = "積んでおく (tsundeoku) –– \"to pile up for later\"")]
#[command(version)]
struct Cli {
    #[command(subcommand)]
    command: Option<Commands>,

    #[arg(global = true)]
    #[arg(long)]
    #[arg(value_name = "FILE")]
    config_file: Option<String>,
}

fn get_home_directory() -> Result<PathBuf> {
    home_dir().context("failed to get $HOME directory")
}

const fn get_app_name() -> &'static str {
    "tsundeoku"
}

fn get_binary_path() -> Result<PathBuf> {
    Ok(get_home_directory()?.join(".cargo").join("bin").join("tsu"))
}

#[derive(Debug)]
pub enum LogLevel {
    Info,
    Warning,
    Error,
}

fn print_error(message: &str) {
    eprintln!("{} {message}", format!("{}:", "error".red()).bold());
}

pub fn log(
    message: &str,
    level: &LogLevel,
    log_file: Option<&File>,
    write: bool,
) {
    let message = match level {
        LogLevel::Info => None,
        LogLevel::Warning => Some("warning.yellow()".to_string()),
        LogLevel::Error => Some("error".red().to_string()),
    }
    .map_or(message.to_string(), |level_label| {
        format!("{level_label}: {message}")
    });

    if matches!(level, LogLevel::Info) {
        println!("{message}");
    } else {
        eprintln!("{message}");
    }

    if write {
        if let Some(mut log_file) = log_file {
            if let Err(error) = log_file.write_all(
                format!(
                    "[{}] {:>7} {}\n",
                    Local::now().format("%Y-%m-%d %H:%M:%S"),
                    format!("{level:?}").to_uppercase().bold(),
                    message.trim()
                )
                .as_bytes(),
            ) {
                print_error(&error.to_string());
            }
        } else {
            print_error("failed to write to log file");
        }
    }
}

fn get_config_file(config_file: Option<&String>) -> Result<PathBuf> {
    config_file.map_or_else(
        || {
            Ok::<PathBuf, Error>(
                get_home_directory()?
                    .join(".config")
                    .join(get_app_name())
                    .join(format!("{}.toml", get_app_name())),
            )
        },
        |config_path| {
            Ok(PathBuf::from_str(
                Path::new(config_path)
                    .parse_dot()
                    .context("failed to parse config path")?
                    .to_str()
                    .context("failed to get config path")?,
            )?)
        },
    )
}

fn get_state_directory() -> Result<PathBuf> {
    let state_directory = get_home_directory()?
        .join(".local/state")
        .join(get_app_name());

    create_dir_all(&state_directory)?;

    Ok(state_directory)
}

fn get_imported_files_path() -> Result<PathBuf> {
    Ok(get_state_directory()?
        .join(format!("{}-imported-files.log", get_app_name())))
}

fn get_log_path() -> Result<PathBuf> {
    Ok(get_state_directory()?.join(format!("{}.log", get_app_name())))
}

pub fn warn_about_missing_shared_directories(config_values: &ConfigFile) {
    if config_values.shared_directories.is_empty() {
        log(
            "shared-directories is not set",
            &LogLevel::Warning,
            None,
            false,
        );
    }
}

fn main() {
    colored::control::set_override(true);

    let cli = Cli::parse();

    let log_file = get_log_path().map_or_else(
        |_| None,
        |log_path| {
            OpenOptions::new()
                .create(true)
                .append(true)
                .open(log_path)
                .ok()
        },
    );

    if let Ok(config_path) = get_config_file(cli.config_file.as_ref()) {
        let config_path = Path::new(&config_path);

        let Ok(config_values) = ConfigFile::from_file(config_path) else {
            log(
                "failed to read config file",
                &LogLevel::Error,
                log_file.as_ref(),
                true,
            );

            return;
        };

        let command = &cli.command;

        let should_log = matches!(
            command,
            Some(Commands::Import {
                shared_directories: _,
                ignored_paths: _,
                local_directory: _,
                dry_run: _,
                no_reformat: _,
                force: _,
            })
        );

        if let Err(error) = match command {
            Some(Commands::Config {
                command: Some(command),
            }) => {
                config(command, config_path, &config_values, log_file.as_ref())
            }

            Some(Commands::Import {
                shared_directories,
                ignored_paths,
                local_directory,
                dry_run,
                no_reformat: _,
                force,
            }) => import(
                &config_values,
                shared_directories.as_ref(),
                ignored_paths.as_ref(),
                local_directory.as_ref(),
                log_file.as_ref(),
                *dry_run,
                *force,
            ),

            Some(Commands::Imported) => {
                imported(&config_values, log_file.as_ref());

                Ok(())
            }

            Some(Commands::Logs) => {
                logs(&config_values, log_file.as_ref());

                Ok(())
            }

            Some(Commands::Schedule { command }) => {
                schedule(&config_values, command.as_ref(), log_file.as_ref())
            }

            _ => Ok(()),
        } {
            log(
                &error.to_string(),
                &LogLevel::Error,
                log_file.as_ref(),
                should_log,
            );
        }
    } else {
        let message = cli.config_file.map_or_else(
            || "invalid value for `--config-file`".to_string(),
            |config_file| format!("{config_file} does not exist"),
        );

        log(&message, &LogLevel::Error, log_file.as_ref(), true);
    };
}
