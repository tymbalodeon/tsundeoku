use std::fs::{copy, create_dir_all, read_to_string, File, OpenOptions};
use std::io::{BufWriter, Write};
use std::path::{Path, PathBuf};
use std::string::ToString;
use std::vec::Vec;

use home::home_dir;
use symphonia::core::formats::FormatOptions;
use symphonia::core::io::{MediaSourceStream, MediaSourceStreamOptions};
use symphonia::core::meta::{MetadataOptions, StandardTagKey, Tag};
use symphonia::core::probe::Hint;
use walkdir::{DirEntry, WalkDir};

use crate::commands::config::ConfigFile;
use crate::get_app_name;
use crate::print_message;
use crate::LogLevel;

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
            PathBuf::from(shellexpand::tilde(path_name).to_string().as_str())
        },
    )
}

fn expand_paths(paths: &[PathBuf]) -> Vec<PathBuf> {
    paths.iter().map(expand_path).collect::<Vec<PathBuf>>()
}

impl ConfigFile {
    pub fn from_file(config_path: &Path) -> Self {
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

fn get_config_value<'a, T>(
    override_value: Option<&'a T>,
    config_value: &'a T,
) -> &'a T {
    override_value.map_or(config_value, |value| value)
}

fn get_imported_files_path() -> Option<PathBuf> {
    home_dir().map(|home| {
        home.join(".local/share")
            .join(get_app_name())
            .join("imported_files")
    })
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

fn get_tag(tags: &[Tag], tag_name: StandardTagKey) -> Option<&Tag> {
    tags.iter()
        .filter(|tag| tag.std_key.is_some_and(|key| key == tag_name))
        .collect::<Vec<&Tag>>()
        .first()
        .map(|tag| &**tag)
}

fn get_tag_or_unknown(tags: &[Tag], tag_name: StandardTagKey) -> String {
    get_tag(tags, tag_name)
        .map_or("Unknown".to_string(), |tag| tag.value.to_string())
}

pub fn import(
    config_values: &ConfigFile,
    shared_directories: Option<&Vec<PathBuf>>,
    ignored_paths: Option<&Vec<PathBuf>>,
    local_directory: Option<&PathBuf>,
    dry_run: bool,
    force: bool,
) {
    let shared_directories = get_config_value(
        shared_directories,
        &config_values.shared_directories,
    );

    let ignored_paths =
        get_config_value(ignored_paths, &config_values.ignored_paths);

    let local_directory =
        get_config_value(local_directory, &config_values.local_directory);

    let imported_files =
        (!force).then_some(get_imported_files_path().map_or_else(
            Vec::new,
            |imported_files_path| {
                read_to_string(imported_files_path).map_or_else(
                    |_| vec![],
                    |imported_files| {
                        imported_files.lines().map(PathBuf::from).collect()
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
                                imported_files
                                    .contains(&dir_entry.path().to_path_buf())
                            },
                        ) && Path::is_file(dir_entry.path())
                            && !ignored_paths
                                .contains(&dir_entry.path().to_path_buf())
                    })
                    .collect::<Vec<DirEntry>>()
            }
        })
        .collect();

    files.sort_by(|a, b| a.path().cmp(b.path()));

    let mut imported_files_log = get_imported_files_path().map(|path| {
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
                    File::open(file.path()).expect("failed to open media"),
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
                let artist =
                    get_tag_or_unknown(tags, StandardTagKey::AlbumArtist);
                let album = get_tag_or_unknown(tags, StandardTagKey::Album);
                let title =
                    get_tag_or_unknown(tags, StandardTagKey::TrackTitle);
                let track_display = format!("{artist} – {album} – {title}");

                if dry_run {
                    println!("{track_display}");
                } else {
                    print_message(track_display, &LogLevel::Import);

                    let file_name =
                        if let Some(file_name) = file.path().file_name() {
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
                                                                            // TODO handle weird characters!
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
                                                .and_then(|extension| {
                                                    extension.to_str()
                                                })
                                                .map(|extension| {
                                                    path.to_path_buf().join(
                                                        format!(
                                                        "{}__{}.{}",
                                                        stem,
                                                        latest_version_number
                                                            + 1,
                                                        extension,
                                                    ),
                                                    )
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
                            format!(
                                "failed to import {}",
                                file.path().display()
                            ),
                            &LogLevel::Error,
                        ),

                        Some(new_file) => {
                            if matches!(
                                &new_file.parent().map(create_dir_all),
                                Some(Ok(()))
                            ) {
                                match File::create_new(&new_file) {
                                    Ok(_) => {
                                        if let Err(error) =
                                            copy(file.path(), &new_file)
                                        {
                                            print_message(
                                                error.to_string(),
                                                &LogLevel::Error,
                                            );
                                        } else {
                                            imported_files_log.as_mut().map(
                                                        |imported_files| {
                                                            imported_files.as_mut().ok().map(
                                                                |imported_files| {
                                                                    if let Err(error) =
                                                                        imported_files.write(
                                                                            format!(
                                                                                "{}\n",
                                                                                file.path()
                                                                                    .display()
                                                                            )
                                                                            .as_bytes(),
                                                                        )
                                                                    {
                                                                        print_message(
                                                                            error.to_string(),
                                                                            &LogLevel::Error,
                                                                        );
                                                                    }
                                                                },
                                                            )
                                                        },
                                                    );
                                        }
                                    }

                                    Err(error) => {
                                        print_message(
                                            format!(
                                                "{} ({})",
                                                error,
                                                new_file.display()
                                            ),
                                            &LogLevel::Error,
                                        );
                                    }
                                }
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
