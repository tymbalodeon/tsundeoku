use std::path::PathBuf;

use bat::PrettyPrinter;
use clap::{Parser, Subcommand};

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
        #[arg(default_value = "~/Dropbox")]
        #[arg(long)]
        #[arg(value_name = "DIR")]
        shared_dirs: Option<Vec<PathBuf>>,

        #[arg(long)]
        #[arg(value_name = "PATH")]
        ignored_paths: Option<Vec<PathBuf>>,

        #[arg(default_value = "~/Music")]
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

fn get_config_path(override_path: Option<&PathBuf>) -> String {
    override_path.map_or_else(get_default_config_path, |path| {
        path.display().to_string()
    })
}

// #[derive(Debug, Deserialize)]
// struct ConfigFile {
//     shared_directories: Vec<String>,
//     ignored_paths: Vec<String>,
//     local_directory: String,
// }

fn main() {
    let cli = Cli::parse();

    match &cli.command {
        Some(Commands::Config {
            command: Some(command),
        }) => match command {
            Config::Path => {
                println!("{}", get_config_path(cli.config_file.as_ref()));
            }

            Config::Show => {
                PrettyPrinter::new()
                    .input_file(get_config_path(cli.config_file.as_ref()))
                    .theme("ansi")
                    .print()
                    .expect("Failed to parse config file");
            }
            _ => println!("{command:?} is not yet implemented."),
        },

        Some(Commands::Import {
            shared_dirs,
            ignored_paths,
            local_dir,
            no_reformat,
            force,
        }) => {
            println!(
                "{shared_dirs:?}, {ignored_paths:?}, {local_dir:?}, {no_reformat:?}, {force:?}"
            );
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
