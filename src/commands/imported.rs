use std::{
    fs::{read_to_string, File},
    path::PathBuf,
};

use anyhow::Result;

use crate::{
    config::get_config, get_imported_files_path, log,
    warn_about_missing_shared_directories, LogLevel,
};

pub fn imported(
    config_file: Option<&PathBuf>,
    log_file: Option<&File>,
    is_scheduled: bool,
) -> Result<()> {
    let config = get_config(config_file)?;

    warn_about_missing_shared_directories(&config, is_scheduled);

    let imported_files =
        get_imported_files_path()
            .ok()
            .and_then(|imported_files_path| {
                if imported_files_path.exists() {
                    read_to_string(imported_files_path).ok()
                } else {
                    None
                }
            });

    match imported_files {
        Some(imported_files) => {
            let mut lines: Vec<&str> = imported_files.trim().lines().collect();

            if !lines.is_empty() {
                lines.sort_unstable();

                println!("{}", lines.join("\n"));
            }
        }

        None => log(
            "failed to get imported files",
            &LogLevel::Error,
            log_file,
            false,
        ),
    }

    Ok(())
}
