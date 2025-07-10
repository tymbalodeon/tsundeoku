#!/usr/bin/env nu

# Run the application, with any provided <args>.
def main [...args: string] {
  cargo run -- ...$args
}
