#!/usr/bin/env nu

def main [
  --release # Build in release mode, with optimizations
] {
  if $release {
    cargo build --release
  } else {
    cargo build
  }
}
