#!/usr/bin/env nu

# Run the tests
def main [package?: string] {
  if ($package | is-empty) {
    cargo test
  } else {
    cargo test --package $package
  }
}
