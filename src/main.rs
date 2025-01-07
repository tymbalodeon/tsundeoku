use std::env::var;
use std::fs::{copy, read_to_string, File, OpenOptions};
use std::io::{BufWriter, Write};
use std::path::{Path, PathBuf};
use std::process::Command;
use std::str::FromStr;
use std::string::ToString;
use std::vec::Vec;

use bat::PrettyPrinter;
use clap::{Parser, Subcommand, ValueEnum};
use colored::Colorize;
use home::home_dir;
use path_dedot::ParseDot;
use serde::{Deserialize, Serialize};
use symphonia::core::formats::FormatOptions;
use symphonia::core::io::{MediaSourceStream, MediaSourceStreamOptions};
use symphonia::core::meta::{MetadataOptions, StandardTagKey, Tag};
use symphonia::core::probe::Hint;
use walkdir::{DirEntry, WalkDir};

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

fn expand_path(path: &PathBuf) -> PathBuf {
    path.as_os_str().to_str().map_or_else(
        || path.to_owned(),
        |path_name| {
            PathBuf::from_str(
                shellexpand::tilde(path_name).to_string().as_str(),
            )
            .unwrap_or_else(|_| path.to_owned())
        },
    )
}

fn expand_paths(paths: &[PathBuf]) -> Vec<PathBuf> {
    paths.iter().map(expand_path).collect::<Vec<PathBuf>>()
}

