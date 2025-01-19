use std::fs::{read_to_string, File};

use crate::{get_imported_files_path, log, LogLevel};

pub fn imported(log_file: &Option<File>) {
    let imported_files = if let Ok(imported_files_path) =
        get_imported_files_path()
    {
        if imported_files_path.exists() {
            if let Ok(imported_files) = read_to_string(imported_files_path) {
                imported_files
            } else {
                log(
                    "failed to get imported files",
                    &LogLevel::Error,
                    log_file,
                    true,
                );

                return;
            }
        } else {
            return;
        }
    } else {
        // TODO dry this up?
        log(
            "failed to get imported files",
            &LogLevel::Error,
            log_file,
            true,
        );

        return;
    };

    let mut lines: Vec<&str> = imported_files.trim().lines().collect();

    lines.sort_unstable();

    println!("{}", lines.join("\n"));
}
