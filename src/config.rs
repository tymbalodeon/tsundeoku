use std::path::{Path, PathBuf};
use std::str::FromStr;

use anyhow::Result;
use dirs::config_dir;
use figment::{
    providers::{Env, Format, Serialized, Toml},
    Figment,
};
use serde::{Deserialize, Serialize};
use shellexpand::tilde;

use crate::log;

#[derive(Debug, Deserialize, Serialize)]
pub struct Config {
    pub shared_directories: Vec<PathBuf>,
    pub ignored_paths: Vec<PathBuf>,
    pub local_directory: Option<PathBuf>,
    pub schedule_interval: Option<cron::Schedule>,
}

impl Default for Config {
    fn default() -> Self {
        Self {
            shared_directories: vec![],
            ignored_paths: vec![],
            local_directory: None,
            schedule_interval: cron::Schedule::from_str("0 0 * * * *").ok(),
        }
    }
}

impl Config {
    pub fn to_toml(&self) -> Result<String> {
        Ok(toml::to_string(&self)?)
    }
}

pub fn get_config_path() -> Option<String> {
    config_dir().and_then(|config_dir| {
        config_dir
            .join("tsundeoku/config.toml")
            .to_str()
            .map(std::string::ToString::to_string)
    })
}

fn tilde_expand_path(path: &Path) -> PathBuf {
    PathBuf::from(tilde(&path.to_string_lossy()).to_string())
}
fn tilde_expand_paths(paths: &[PathBuf]) -> Vec<PathBuf> {
    paths
        .iter()
        .map(|path| tilde_expand_path(path))
        .collect::<Vec<PathBuf>>()
}

pub fn get_config(config_file: Option<&PathBuf>) -> Result<Config> {
    let config = Figment::from(Serialized::defaults(Config::default()));

    let config = if let Some(config_file) = config_file {
        config.merge(Toml::file(config_file))
    } else if let Some(config_path) = get_config_path() {
        config.merge(Toml::file(config_path))
    } else {
        config
    };

    let mut config: Config =
        config.merge(Env::prefixed("TSUNDEOKU_")).extract()?;

    for path in &config.ignored_paths {
        if !path.exists() {
            log(
                &format!(
                    "{:?} has been removed from the shared folder",
                    path.to_string_lossy()
                ),
                &crate::LogLevel::Warning,
                None,
                false,
            );
        }
    }

    config.shared_directories = tilde_expand_paths(&config.shared_directories);
    config.ignored_paths = tilde_expand_paths(&config.ignored_paths);

    config.local_directory =
        config.local_directory.map(|path| tilde_expand_path(&path));

    Ok(config)
}
