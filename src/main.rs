use std::env::{current_dir, var};
use std::fs;
use std::path::{Path, PathBuf};
use std::process::Command;

use bat::PrettyPrinter;
use clap::{Parser, Subcommand, ValueEnum};
use colored::Colorize;
use serde::{Deserialize, Serialize};
use symphonia::core::formats::FormatOptions;
use symphonia::core::io::{MediaSourceStream, MediaSourceStreamOptions};
use symphonia::core::meta::{MetadataOptions, StandardTagKey, Tag};
use symphonia::core::probe::Hint;
use walkdir::WalkDir;

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

    /// Set config values
    Set,

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
    config_file: Option<String>,
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

#[derive(Debug, Deserialize, Serialize)]
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

impl ConfigFile {
    fn from_file(config_path: &Path) -> Self {
        fs::read_to_string(config_path).map_or_else(
            |_| Self::default(),
            |file| {
                // TODO
                // expand tilde in config values

                toml::from_str::<Self>(&file).unwrap_or_default()
            },
        )
    }
}

fn print_config(pretty_printer: &mut PrettyPrinter) {
    pretty_printer
        .theme("ansi")
        .language("toml")
        .print()
        .expect("Failed to print config");
}

fn expand_path(path: &str) -> PathBuf {
    Path::new(&shellexpand::tilde(path).into_owned()).to_path_buf()
}

fn get_default_shared_directories() -> Vec<PathBuf> {
    vec![expand_path("~/Dropbox")]
}

fn get_default_local_directory() -> PathBuf {
    expand_path("~/Music")
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

fn get_config_value_display(
    config: &ConfigFile,
    key: &ConfigKey,
) -> Option<String> {
    match key {
        ConfigKey::SharedDirectories => {
            Some(format!("{:?}", config.shared_directories))
        }

        ConfigKey::IgnoredPaths => Some(format!("{:?}", config.ignored_paths)),

        ConfigKey::LocalDirectory => config
            .local_directory
            .as_os_str()
            .to_str()
            .map(std::string::ToString::to_string),
    }
}

fn main() {
    let cli = Cli::parse();

    let config_path = cli.config_file.as_ref().map_or_else(
        get_default_config_path,
        |config_path| {
            let path = Path::new(config_path);

            if path.is_relative() {
                current_dir().map_or_else(
                    |_| get_default_config_path(),
                    |current_dir| {
                        current_dir
                            .join(path)
                            .to_str()
                            .map_or_else(get_default_config_path, |path| {
                                path.to_string()
                            })
                    },
                )
            } else {
                shellexpand::tilde(config_path).to_string()
            }
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
                    // TODO make proper error
                    println!("{} does not exist.", config_path.display());
                }
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
                    let probed_metadata = probed.metadata.get();

                    if let Some(tags) =
                        probed.format.metadata().current().map_or_else(
                            || {
                                probed_metadata
                                    .as_ref()
                                    .and_then(|metadata| metadata.current())
                                    .map(symphonia_core::meta::MetadataRevision::tags)
                            },
                            |metadata| Some(metadata.tags()),
                        )
                    {
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
                    } else {
                        println!(
                            "{} failed to detect tags for {}",
                            "warning:".yellow().bold(),
                            file.file_name().to_string_lossy()
                        );
                    }
                } else {
                    println!(
                        "{} failed to detect {} as audio file.",
                        "error:".red().bold(),
                        file.file_name().to_string_lossy()
                    );
                }
            }
        }

        Some(Commands::Logs) => {
            if let Ok(file) =
                fs::read_to_string(format!("/tmp/{}.log", get_app_name()))
            {
                println!("{file}");
            }
        }

        Some(Commands::Schedule {
            command: Some(command),
        }) => {
            println!("{command:?} is not yet implemented.");
        }

        _ => {}
    }
}
