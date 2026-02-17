use std::path::PathBuf;
use std::str::FromStr;

use anyhow::Result;
use dirs::config_dir;
use figment::{
    providers::{Env, Format, Serialized, Toml},
    Figment,
};
use serde::{Deserialize, Serialize};

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

pub fn get_config(config_file: Option<&PathBuf>) -> Result<Config> {
    let config = Figment::from(Serialized::defaults(Config::default()));

    let config = if let Some(config_file) = config_file {
        config.merge(Toml::file(config_file))
    } else if let Some(config_path) = get_config_path() {
        config.merge(Toml::file(config_path))
    } else {
        config
    };

    Ok(config.merge(Env::prefixed("TSUNDEOKU_")).extract()?)
}
