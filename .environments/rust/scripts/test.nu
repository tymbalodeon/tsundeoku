#!/usr/bin/env nu

# Run the tests
def --wrapped main [...args: string] {
  cargo test ...$args
}
