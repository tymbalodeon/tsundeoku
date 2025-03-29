#!/usr/bin/env nu

export def display-message [
  action: string
  message: string
  --color-entire-message
  --color: string
] {
  let color = if ($color | is-not-empty) {
    $color
  } else match $color_entire_message {
    true => (
      match $action {
        "Added" =>  "light_green_bold"
        "Removed" => "light_yellow_bold"
        "Skipped" => "light_gray_bold"
        "Upgraded" =>  "light_cyan_bold"
        _ => "white"
      }
    )

    false => (
      match $action {
        "Added" =>  "green_bold"
        "Removed" => "yellow_bold"
        "Skipped" => "light_gray_dimmed"
        "Upgraded" =>  "cyan_bold"
        _ => "white"
      }
    )
  }

  mut action = $action

  while (($action | split chars | length) < 8) {
    $action = $" ($action)"
  }

  let message = if $color_entire_message {
    $"(ansi $color)($action) ($message)(ansi reset)"
  } else {
    $"(ansi $color)($action)(ansi reset) ($message)"
  }

  print $"  ($message)"
}

export def get-project-root [] {
  echo (git rev-parse --show-toplevel)
}

export def get-project-path [path: string] {
  get-project-root
  | path join $path
}

# Activate installed environments
def "main activate" [] {
  if (which direnv | is-empty) {
    print "Direnv (https://direnv.net/) is not installed."
    print "Please install and try again."

    exit 1
  }

  "use flake"
  | save --force (get-project-path .envrc)

  direnv allow
}

# Add environments to the project
export def "main add" [...environments: string] {
  if not (".environments.toml" | path exists) {
    {environments: []}
    | to toml
    | save .environments.toml
  }

  open .environments.toml
  | update environments (
      (open .environments.toml).environments
      | append $environments
      | uniq
      | sort
    )
  | save --force .environments.toml

  main activate
}

# List environments and files
def "main list" [
  environment?: string
  path?: string
] {
  if ($environment | is-empty) {
    ls --short-names $env.ENVIRONMENTS
    | where type == dir
    | get name
    | str join "\n"
  } else if ($path | is-empty) {
    fd --type file "" $"($env.ENVIRONMENTS)/($environment)"
    | lines
    | each {|file| $file | split row $"src/($environment)/" | last}
    | str join "\n"
  } else {
    ls --short-names $"($env.ENVIRONMENTS)/($environment)/($path)"
    | get name
    | str join "\n"
  }
}

# List installed environments
def "main list installed" [] {
  # TODO: show local environments
  (open .environments.toml).environments
  | str join "\n"
}

# Remove environments from the project
def "main remove" [
  ...environments: string
  --reactivate
] {
  if not (".environments.toml" | path exists) {
    {environments: []}
    | to toml
    | save .environments.toml
  }

  open .environments.toml
  | update environments (
      (open .environments.toml).environments
      | where {$in not-in $environments}
    )
  | save --force .environments.toml

  main activate
}

# View the contents of a remote environment file
def "main source" [
  environment: string
  file: string
] {
  # TODO: make env and file optional and use fzf in those cases
  let files = (^fd $file $"($env.ENVIRONMENTS)/($environment)")

  if ($files | is-empty) {
    return
  }

  let file = if ($files | lines | length) > 1 {
    $files
    | fzf
  } else {
    $files
  }

  bat $file
}

alias "main src" = main source

# Run tests
def "main test" [
  --suites: string # Regular expression to match against suite names (defaults to all)
  --tests: string # Regular expression to match against test names (defaults to all)
] {
  let command = "use nutest; nutest run-tests"

  let command = if ($suites | is-not-empty) {
    $"($command) --match-suites ($suites)"
  } else {
    $command
  }

  let command = if ($tests | is-not-empty) {
    $"($command) --match-suites ($tests)"
  } else {
    $command
  }

  nu --commands $command --include-path $env.NUTEST
}

# Update environment dependencies
def "main update" [] {
  nix flake update
}

def main [] {
  main list installed
}
