use std::fs::{read_to_string, File};

use crate::{
    get_log_path, log, warn_about_missing_shared_directories, LogLevel,
};

use super::config::ConfigFile;

pub fn logs(config_values: &ConfigFile, log_file: Option<&File>) {
    warn_about_missing_shared_directories(config_values);

    if let Ok(log_path) = get_log_path() {
        if let Ok(logs) = read_to_string(log_path) {
            println!("{}", logs.trim());
        } else {
            log("failed to read logs", &LogLevel::Error, log_file, true);
        }
    } else {
        // TODO dry this up?
        log("failed to read logs", &LogLevel::Error, log_file, true);
    }
}
