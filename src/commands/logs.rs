use std::fs::{read_to_string, File};

use anyhow::Result;
use bat::PrettyPrinter;

use crate::{
    get_log_path, log, warn_about_missing_shared_directories, LogLevel,
};

use super::config::ConfigFile;

fn print_logs(pretty_printer: &mut PrettyPrinter) -> Result<bool> {
    Ok(pretty_printer.theme("ansi").language("log").print()?)
}

pub fn logs(config_values: &ConfigFile, log_file: Option<&File>) {
    warn_about_missing_shared_directories(config_values);

    get_log_path().map_or_else(
        |error| log(&error.to_string(), &LogLevel::Error, log_file, false),
        |log_path| {
            read_to_string(&log_path).map_or_else(
                |_| {
                    log(
                        &format!("failed to read {}", log_path.display()),
                        &LogLevel::Error,
                        log_file,
                        true,
                    );
                },
                |logs| {
                    let logs = logs.trim();

                    if !logs.is_empty() {
                        let mut pretty_printer = PrettyPrinter::new();

                        pretty_printer.input_from_bytes(logs.as_bytes());

                        if print_logs(&mut pretty_printer).is_err() {
                            log(
                                "failed to print logs",
                                &LogLevel::Error,
                                log_file,
                                false,
                            );
                        }
                    }
                },
            );
        },
    );
}
