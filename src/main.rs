mod commands;

use std::fs::File;
// use std::fs::read_to_string;
use std::io::Write;
use std::path::{Path, PathBuf};
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
        log_file.write_all(message.as_bytes())?;
        eprintln!("{message}");
    }

    Ok(())
}

fn main() -> Result<()> {
    let cli = Cli::parse();

    let config_path = cli.config_file.as_ref().map_or_else(
        || {
            Ok::<String, Error>(
                get_home_directory()?
                    .join(".config")
                    .join(get_app_name())
                    .join(format!("{}.toml", get_app_name()))
                    .display()
                    .to_string(),
            )
        },
        |config_path| {
            Ok(Path::new(config_path)
                .parse_dot()?
                .to_str()
                .context(format!("invalid config file path {config_path}"))?
                .to_string())
        },
    )?;

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
            *dry_run,
            *force,
            *verbose,
        ),

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
    }
}
