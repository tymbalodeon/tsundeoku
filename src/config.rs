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

pub fn get_config_path() -> String {
    let message = "failed to determine $XDG_CONFIG_HOME";

    config_dir()
        .expect(message)
        .join("tsundeoku/config.toml")
        .to_str()
        .expect(message)
        .to_string()
}

pub fn get_config() -> Config {
    Figment::from(Serialized::defaults(Config::default()))
        .merge(Toml::file(get_config_path()))
        .merge(Env::prefixed("TSUNDEOKU_"))
        .extract()
        .expect("failed to read configuration")
}