impl ConfigFile {
    fn from_file(config_path: &Path) -> Self {
        read_to_string(config_path).map_or_else(
            |_| Self::default(),
            |file| {
                let mut config_items =
                    toml::from_str::<Self>(&file).unwrap_or_default();

                config_items.shared_directories =
                    expand_paths(&config_items.shared_directories);

                config_items.ignored_paths =
                    expand_paths(&config_items.ignored_paths);

                config_items.local_directory =
                    expand_path(&config_items.local_directory);

                config_items
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

fn expand_str_to_path(path: &str) -> PathBuf {
    Path::new(&shellexpand::tilde(path).into_owned()).to_path_buf()
}

fn get_default_shared_directories() -> Vec<PathBuf> {
    vec![expand_str_to_path("~/Dropbox")]
}

fn get_default_local_directory() -> PathBuf {
    expand_str_to_path("~/Music")
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

enum LogLevel {
    Import,
    Warning,
    Error,
}

fn print_message<T: AsRef<str>>(message: T, level: &LogLevel) {
    let label = match level {
        LogLevel::Import => "  Importing".green(),
        LogLevel::Warning => "warning:".yellow(),
        LogLevel::Error => "error:".red(),
    };

    let message = format!("{} {}", label.bold(), message.as_ref());

    match level {
        LogLevel::Error => eprintln!("{message}"),
        _ => println!("{message}"),
    }
}

fn get_tag_or_unknown(tags: &[Tag], tag_name: StandardTagKey) -> String {
    get_tag(tags, tag_name)
        .map_or("Unknown".to_string(), |tag| tag.value.to_string())
}

fn get_imported_files_path() -> Option<PathBuf> {
    home_dir().map(|home| {
        home.join(".local/share")
            .join(get_app_name())
            .join("imported_files")
    })
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

            let imported_files =
                (!force).then_some(get_imported_files_path().map_or_else(
                    Vec::new,
                    |imported_files_path| {
                        read_to_string(imported_files_path).map_or_else(
                            |_| vec![],
                            |imported_files| {
                                imported_files
                                    .lines()
                                    .map(PathBuf::from)
                                    .collect()
                            },
                        )
                    },
                ));

            let mut files: Vec<DirEntry> = shared_directories
                .iter()
                .flat_map(|directory| {
                    {
                        WalkDir::new(directory)
                            .into_iter()
                            .filter_map(Result::ok)
                            .filter(|dir_entry| {
                                !imported_files.as_ref().is_some_and(
                                    |imported_files| {
                                        imported_files.contains(
                                            &dir_entry.path().to_path_buf(),
                                        )
                                    },
                                ) && Path::is_file(dir_entry.path())
                                    && !ignored_paths.contains(
                                        &dir_entry.path().to_path_buf(),
                                    )
                            })
                            .collect::<Vec<DirEntry>>()
                    }
                })
                .collect();

            files.sort_by(|a, b| a.path().cmp(b.path()));

            let mut imported_files_log =
                get_imported_files_path().map(|path| {
                    OpenOptions::new()
                        .create(true)
                        .append(true)
                        .open(path)
                        .map(BufWriter::new)
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
                            File::open(file.path())
                                .expect("failed to open media"),
                        ),
                        MediaSourceStreamOptions::default(),
                    ),
                    &FormatOptions::default(),
                    &MetadataOptions::default(),
                ) {
                    let probed_metadata = probed.metadata.get();

                    if let Some(tags) = probed.format.metadata().current().map_or_else(
                        || {
                            probed_metadata
                                .as_ref()
                                .and_then(|metadata| metadata.current())
                                .map(symphonia_core::meta::MetadataRevision::tags)
                        },
                        |metadata| Some(metadata.tags()),
                    ) {
                        let artist = get_tag_or_unknown(tags, StandardTagKey::AlbumArtist);
                        let album = get_tag_or_unknown(tags, StandardTagKey::Album);
                        let title = get_tag_or_unknown(tags, StandardTagKey::TrackTitle);
                        let track_display = format!("{artist} – {album} – {title}");

                        if *dry_run {
                            println!("{track_display}");
                        } else {
                            print_message(track_display, &LogLevel::Import);

                            let file_name = if let Some(file_name) = file.path().file_name() {
                                file_name
                                    .to_os_string()
                                    .into_string()
                                    .map_or(title, |file_name| file_name)
                            } else {
                                title
                            };

                            let mut new_file = local_directory.to_owned();

                            new_file.push(artist);
                            new_file.push(album);
                            new_file.push(file_name);

                            let new_file = if new_file.exists() {
                                if let Some(parent) = new_file.parent() {
                                    let latest_version_number = WalkDir::new(parent)
                                        .into_iter()
                                        .filter_map(Result::ok)
                                        .filter(|existing_file| {
                                            existing_file.path().file_name().is_some_and(
                                                |existing_file| {
                                                    existing_file.to_str().is_some_and(
                                                        |existing_file| {
                                                            new_file.file_stem().is_some_and(
                                                                |file_name| {
                                                                    file_name.to_str().is_some_and(
                                                                        |file_name| {
                                                                            existing_file
                                                                                .contains(file_name)
                                                                        },
                                                                    )
                                                                },
                                                            )
                                                        },
                                                    )
                                                },
                                            )
                                        })
                                        .filter_map(|existing_file| {
                                            existing_file
                                                .path()
                                                .file_stem()
                                                .and_then(|stem| stem.to_str())
                                                .and_then(|stem| {
                                                    if stem.contains("__") {
                                                        stem.split("__").last().and_then(|number| {
                                                            number.parse::<usize>().ok()
                                                        })
                                                    } else {
                                                        None
                                                    }
                                                })
                                        })
                                        .max()
                                        .unwrap_or_default();

                                    new_file.parent().map_or_else(
                                        || Some(new_file.clone()),
                                        |path| {
                                            new_file
                                                .file_stem()
                                                .and_then(|stem| stem.to_str())
                                                .and_then(|stem| {
                                                    new_file
                                                        .extension()
                                                        .and_then(|extension| extension.to_str())
                                                        .map(|extension| {
                                                            path.to_path_buf().join(format!(
                                                                "{}__{}.{}",
                                                                stem,
                                                                latest_version_number + 1,
                                                                extension,
                                                            ))
                                                        })
                                                })
                                        },
                                    )
                                } else {
                                    Some(new_file)
                                }
                            } else {
                                Some(new_file)
                            };

                            match new_file {
                                None => print_message(
                                    format!("failed to import {}", file.path().display()),
                                    &LogLevel::Error,
                                ),

                                Some(new_file) => {
                                    if let Err(error) = copy(file.path(), &new_file) {
                                        print_message(error.to_string(), &LogLevel::Error);
                                    } else {
                                        imported_files_log.as_mut().map(|imported_files| {
                                            imported_files.as_mut().ok().map(|imported_files| {
                                                if let Err(error) = imported_files.write(
                                                    file.path().display().to_string().as_bytes(),
                                                ) {
                                                    print_message(
                                                        error.to_string(),
                                                        &LogLevel::Error,
                                                    );
                                                }
                                            })
                                        });
                                    }
                                }
                            }
                        }
                    } else {
                        print_message(
                            format!(
                                "failed to detect tags for {}",
                                file.file_name().to_string_lossy()
                            ),
                            &LogLevel::Warning,
                        );
                    }
                } else {
                    print_message(
                        format!(
                            "{} is not a recognized file type.",
                            file.file_name().to_string_lossy()
                        ),
                        &LogLevel::Error,
                    );
                }
            }
        }

        Some(Commands::Logs) => {
            if let Ok(file) =
                read_to_string(format!("/tmp/{}.log", get_app_name()))
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
