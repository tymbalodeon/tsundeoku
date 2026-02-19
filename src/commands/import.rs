use std::collections::HashSet;
use std::fs::{self, copy, create_dir_all, read_to_string, File, OpenOptions};
use std::io::Write;
use std::path::{Path, PathBuf};
use std::string::ToString;
use std::vec::Vec;

use anyhow::{anyhow, Context, Result};
use colored::Colorize;
use symphonia::core::formats::FormatOptions;
use symphonia::core::io::{MediaSourceStream, MediaSourceStreamOptions};
use symphonia::core::meta::{MetadataOptions, StandardTagKey, Tag};
use symphonia::core::probe::Hint;
use walkdir::WalkDir;

use crate::commands::config::get_config_value;
use crate::config::get_config;
use crate::{get_imported_files_path, log, LogLevel};

fn get_tag_or_unknown(tags: &[Tag], tag_name: StandardTagKey) -> String {
    tags.iter()
        .filter(|tag| tag.std_key.is_some_and(|key| key == tag_name))
        .collect::<Vec<&Tag>>()
        .first()
        .map(|tag| &**tag)
        .map_or_else(|| "Unknown".to_string(), |tag| tag.value.to_string())
}

fn get_parent_directory(path: &Path) -> Result<PathBuf> {
    Ok(path
        .parent()
        .context(format!("failed to get parent of {}", path.display()))?
        .to_path_buf())
}

fn matches_file_name(existing_file: &Path, new_file: &Path) -> Result<bool> {
    let existing_file_name = get_file_name(existing_file)?;
    let new_file_stem = get_file_stem(new_file)?;

    Ok(existing_file_name.contains(new_file_stem))
}

fn get_invalid_path_error(path: &Path) -> String {
    format!("invalid path {}", path.display())
}

fn get_file_name(path: &Path) -> Result<&str> {
    path.file_name()
        .with_context(|| get_invalid_path_error(path))?
        .to_str()
        .with_context(|| get_invalid_path_error(path))
}

fn get_file_stem(path: &Path) -> Result<&str> {
    path.file_stem()
        .with_context(|| get_invalid_path_error(path))?
        .to_str()
        .with_context(|| get_invalid_path_error(path))
}

fn copy_file(
    file: &PathBuf,
    local_directory: Option<PathBuf>,
    imported_files_log: &mut File,
    log_file: Option<&File>,
    dry_run: bool,
    is_scheduled: bool,
) -> Result<Option<u64>> {
    let mut hint = Hint::new();

    if let Some(extension) =
        file.extension().and_then(|extension| extension.to_str())
    {
        hint.with_extension(extension);
    }

    let Ok(mut probed) = symphonia::default::get_probe().format(
        &hint,
        MediaSourceStream::new(
            Box::new(File::open(file)?),
            MediaSourceStreamOptions::default(),
        ),
        &FormatOptions::default(),
        &MetadataOptions::default(),
    ) else {
        let should_warn = file.extension().is_none_or(|extension| {
            extension.to_str().is_none_or(|extension| {
                [
                    "aac", "adpcm", "aiff", "alac", "caf", "flac", "mkv",
                    "mp1", "mp2", "mp3", "mp4", "ogg", "vorbis", "wav",
                    "webm",
                ]
                .contains(&extension)
            })
        });

        if should_warn {
            log(
                &format!("failed to detect tags for {}", file.display()),
                &LogLevel::Warning,
                log_file,
                is_scheduled,
            );
        }

        return Ok(None);
    };

    let container_metadata = probed.format.metadata();
    let other_metadata = probed.metadata.get();

    let tags = container_metadata.current().map_or_else(
        || {
            other_metadata
                .as_ref()
                .and_then(|metadata| metadata.current())
                .map(symphonia_core::meta::MetadataRevision::tags)
                .context("failed to detect tags")
        },
        |metadata| Ok(metadata.tags()),
    )?;

    let artist = get_tag_or_unknown(tags, StandardTagKey::AlbumArtist);
    let album = get_tag_or_unknown(tags, StandardTagKey::Album);

    if dry_run {
        println!("{}", file.display());
    } else {
        match local_directory {
            Some(local_directory) => {
                log(
                    &format!("{} {}", "Importing".green(), file.display()),
                    &LogLevel::Info,
                    log_file,
                    is_scheduled,
                );

                let file_name = get_file_name(file)?;
                let mut new_file = local_directory;

                new_file.push(artist);
                new_file.push(album);
                new_file.push(file_name);

                let parent = get_parent_directory(&new_file)?;

                let latest_version_number = WalkDir::new(&parent)
                    .into_iter()
                    .filter_map(Result::ok)
                    .filter(|existing_file| {
                        matches_file_name(existing_file.path(), &new_file)
                            .unwrap_or_else(|_| {
                                panic!(
                                    "failed to compare {} to {}",
                                    existing_file.path().display(),
                                    new_file.display()
                                )
                            })
                    })
                    .filter_map(|existing_file| {
                        get_file_stem(existing_file.path()).ok().and_then(
                            |stem| {
                                if stem.contains("__") {
                                    stem.split("__").last().and_then(
                                        |number| number.parse::<usize>().ok(),
                                    )
                                } else {
                                    None
                                }
                            },
                        )
                    })
                    .max()
                    .unwrap_or_default();

                new_file = parent.join(format!(
                    "{}__{}.{}",
                    get_file_stem(&new_file)?,
                    latest_version_number + 1,
                    new_file
                        .extension()
                        .with_context(|| get_invalid_path_error(&new_file))?
                        .to_str()
                        .with_context(|| get_invalid_path_error(&new_file))?
                ));

                create_dir_all(&parent)?;
                File::create_new(&new_file)?;

                let copied = copy(file, &new_file);

                if copied.is_ok() {
                    imported_files_log.write_all(
                        format!("{}\n", file.display()).as_bytes(),
                    )?;
                }

                return Ok(Some(copied?));
            }

            None => return Ok(None),
        }
    }

    Ok(None)
}

