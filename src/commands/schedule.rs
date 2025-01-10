use clap::Subcommand;

#[derive(Subcommand, Debug)]
pub enum Schedule {
    /// Enable scheduled imports
    On {
        #[arg(long)]
        frequency: Option<String>,
    },

    /// Disable scheduled imports
    Off,

    /// Show schedule status
    Status,
}

fn on(frequency: Option<&String>) {
    println!("enabled scheduled imports at frequency {frequency:?}.");
}

fn off() {
    println!("disabled scheduled imports.");
}

fn status() {
    println!("showing the status");
}

pub fn schedule(command: Option<&Schedule>) {
    match command {
        Some(Schedule::On { frequency }) => on(frequency.as_ref()),
        Some(Schedule::Off) => off(),
        Some(Schedule::Status) | None => status(),
    }
}
