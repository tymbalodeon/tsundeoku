#!/usr/bin/env nu

# Update rust dependencies
def main [
  --breaking # Update to latest SemVer-breaking version
] {
  if $breaking {
    cargo update --breaking -Z unstable-options
  } else {
    cargo update
  }
}
