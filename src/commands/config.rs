use std::env::var;
use std::path::{Path, PathBuf};
use std::process::Command;

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

        /// Show the default config
        #[arg(long)]
        default: bool,
    },
}

fn get_path_vector_display(vector: &[PathBuf]) -> String {
    vector
        .iter()
        .filter_map(|item| item.as_os_str().to_str())
        .map(|item| item.trim().to_string())
        .collect::<Vec<String>>()
        .join("\n")
}

pub fn get_config_value_display(
    config: &ConfigFile,
    key: &ConfigKey,
) -> Option<String> {
    match key {
        ConfigKey::SharedDirectories => {
            Some(get_path_vector_display(&config.shared_directories))
        }

        ConfigKey::IgnoredPaths => {
            Some(get_path_vector_display(&config.ignored_paths))
        }

        ConfigKey::LocalDirectory => config
            .local_directory
            .as_os_str()
            .to_str()
            .map(ToString::to_string),
    }
}

pub fn print_config(pretty_printer: &mut PrettyPrinter) {
    pretty_printer
        .theme("ansi")
        .language("toml")
        .print()
        .expect("Failed to print config");
}

pub fn config(
    command: &Config,
    config_path: &Path,
    config_values: &ConfigFile,
) {
    match command {
        Config::Edit => {
            if let Ok(editor) = var("EDITOR") {
                Command::new(editor)
                    .arg(config_path)
                    .status()
                    .expect("Failed to open config file in editor.");
            }
        }

        Config::Path => {
            if let Some(path) = config_path.to_str() {
                println!("{path}");
            }
        }

        Config::Show { key, default } => {
            let default_config = ConfigFile::default();

            if *default {
                if let Some(key) = key {
                    if let Some(value) =
                        get_config_value_display(&default_config, key)
                    {
                        println!("{value}");
                    }
                } else if let Ok(default_config_toml) =
                    toml::to_string(&default_config)
                {
                    let default_config_toml = default_config_toml.into_bytes();

                    print_config(
                        PrettyPrinter::new()
                            .input_from_bytes(&default_config_toml),
                    );
                }
            } else if config_path.exists() {
                if let Some(key) = key {
                    if let Some(value) =
                        get_config_value_display(config_values, key)
                    {
                        println!("{value}");
                    }
                } else {
                    print_config(PrettyPrinter::new().input_file(config_path));
                }
            } else {
                print_message(
                    format!("{} does not exist.", config_path.display()),
                    &LogLevel::Error,
                );
            }
        }
    }
}
