use std::collections::HashSet;
use std::fs::OpenOptions;
use std::io::Write;
use std::path::PathBuf;

use anyhow::{anyhow, Result};

use crate::commands::config::get_config_value;
use crate::commands::import::get_files_to_import;
use crate::commands::imported::get_imported_files;
use crate::config::get_config;
use crate::{get_imported_files_path, log, LogLevel};

pub fn set_imported(
    config_file: Option<&PathBuf>,
    shared_directories: Option<&Vec<PathBuf>>,
    ignored_paths: Option<&Vec<PathBuf>>,
    force: bool,
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
                    None,
                    false,
                );

                return Ok(());
            }

            let ignored_paths =
                get_config_value(ignored_paths, Some(&config.ignored_paths))
                    .map_or_else(
                        || {
                            log(
                                "failed to read ignored-paths value",
                                &LogLevel::Warning,
                                None,
                                false,
                            );

                            vec![]
                        },
                        std::clone::Clone::clone,
                    );

            let mut imported_files = get_imported_files();

            let files_to_import: Vec<String> = get_files_to_import(
                shared_directories,
                &ignored_paths,
                &get_imported_files_path()?,
                force,
            )?
            .into_iter()
            .map(|path| path.to_string_lossy().to_string())
            .collect();

            imported_files.extend(files_to_import);

            let imported_files: Vec<String> = imported_files
                .into_iter()
                .collect::<HashSet<String>>()
                .into_iter()
                .collect();

            let mut imported_files_log = OpenOptions::new()
                .create(true)
                .truncate(true)
                .write(true)
                .open(get_imported_files_path()?)?;

            imported_files_log
                .write_all(imported_files.join("\n").as_bytes())?;

            println!("set all shared files as imported");

            Ok(())
        }

        None => Err(anyhow!("failed to determine shared-directories")),
    }
}
