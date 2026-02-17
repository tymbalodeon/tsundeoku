use std::fs::{read_to_string, File};

use anyhow::Result;
use bat::PrettyPrinter;
use clap::Subcommand;

use crate::{get_log_path, log, LogLevel};

#[derive(Subcommand, Debug)]
pub enum LogCommand {
    /// Clear the logs
    Clear,

    /// Show the logs
    Show,
}

fn print_logs(pretty_printer: &mut PrettyPrinter) -> Result<bool> {
    Ok(pretty_printer.theme("ansi").language("log").print()?)
}

fn filter_logs(logs: &str, imported: bool) -> String {
    if imported {
        logs.lines()
            .filter(|line| line.contains("Imported"))
            .map(std::string::ToString::to_string)
            .collect::<Vec<String>>()
            .join("\n")
    } else {
        logs.to_string()
    }
}

fn clear(log_file: Option<&File>) {
    log_file.map(|log_file| log_file.set_len(0));
}

fn show(log_file: Option<&File>, imported: bool) {
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
                    let logs = filter_logs(logs.trim(), imported);

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

pub fn logs(
    command: Option<&LogCommand>,
    log_file: Option<&File>,
    imported: bool,
) {
    match command {
        Some(LogCommand::Clear) => clear(log_file),
        None | Some(LogCommand::Show) => show(log_file, imported),
    }
}
