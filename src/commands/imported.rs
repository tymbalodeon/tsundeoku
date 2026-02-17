use std::fs::{read_to_string, File};

use anyhow::{anyhow, Result};

use crate::{get_imported_files_path, log, LogLevel};

pub fn get_imported_files() -> Result<Vec<String>> {
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

    imported_files.map_or_else(
        || Err(anyhow!("failed to read imported files")),
        |imported_files| {
            let mut lines: Vec<String> = imported_files
                .trim()
                .lines()
                .map(std::string::ToString::to_string)
                .collect();

            if !lines.is_empty() {
                lines.sort_unstable();
            }

            Ok(lines)
        },
    )
}

pub fn imported(log_file: Option<&File>) {
    match get_imported_files() {
        Ok(imported_files) => {
            println!("{}", imported_files.join("\n"));
        }

        Err(error) => {
            log(&error.to_string(), &LogLevel::Error, log_file, false);
        }
    }
}
