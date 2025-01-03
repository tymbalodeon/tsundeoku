use std::env::var;
use std::fs;
use std::path::{Path, PathBuf};
use std::process::Command;

use bat::PrettyPrinter;
use clap::{Parser, Subcommand};
use colored::Colorize;
use serde::Deserialize;
use symphonia::core::formats::FormatOptions;
use symphonia::core::io::{MediaSourceStream, MediaSourceStreamOptions};
use symphonia::core::meta::{MetadataOptions, StandardTagKey, Tag};
use symphonia::core::probe::Hint;
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
        shared_directories: Option<Vec<PathBuf>>,

        #[arg(long)]
        #[arg(value_name = "PATH")]
        ignored_paths: Option<Vec<PathBuf>>,

        // #[arg(default_value = "~/Music")]
        #[arg(long)]
        #[arg(value_name = "DIR")]
        local_directory: Option<PathBuf>,

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

#[derive(Debug, Deserialize)]
struct ConfigFile {
    shared_directories: Vec<PathBuf>,
    ignored_paths: Vec<PathBuf>,
    local_directory: PathBuf,
}

impl Default for ConfigFile {
    fn default() -> Self {
        Self {
            shared_directories: get_default_shared_directories(),
            ignored_paths: vec![],
            local_directory: get_default_local_directory(),
        }
    }
}

fn get_default_shared_directories() -> Vec<PathBuf> {
    vec!["~/Dropbox".into()]
}

fn get_default_local_directory() -> PathBuf {
    "~/Music".into()
}

fn get_config_value<'a, T>(
    override_value: Option<&'a T>,
    config_value: &'a T,
) -> &'a T {
    override_value.map_or(config_value, |value| value)
}

fn get_tag(tags: &[Tag], tag_name: StandardTagKey) -> Option<&Tag> {
    tags.iter()
        .filter(|tag| tag.std_key.is_some_and(|key| key == tag_name))
        .collect::<Vec<&Tag>>()
        .first()
        .map(|tag| &**tag)
}

fn main() {
    let cli = Cli::parse();

    let config_path = cli
        .config_file
        .as_ref()
        .map_or_else(get_default_config_path, |path| {
            path.display().to_string()
        });

    let config_values = match toml::from_str::<ConfigFile>(
        &fs::read_to_string(&config_path).expect("Failed to read config file"),
    ) {
        Ok(values) => values,
        Err(error) => {
            // TODO Allow for incomplete config files
            eprintln!(
                "{}",
                format!("{}: {}", "config error".red(), error.message())
            );
            return;
        }
    };

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
            shared_directories,
            ignored_paths,
            local_directory,
            no_reformat: _,
            force: _,
        }) => {
            let shared_directories = get_config_value(
                shared_directories.as_ref(),
                &config_values.shared_directories,
            );

            let ignored_paths = get_config_value(
                ignored_paths.as_ref(),
                &config_values.ignored_paths,
            );

            let local_directory = get_config_value(
                local_directory.as_ref(),
                &config_values.local_directory,
            );

            println!("Importing files from {shared_directories:?}, ignoring {ignored_paths:?} to {local_directory:?}");

            let files = shared_directories.iter().flat_map(|directory| {
                WalkDir::new(directory)
                    .into_iter()
                    .filter_map(Result::ok)
                    .filter(|dir_entry| {
                        Path::is_file(dir_entry.path())
                            && !ignored_paths
                                .contains(&dir_entry.path().to_path_buf())
                    })
            });

            for file in files {
                let mut hint = Hint::new();

                if let Some(extension) = file
                    .path()
                    .extension()
                    .and_then(|extension| extension.to_str())
                {
                    hint.with_extension(extension);
                }

                if let Ok(mut probed) = symphonia::default::get_probe().format(
                    &hint,
                    MediaSourceStream::new(
                        Box::new(
                            std::fs::File::open(file.path())
                                .expect("failed to open media"),
                        ),
                        MediaSourceStreamOptions::default(),
                    ),
                    &FormatOptions::default(),
                    &MetadataOptions::default(),
                ) {
                    let metadata =
                        if let Some(metadata) = probed.metadata.get() {
                            metadata
                        } else {
                            probed.format.metadata()
                        };

                    if let Some(metadata) = metadata.current() {
                        let tags = metadata.tags();

                        let mut track_display = String::new();

                        let artist =
                            get_tag(tags, StandardTagKey::AlbumArtist);

                        if let Some(artist) = artist {
                            track_display
                                .push_str(&format!("{}", artist.value));
                        }

                        let album = get_tag(tags, StandardTagKey::Album);

                        if let Some(album) = album {
                            track_display
                                .push_str(&format!(" – {}", album.value));
                        }

                        let title = get_tag(tags, StandardTagKey::TrackTitle);

                        if let Some(title) = title {
                            track_display
                                .push_str(&format!(" – {}", title.value));
                        }

                        println!(
                            "  {} {}",
                            "Importing".green().bold(),
                            track_display
                        );
                    }
                } else {
                    println!(
                        "failed to read tags for file {}",
                        file.file_name().to_string_lossy()
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
