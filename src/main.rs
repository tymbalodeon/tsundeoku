mod commands;

use std::fs::{read_to_string, File, OpenOptions};
// use std::fs::read_to_string;
use std::io::Write;
use std::path::{Path, PathBuf};
use std::str::FromStr;
use std::string::ToString;
use std::vec::Vec;

use anyhow::{Context, Error, Result};
use clap::{Parser, Subcommand};
use colored::Colorize;
use commands::schedule::{schedule, Schedule};
use home::home_dir;
use path_dedot::ParseDot;

use crate::commands::config::config;
use crate::commands::config::Config;
use crate::commands::config::ConfigFile;
use crate::commands::import::import;

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

        #[arg(long)]
        #[arg(long)]
        verbose: bool,
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
    home_dir().context("could not determine $HOME directory")
}

const fn get_app_name() -> &'static str {
    "tsundeoku"
}

pub enum LogLevel {
    Import,
    Warning,
    Error,
}

pub fn log<T: AsRef<str>>(
    message: T,
    level: &LogLevel,
    log_file: &mut File,
) -> Result<()> {
    let label = match level {
        LogLevel::Import => "   Importing".green().to_string(),
        LogLevel::Warning => format!("{}:", "warning".yellow()),
        LogLevel::Error => format!("{}:", "error".red()),
    };

    let message = format!("{} {}", label.bold(), message.as_ref());

    if matches!(level, LogLevel::Import) {
        println!("{message}");
    } else {
        eprintln!("{message}");
        log_file.write_all(format!("{message}\n").as_bytes())?;
    }

    Ok(())
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
                    .context("the")?
                    .to_str()
                    .context("YO")?,
            )?)
        },
    )
}

pub fn get_state_directory() -> Result<PathBuf> {
    Ok(get_home_directory()?
        .join(".local/state")
        .join(get_app_name()))
}

fn get_imported_files_path() -> Result<PathBuf> {
    Ok(get_state_directory()?
        .join(format!("{}-imported-files.log", get_app_name())))
}

fn get_log_path() -> Result<PathBuf> {
    Ok(get_state_directory()?.join(format!("{}.log", get_app_name())))
}

fn main() -> Result<()> {
    let cli = Cli::parse();

    let mut log_file = OpenOptions::new()
        .create(true)
        .append(true)
        .open(get_log_path()?)?;

    if let Ok(config_path) = get_config_file(cli.config_file.as_ref()) {
        let config_path = Path::new(&config_path);
        let config_values = ConfigFile::from_file(config_path)?;

        match &cli.command {
            Some(Commands::Config {
                command: Some(command),
            }) => config(command, config_path, &config_values),

            Some(Commands::Import {
                shared_directories,
                ignored_paths,
                local_directory,
                dry_run,
                no_reformat: _,
                force,
                verbose,
            }) => import(
                &config_values,
                shared_directories.as_ref(),
                ignored_paths.as_ref(),
                local_directory.as_ref(),
                &mut log_file,
                *dry_run,
                *force,
                *verbose,
            ),

            Some(Commands::Imported) => {
                let imported_files =
                    read_to_string(get_imported_files_path()?)?;

                let mut lines: Vec<&str> =
                    imported_files.trim().lines().collect();

                lines.sort_unstable();

                println!("{}", lines.join("\n"));

                Ok(())
            }

            Some(Commands::Logs) => {
                todo!();
                // if let Ok(file) = read_to_string(format!("/tmp/{}.log", get_app_name())) {
                //     println!("{file}");
                // }
            }

            Some(Commands::Schedule { command }) => {
                schedule(command.as_ref())?;

                Ok(())
            }

            _ => todo!(),
        }?;
    } else {
        log("bad", &LogLevel::Error, &mut log_file)?;
    };

    Ok(())
}
