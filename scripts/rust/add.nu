#!/usr/bin/env nu

def main [
  ...dependencies # Dependencies to add
] {
  cargo add ...$dependencies
}
