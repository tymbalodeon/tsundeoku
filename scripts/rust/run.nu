#!/usr/bin/env nu

# Run the application, with any provided <args>.
def --wrapped main [...args: string] {
  if "help" in $args {
    return (help main)
  }

  cargo run -- ...$args
}
