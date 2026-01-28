#!/usr/bin/env nu

# Run the application, with any provided <args>.
def --wrapped main [...args: string] {
  cargo run -- ...$args
}
