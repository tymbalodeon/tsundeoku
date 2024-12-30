use std::path::{Path, PathBuf};

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
        #[arg(long, value_name = "TIME")]
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
        #[arg(long, value_name = "FILE")]
        shared_dirs: Option<PathBuf>,

        #[arg(long, value_name = "FILE")]
        ignored_paths: Option<PathBuf>,

        #[arg(long, value_name = "FILE")]
        local_dir: Option<PathBuf>,

        #[arg(short, long)]
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

    #[arg(long, value_name = "FILE")]
    config_file: Option<PathBuf>,
}

fn main() {
    let cli = Cli::parse();

    if let Some(config_path) = cli.config_file.as_deref() {
        println!("Value for config: {}", config_path.display());
    }

    match &cli.command {
        Some(Commands::Config {
            command: Some(command),
        }) => match command {
            Config::Show => {
                if let Some(home) = home::home_dir()
                    .filter(|path| !path.as_os_str().is_empty())
                {
                    println!(
                        "{}",
                        Path::new(&home)
                            .join(".config")
                            .join("tsundeoku")
                            .join("tsundeoku.toml")
                            .into_os_string()
                            .into_string()
                            .expect("Unable to determine $HOME path")
                    );
                }
            }

            _ => println!("{command:?} is not yet implemented."),
        },

        Some(Commands::Import {
            shared_dirs,
            ignored_paths,
            local_dir,
            force,
        }) => {
            println!(
                "{shared_dirs:?}, {ignored_paths:?}, {local_dir:?}, {force:?}"
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
