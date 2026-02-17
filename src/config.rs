use std::path::PathBuf;

use dirs::{config_dir, home_dir};
use figment::{
    providers::{Env, Format, Serialized, Toml},
    Figment,
};
use serde::{Deserialize, Serialize};

#[derive(Deserialize, Serialize)]
pub struct Config {
    pub host: Option<String>,
    pub owner: Option<String>,
    pub root_directory: Option<PathBuf>,
}

impl Default for Config {
    fn default() -> Self {
        let mut username = get_git_config_user("github");

        username =
            username.map_or_else(|| get_git_config_user("gitlab"), Some);

        Self {
            root_directory: home_dir().map(|home_dir| home_dir.join("src")),
            host: Some("github.com".to_string()),
            owner: username,
        }
    }
}

/// # Errors
///
/// Will return `SrcRepoError` if it fails to parse the config file path
pub fn get_config_path() -> Result<String, SrcRepoError> {
    Ok(config_dir()
        .ok_or(SrcRepoError::Config)?
        .join("src/config.toml")
        .to_str()
        .ok_or(SrcRepoError::Config)?
        .to_string())
}

/// # Errors
///
/// Will return `SrcRepoError` if it fails to merge configuration from the file
/// and the environment
pub fn get_config() -> Result<Config, SrcRepoError> {
    Figment::from(Serialized::defaults(Config::default()))
        .merge(Toml::file(get_config_path()?))
        .merge(Env::prefixed("SRC_"))
        .extract()
        .map_or(Err(SrcRepoError::Config), Ok)
}
