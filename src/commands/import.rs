use std::fs::{copy, create_dir_all, read_to_string, File, OpenOptions};
use std::io::Write;
use std::path::{Path, PathBuf};
use std::string::ToString;
use std::vec::Vec;

use anyhow::{Context, Result};
use home::home_dir;
use symphonia::core::formats::FormatOptions;
use symphonia::core::io::{MediaSourceStream, MediaSourceStreamOptions};
use symphonia::core::meta::{MetadataOptions, StandardTagKey, Tag};
use symphonia::core::probe::Hint;
use walkdir::WalkDir;

use crate::commands::config::ConfigFile;
use crate::get_app_name;
use crate::print_message;
use crate::LogLevel;

impl Default for ConfigFile {
    fn default() -> Self {
        Self {
            // TODO don't use a default shared in case it contains tons of files that shouldn't be imported
            shared_directories: get_default_shared_directories(),
            ignored_paths: vec![],
            local_directory: get_default_local_directory(),
        }
    }
}

fn expand_path(path: &Path) -> PathBuf {
    shellexpand::tilde(&path.display().to_string())
        .to_string()
        .into()
}

fn expand_paths(paths: &[PathBuf]) -> Vec<PathBuf> {
    paths
        .iter()
        .map(|path| expand_path(path.as_path()))
        .collect::<Vec<PathBuf>>()
}

impl ConfigFile {
    pub fn from_file(config_path: &Path) -> Result<Self> {
        let file = read_to_string(config_path)?;

        let mut config_items =
            toml::from_str::<Self>(&file).unwrap_or_default();

        config_items.shared_directories =
            expand_paths(&config_items.shared_directories);

        config_items.ignored_paths = expand_paths(&config_items.ignored_paths);

        config_items.local_directory =
            expand_path(&config_items.local_directory);

        Ok(config_items)
    }
}

fn get_config_value<'a, T>(
    override_value: Option<&'a T>,
    config_value: &'a T,
) -> &'a T {
    override_value.map_or(config_value, |value| value)
}

fn get_imported_files_path() -> Result<PathBuf> {
    Ok(home_dir()
        .context("could not determine $HOME directory")?
        .join(".local/share")
        .join(get_app_name())
        .join("imported_files"))
}

fn expand_str_to_path(path: &str) -> PathBuf {
    PathBuf::from(shellexpand::tilde(path).into_owned())
}

// TODO remove this, don't use default
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

fn matches_filename(existing_file: &Path, new_file: &Path) -> Result<bool> {
    let existing_file_error =
        || format!("failed to get filename for {}", existing_file.display());

    let existing_file_stem = existing_file
        .file_name()
        .with_context(existing_file_error)?
        .to_str()
        .with_context(existing_file_error)?;

    let new_file_error =
        || format!("failed to get filename for {}", new_file.display());

    let new_file_stem = new_file
        .file_stem()
        .with_context(new_file_error)?
        .to_str()
        .with_context(new_file_error)?;

    Ok(existing_file_stem.contains(new_file_stem))
}

