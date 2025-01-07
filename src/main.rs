mod commands;

use std::env::var;
use std::fs::read_to_string;
use std::path::{Path, PathBuf};
use std::process::Command;
use std::string::ToString;
use std::vec::Vec;

use bat::PrettyPrinter;
use clap::{Parser, Subcommand, ValueEnum};
use home::home_dir;
use path_dedot::ParseDot;

use crate::commands::import::import;
use crate::commands::import::print_message;
use crate::commands::import::ConfigFile;
use crate::commands::import::LogLevel;

#[derive(Clone, Debug, ValueEnum)]
enum ConfigKey {
    SharedDirectories,
    IgnoredPaths,
    LocalDirectory,
}

#[derive(Subcommand, Debug)]
#[command(arg_required_else_help = true)]
enum Config {
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

#[derive(Subcommand, Debug)]
#[command(arg_required_else_help = true)]
enum Schedule {
    /// Enabled scheduled imports
    Enable {
        #[arg(long)]
        #[arg(value_name = "TIME")]
        time: Option<String>,
    },

    /// Disable scheduled imports
    Disable,

    /// Show schedule status
    Status,
}

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

const fn get_app_name() -> &'static str {
    "tsundeoku"
}

fn get_default_config_path() -> String {
    home_dir()
        .expect("Unable to determine $HOME path")
        .join(".config")
        .join(get_app_name())
        .join(format!("{}.toml", get_app_name()))
        .into_os_string()
        .into_string()
        .expect("Unable to get default config path")
}

fn print_config(pretty_printer: &mut PrettyPrinter) {
    pretty_printer
        .theme("ansi")
        .language("toml")
        .print()
        .expect("Failed to print config");
}

fn get_path_vector_display(vector: &[PathBuf]) -> String {
    vector
        .iter()
        .filter_map(|item| item.as_os_str().to_str())
        .map(|item| item.trim().to_string())
        .collect::<Vec<String>>()
        .join("\n")
}

fn get_config_value_display(
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

fn main() {
    let cli = Cli::parse();

    let config_path = cli.config_file.as_ref().map_or_else(
        get_default_config_path,
        |config_path| {
            Path::new(config_path).parse_dot().map_or(
                shellexpand::tilde(config_path).to_string(),
                |path| {
                    path.to_str().map_or_else(
                        || shellexpand::tilde(config_path).to_string(),
                        ToString::to_string,
                    )
                },
            )
        },
    );

    let config_path = Path::new(&config_path);
    let config_values = ConfigFile::from_file(config_path);

    match &cli.command {
        Some(Commands::Config {
            command: Some(command),
        }) => match command {
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
                        let default_config_toml =
                            default_config_toml.into_bytes();

                        print_config(
                            PrettyPrinter::new()
                                .input_from_bytes(&default_config_toml),
                        );
                    }
                } else if config_path.exists() {
                    if let Some(key) = key {
                        if let Some(value) =
                            get_config_value_display(&config_values, key)
                        {
                            println!("{value}");
                        }
                    } else {
                        print_config(
                            PrettyPrinter::new().input_file(config_path),
                        );
                    }
                } else {
                    print_message(
                        format!("{} does not exist.", config_path.display()),
                        &LogLevel::Error,
                    );
                }
            }
        },

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
            *dry_run,
            *force,
        ),

        Some(Commands::Logs) => {
            if let Ok(file) =
                read_to_string(format!("/tmp/{}.log", get_app_name()))
            {
                println!("{file}");
            }
        }

        Some(Commands::Schedule { command: Some(_) }) => {
            todo!();
        }

        _ => {}
    }
}