fn sync_imported_files(
    files: &[PathBuf],
    imported_files_path: &Path,
) -> Result<Vec<PathBuf>> {
    let imported_files = read_to_string(imported_files_path)?;

    let current_imported_files: Vec<PathBuf> = imported_files
        .lines()
        .map(PathBuf::from)
        .collect::<HashSet<_>>()
        .intersection(&files.iter().cloned().collect::<HashSet<PathBuf>>())
        .cloned()
        .collect();

    let mut imported_files_log: Vec<String> = current_imported_files
        .iter()
        .map(|path| path.display().to_string())
        .collect();

    imported_files_log.push("\n".to_string());
    fs::write(imported_files_path, imported_files_log.join("\n"))?;

    Ok(current_imported_files)
}

pub fn get_files_to_import(
    shared_directories: &[PathBuf],
    ignored_paths: &Vec<PathBuf>,
    imported_files_path: &Path,
    force: bool,
) -> Result<Vec<PathBuf>> {
    let mut files: Vec<PathBuf> = shared_directories
        .iter()
        .flat_map(|directory| {
            WalkDir::new(directory)
                .into_iter()
                .filter_map(Result::ok)
                .filter(|dir_entry| {
                    if Path::is_file(dir_entry.path()) {
                        let mut include = true;

                        dir_entry.path().to_str().map_or(include, |path| {
                            if path.ends_with(".DS_Store") {
                                include = false;
                            } else {
                                for ignored_path in ignored_paths {
                                    if let Some(ignored_path) =
                                        ignored_path.to_str()
                                    {
                                        include = !path.contains(ignored_path);

                                        if !include {
                                            break;
                                        }
                                    }
                                }
                            }

                            include
                        })
                    } else {
                        false
                    }
                })
                .map(|dir_entry| dir_entry.path().to_path_buf())
                .collect::<Vec<PathBuf>>()
        })
        .collect();

    let imported_files: Option<Vec<PathBuf>> = if force {
        None
    } else {
        Some(sync_imported_files(&files, imported_files_path)?)
    };

    files = files
        .iter()
        .filter(|path| {
            force
                || imported_files.as_ref().is_some_and(|imported_files| {
                    !imported_files.contains(path)
                })
        })
        .cloned()
        .collect::<Vec<PathBuf>>();

    files.sort();

    Ok(files)
}

pub fn import(
    config_file: Option<&PathBuf>,
    shared_directories: Option<&Vec<PathBuf>>,
    ignored_paths: Option<&Vec<PathBuf>>,
    local_directory: Option<&PathBuf>,
    log_file: Option<&File>,
    dry_run: bool,
    force: bool,
    is_scheduled: bool,
) -> Result<()> {
    let config = get_config(config_file)?;

    let shared_directories =
        get_config_value(shared_directories, Some(&config.shared_directories));

    match shared_directories {
        Some(shared_directories) => {
            if shared_directories.is_empty() {
                log(
                    "shared-directories is not set",
                    &LogLevel::Warning,
                    log_file,
                    is_scheduled,
                );

                return Ok(());
            }

            let ignored_paths =
                get_config_value(ignored_paths, Some(&config.ignored_paths));

            let local_directory = get_config_value(
                local_directory,
                config.local_directory.as_ref(),
            );

            if !dry_run
                && local_directory
                    .is_none_or(|local_directory| !local_directory.exists())
            {
                return Err(anyhow!("local-directory does not exist"));
            }

            let imported_files_path = get_imported_files_path()?;

            let ignored_paths = if let Some(ignored_paths) = ignored_paths {
                ignored_paths
            } else {
                log(
                    "failed to read ignored-paths value",
                    &LogLevel::Warning,
                    log_file,
                    is_scheduled,
                );

                if dry_run {
                    &vec![]
                } else {
                    return Ok(());
                }
            };

            let files = get_files_to_import(
                shared_directories,
                ignored_paths,
                &imported_files_path,
                force,
            )?;

            let mut imported_files_log = OpenOptions::new()
                .append(true)
                .create(true)
                .open(imported_files_path)?;

            let mut imported = false;

            for file in files {
                match copy_file(
                    &file,
                    local_directory.cloned(),
                    &mut imported_files_log,
                    log_file,
                    dry_run,
                    is_scheduled,
                ) {
                    Ok(copied) => {
                        if copied.is_some() {
                            imported = true;
                        }
                    }

                    Err(error) => {
                        log(
                            &format!("{error}: {}", file.as_path().display()),
                            &LogLevel::Error,
                            log_file,
                            is_scheduled,
                        );
                    }
                }
            }

            if !dry_run && !imported {
                log(
                    "nothing to import",
                    &LogLevel::Info,
                    log_file,
                    is_scheduled,
                );
            }

            Ok(())
        }

        None => Ok(()),
    }
}
