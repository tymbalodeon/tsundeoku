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

use crate::commands::config::{get_config_value, ConfigFile};
use crate::{get_imported_files_path, log, LogLevel};

fn get_tag_or_unknown(tags: &[Tag], tag_name: StandardTagKey) -> String {
    tags.iter()
        .filter(|tag| tag.std_key.is_some_and(|key| key == tag_name))
        .collect::<Vec<&Tag>>()
        .first()
        .map(|tag| &**tag)
        .map_or("Unknown".to_string(), |tag| tag.value.to_string())
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
    local_directory: PathBuf,
    imported_files_log: &mut File,
    log_file: Option<&File>,
    dry_run: bool,
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
        let should_warn = file.extension().map_or(true, |extension| {
            extension.to_str().map_or(true, |extension| {
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
                &format!(
                    "failed to read audio file metadata for {}",
                    file.as_path().display()
                ),
                &LogLevel::Warning,
                log_file,
                true,
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
                .context(format!(
                    "failed to detect tags for {} ",
                    file.display()
                ))
        },
        |metadata| Ok(metadata.tags()),
    )?;

    let artist = get_tag_or_unknown(tags, StandardTagKey::AlbumArtist);
    let album = get_tag_or_unknown(tags, StandardTagKey::Album);

    if dry_run {
        println!("{}", file.display());
    } else {
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
                get_file_stem(existing_file.path()).ok().and_then(|stem| {
                    if stem.contains("__") {
                        stem.split("__")
                            .last()
                            .and_then(|number| number.parse::<usize>().ok())
                    } else {
                        None
                    }
                })
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
            imported_files_log
                .write_all(format!("{}\n", file.display()).as_bytes())?;
        }

        log(
            &format!(
                "{} {}",
                "  Imported".green(),
                file.display()
            ),
            &LogLevel::Info,
            log_file,
            true,
        );

        return Ok(Some(copied?));
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

pub fn import(
    config_values: &ConfigFile,
    shared_directories: Option<&Vec<PathBuf>>,
    ignored_paths: Option<&Vec<PathBuf>>,
    local_directory: Option<&PathBuf>,
    log_file: Option<&File>,
    dry_run: bool,
    force: bool,
) -> Result<()> {
    let shared_directories = get_config_value(
        shared_directories,
        &config_values.shared_directories,
    );

    if shared_directories.is_empty() {
        let error_message = "shared-directories is not set";

        log(error_message, &LogLevel::Error, log_file, true);

        return Err(anyhow!(error_message));
    }

    let ignored_paths =
        get_config_value(ignored_paths, &config_values.ignored_paths);

    let local_directory =
        get_config_value(local_directory, &config_values.local_directory);

    let mut files: Vec<PathBuf> = shared_directories
        .iter()
        .flat_map(|directory| {
            WalkDir::new(directory)
                .into_iter()
                .filter_map(Result::ok)
                .filter(|dir_entry| {
                    Path::is_file(dir_entry.path())
                        && !ignored_paths
                            .contains(&dir_entry.path().to_path_buf())
                })
                .map(|dir_entry| dir_entry.path().to_path_buf())
                .collect::<Vec<PathBuf>>()
        })
        .collect();

    let imported_files_path = get_imported_files_path()?;

    let imported_files: Option<Vec<PathBuf>> = if force {
        None
    } else {
        Some(sync_imported_files(&files, &imported_files_path)?)
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

    let mut imported_files_log = OpenOptions::new()
        .create(true)
        .append(true)
        .open(imported_files_path)?;

    let mut imported = false;

    for file in files {
        match copy_file(
            &file,
            local_directory.to_owned(),
            &mut imported_files_log,
            log_file,
            dry_run,
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
                    true,
                );
            }
        };
    }

    if !imported {
        log("nothing to import", &LogLevel::Info, log_file, true);
    }

    Ok(())
}
