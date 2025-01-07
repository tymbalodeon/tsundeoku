use std::env::var;
use std::path::{Path, PathBuf};
use std::process::Command;

use anyhow::Result;
use bat::PrettyPrinter;
use clap::{Subcommand, ValueEnum};
use serde::{Deserialize, Serialize};

use crate::print_message;
use crate::LogLevel;

#[derive(Debug, Deserialize, Serialize)]
pub struct ConfigFile {
    pub shared_directories: Vec<PathBuf>,
    pub ignored_paths: Vec<PathBuf>,
    pub local_directory: PathBuf,
}

#[derive(Clone, Debug, ValueEnum)]
pub enum ConfigKey {
    SharedDirectories,
    IgnoredPaths,
    LocalDirectory,
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
        .collect()
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
            Command::new(var("EDITOR")?).arg(config_path).status()?;
        }

        Config::Path => {
            println!("{}", config_path.display());
        }

        Config::Show { key } => {
            if let Some(key) = key {
                println!("{}", get_config_value_display(config_values, key));
            } else if let Err(error) =
                print_config(PrettyPrinter::new().input_file(config_path))
            {
                print_message(error.to_string(), &LogLevel::Warning);
                println!("{config_values:#?}");
            }
        }
    }

    Ok(())
}
