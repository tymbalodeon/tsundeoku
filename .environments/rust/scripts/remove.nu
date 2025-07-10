#!/usr/bin/env nu

def main [
  ...dependencies: string # Dependencies to remove
] {
  for dependency in $dependencies {
      cargo remove $dependency
  }
}
