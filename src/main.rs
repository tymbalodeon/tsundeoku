use std::env::var;
use std::fs;
use std::path::PathBuf;
use std::process::Command;

use bat::PrettyPrinter;
use clap::{Parser, Subcommand};
use colored::Colorize;
use serde::Deserialize;
use walkdir::WalkDir;

#[derive(Subcommand, Debug)]
#[command(arg_required_else_help = true)]
enum Config {
    /// Open config file in $EDITOR
    Edit,

    /// Show config file path
    Path,

    /// Set config values
    Set,

    /// Show config values
    Show,
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
    /// Show and set config values
    Config {
        #[command(subcommand)]
        command: Option<Config>,
    },

    /// Import newly added audio files from shared folders to a local folder
    Import {
        // #[arg(default_value = "~/Dropbox")]
        #[arg(long)]
        #[arg(value_name = "DIR")]
        shared_dirs: Option<Vec<PathBuf>>,

        #[arg(long)]
        #[arg(value_name = "PATH")]
        ignored_paths: Option<Vec<PathBuf>>,

        // #[arg(default_value = "~/Music")]
        #[arg(long)]
        #[arg(value_name = "DIR")]
        local_dir: Option<PathBuf>,

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

    #[arg(long)]
    #[arg(value_name = "FILE")]
    config_file: Option<PathBuf>,
}

const fn get_app_name() -> &'static str {
    "tsundeoku"
}

fn get_default_config_path() -> String {
    home::home_dir()
        .expect("Unable to determine $HOME path")
        .join(".config")
        .join(get_app_name())
        .join(format!("{}.toml", get_app_name()))
        .into_os_string()
        .into_string()
        .expect("Unable to get default config path")
}

#[derive(Deserialize)]
struct ConfigFile {
    shared_dirs: Vec<PathBuf>,
    ignored_paths: Vec<PathBuf>,
    local_dir: PathBuf,
}

impl Default for ConfigFile {
    fn default() -> Self {
        Self {
            shared_dirs: get_default_shared_dirs(),
            ignored_paths: vec![],
            local_dir: get_default_local_dir(),
        }
    }
}

fn get_default_shared_dirs() -> Vec<PathBuf> {
    vec!["~/Dropbox".into()]
}

fn get_default_local_dir() -> PathBuf {
    "~/Music".into()
}

fn get_config_value<T>(override_value: Option<T>, config_value: T) -> T {
    override_value.map_or(config_value, |value| value)
}

fn main() {
    let cli = Cli::parse();

    let config_path = cli
        .config_file
        .as_ref()
        .map_or_else(get_default_config_path, |path| {
            path.display().to_string()
        });

    let config_values = toml::from_str::<ConfigFile>(
        &fs::read_to_string(&config_path).expect("Failed to read config file"),
    )
    .unwrap_or_default();

    match &cli.command {
        Some(Commands::Config {
            command: Some(command),
        }) => match command {
            Config::Edit => {
                if let Ok(editor) = var("EDITOR") {
                    Command::new(editor)
                        .arg(&config_path)
                        .status()
                        .expect("Failed to open config file in editor.");
                }
            }

            Config::Path => {
                println!("{}", &config_path);
            }

            Config::Show => {
                PrettyPrinter::new()
                    .input_file(&config_path)
                    .theme("ansi")
                    .print()
                    .expect("Failed to parse config file");
            }

            Config::Set => println!("{command:?} is not yet implemented."),
        },

        Some(Commands::Import {
            shared_dirs,
            ignored_paths,
            local_dir,
            no_reformat: _,
            force: _,
        }) => {
            let shared_dirs = get_config_value(
                shared_dirs.as_ref(),
                &config_values.shared_dirs,
            );

            let ignored_paths = get_config_value(
                ignored_paths.as_ref(),
                &config_values.ignored_paths,
            );

            let local_dir =
                get_config_value(local_dir.as_ref(), &config_values.local_dir);

            println!("Importing files from {shared_dirs:?}, ignoring {ignored_paths:?} to {local_dir:?}");

            for dir in shared_dirs {
                let dir = dir.as_path().to_string_lossy();

                for entry in
                    WalkDir::new(&*dir).into_iter().filter_map(Result::ok)
                {
                    println!(
                        "  {} {}",
                        "Importing".green().bold(),
                        entry.path().to_string_lossy().replace(&*dir, "")
                    );
                }
            }
        }

        Some(Commands::Logs) => {
            println!("Logs is not yet implemented.");
        }

        Some(Commands::Schedule {
            command: Some(command),
        }) => {
            println!("{command:?} is not yet implemented.");
        }

        _ => {}
    }
}
