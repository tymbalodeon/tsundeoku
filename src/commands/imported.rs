use std::fs::{read_to_string, File};

use crate::{
    commands::config::ConfigFile, get_imported_files_path, log,
    warn_about_missing_shared_directories, LogLevel,
};

pub fn imported(config_values: &ConfigFile, log_file: Option<&File>) {
    warn_about_missing_shared_directories(config_values);

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

            lines.sort_unstable();

            println!("{}", lines.join("\n"));
        }

        None => log(
            "failed to get imported files",
            &LogLevel::Error,
            log_file,
            false,
        ),
    }
}