fn copy_file(
    file: &PathBuf,
    local_directory: PathBuf,
    imported_files_log: &mut File,
    dry_run: bool,
) -> Result<()> {
    let mut hint = Hint::new();

    if let Some(extension) =
        file.extension().and_then(|extension| extension.to_str())
    {
        hint.with_extension(extension);
    }

    let mut probed = if let Ok(probed) = symphonia::default::get_probe()
        .format(
            &hint,
            MediaSourceStream::new(
                Box::new(File::open(file)?),
                MediaSourceStreamOptions::default(),
            ),
            &FormatOptions::default(),
            &MetadataOptions::default(),
        ) {
        probed
    } else {
        print_message(
            format!(
                "failed to read audio file metadata for {}",
                file.as_path().display()
            ),
            &LogLevel::Warning,
        );

        return Ok(());
    };

    let container_metadata = probed.format.metadata();
    let other_metadata = probed.metadata.get();

    let tags = container_metadata.current().map_or_else(
        || {
            other_metadata
                .as_ref()
                .and_then(|metadata| metadata.current())
                .map(symphonia_core::meta::MetadataRevision::tags)
                .with_context(|| {
                    format!("failed to detect tags for {} ", file.display())
                })
        },
        |metadata| Ok(metadata.tags()),
    )?;

    let artist = get_tag_or_unknown(tags, StandardTagKey::AlbumArtist);
    let album = get_tag_or_unknown(tags, StandardTagKey::Album);
    let title = get_tag_or_unknown(tags, StandardTagKey::TrackTitle);
    let track_display = format!("{artist} – {album} – {title}");

    if dry_run {
        println!("{track_display}");
    } else {
        print_message(track_display, &LogLevel::Import);

        let file_name = {
            let error =
                || format!("failed to get file name for {}", file.display());

            file.file_name()
                .with_context(error)?
                .to_str()
                .with_context(error)?
        };

        let mut new_file = local_directory;

        new_file.push(artist);
        new_file.push(album);
        new_file.push(file_name);

        let latest_version_number =
            WalkDir::new(new_file.parent().with_context(|| {
                format!("failed to get parent of {}", new_file.display())
            })?)
            .into_iter()
            .filter_map(Result::ok)
            .filter(|existing_file| {
                matches_filename(existing_file.path(), &new_file)
                    .unwrap_or_else(|_| {
                        panic!(
                            "failed to compare {} to {}",
                            existing_file.path().display(),
                            new_file.display()
                        )
                    })
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

        let file_error =
            |item| format!("failed to get {item} for {}", new_file.display());

        new_file = new_file.parent().with_context(|| "")?.to_path_buf().join(
            format!(
                "{}__{}.{}",
                new_file
                    .file_stem()
                    .with_context(|| file_error("stem"))?
                    .to_str()
                    .with_context(|| file_error("stem"))?,
                latest_version_number + 1,
                new_file
                    .extension()
                    .with_context(|| file_error("extension"))?
                    .to_str()
                    .with_context(|| file_error("extension"))?
            ),
        );

        create_dir_all(new_file.parent().with_context(|| {
            format!("failed to get parent of {}", new_file.display())
        })?)?;

        File::create_new(&new_file)?;

        let copied = copy(file, &new_file);

        if copied.is_ok() {
            imported_files_log
                .write_all(format!("{}\n", file.display()).as_bytes())?;
        }

        copied?;
    }

    Ok(())
}

pub fn import(
    config_values: &ConfigFile,
    shared_directories: Option<&Vec<PathBuf>>,
    ignored_paths: Option<&Vec<PathBuf>>,
    local_directory: Option<&PathBuf>,
    dry_run: bool,
    force: bool,
) -> Result<()> {
    let shared_directories = get_config_value(
        shared_directories,
        &config_values.shared_directories,
    );

    let ignored_paths =
        get_config_value(ignored_paths, &config_values.ignored_paths);

    let local_directory =
        get_config_value(local_directory, &config_values.local_directory);

    let imported_files: Option<Vec<PathBuf>> = if force {
        None
    } else {
        Some(
            read_to_string(get_imported_files_path()?)?
                .lines()
                .map(PathBuf::from)
                .collect::<Vec<PathBuf>>(),
        )
    };

    let mut files: Vec<PathBuf> = shared_directories
        .iter()
        .flat_map(|directory| {
            WalkDir::new(directory)
                .into_iter()
                .filter_map(Result::ok)
                .filter(|dir_entry| {
                    !imported_files.as_ref().is_some_and(|imported_files| {
                        imported_files
                            .contains(&dir_entry.path().to_path_buf())
                    }) && Path::is_file(dir_entry.path())
                        && !ignored_paths
                            .contains(&dir_entry.path().to_path_buf())
                })
                .map(|dir_entry| dir_entry.path().to_path_buf())
                .collect::<Vec<PathBuf>>()
        })
        .collect();

    files.sort();

    let mut imported_files_log =
        OpenOptions::new().create(true).append(true).open(
            get_imported_files_path()
                .context("failed to get imported files log path")?,
        )?;

    for file in files {
        if let Err(error) = copy_file(
            &file,
            local_directory.to_owned(),
            &mut imported_files_log,
            dry_run,
        ) {
            print_message(error.to_string(), &LogLevel::Error);

            print_message(
                file.as_path().display().to_string(),
                &LogLevel::Error,
            );
        }
    }

    Ok(())
}
