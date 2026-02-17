use std::{collections::HashSet, path::PathBuf};

use anyhow::{anyhow, Result};

use crate::{
    commands::{
        config::get_config_value, import::get_files_to_import,
        imported::get_imported_files,
    },
    config::get_config,
    get_imported_files_path, log, LogLevel,
};

pub fn status(
    config_file: Option<&PathBuf>,
    shared_directories: Option<&Vec<PathBuf>>,
    ignored_paths: Option<&Vec<PathBuf>>,
    list_unimported: bool,
    force: bool,
) -> Result<()> {
    let config = get_config(config_file)?;

    let shared_directories =
        get_config_value(shared_directories, Some(&config.shared_directories));

    match shared_directories {
        Some(shared_directories) => {
            if shared_directories.is_empty() {
                return Err(anyhow!("shared-directories is not set"));
            }

            let ignored_paths =
                get_config_value(ignored_paths, Some(&config.ignored_paths));

            let ignored_paths = if let Some(ignored_paths) = ignored_paths {
                ignored_paths
            } else {
                log(
                    "failed to read ignored-paths value",
                    &LogLevel::Warning,
                    None,
                    false,
                );

                &vec![]
            };

            let files_to_import: HashSet<String> = get_files_to_import(
                shared_directories,
                ignored_paths,
                &get_imported_files_path()?,
                force,
            )?
            .iter()
            .map(|file| file.to_string_lossy().to_string())
            .collect();

            let imported_files: HashSet<String> =
                get_imported_files().into_iter().collect();

            let difference: Vec<String> = files_to_import
                .difference(&imported_files)
                .map(std::borrow::ToOwned::to_owned)
                .collect();

            if difference.is_empty() {
                println!("up to date!");
            } else if list_unimported {
                println!("{}", difference.join("\n"));
            } else {
                println!("import required");
            }

            Ok(())
        }

        None => Ok(()),
    }
}
