use std::fs::read_to_string;

use crate::get_imported_files_path;

pub fn get_imported_files() -> Vec<String> {
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

    imported_files.map_or(vec![], |imported_files| {
        let mut lines: Vec<String> = imported_files
            .trim()
            .lines()
            .map(std::string::ToString::to_string)
            .collect();

        if !lines.is_empty() {
            lines.sort_unstable();
        }

        lines
    })
}

pub fn imported() {
    let imported_files = get_imported_files();

    if !imported_files.is_empty() {
        println!("{}", imported_files.join("\n"));
    }
}
