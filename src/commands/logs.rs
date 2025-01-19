use std::fs::{read_to_string, File};

use crate::{get_log_path, log, LogLevel};

pub fn logs(log_file: Option<&File>) {
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
