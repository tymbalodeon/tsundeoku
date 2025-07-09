#!/usr/bin/env nu

use ../environment.nu get-project-path
use ../help.nu display-just-help

# View help text
def main [
  recipe?: string # View help text for recipe
  ...subcommands: string  # View help for a recipe subcommand
  --color = "always" # When to use colored output
] {
  let environment = "rust"

  (
    display-just-help
      $recipe
      $subcommands
      --color $color
      --environment $environment
      --justfile (get-project-path $"just/($environment).just")
  )
}
