#!/usr/bin/env nu

use ../environment.nu get-project-root

def main [] {
  cargo install --path (get-project-root)
}
