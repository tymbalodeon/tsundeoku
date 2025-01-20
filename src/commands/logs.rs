use std::fs::{read_to_string, File};

use crate::{
    get_log_path, log, warn_about_missing_shared_directories, LogLevel,
};

use super::config::ConfigFile;

fn log_error(log_file: Option<&File>) {
    log("failed to read logs", &LogLevel::Error, log_file, true);
}

pub fn logs(config_values: &ConfigFile, log_file: Option<&File>) {
    warn_about_missing_shared_directories(config_values);

    get_log_path().map_or_else(
        |_| log_error(log_file),
        |log_path| {
            read_to_string(log_path).map_or_else(
                |_| log_error(log_file),
                |logs| {
                    let logs = logs.trim();

                    if !logs.is_empty() {
                        println!("{logs}");
                    }
                },
            );
        },
    );
}
