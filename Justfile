[private]
@default:
    just help

# View full help text, or for a specific recipe
@help *args:
    .environments/scripts/help.nu {{ args }}

# Check flake and run pre-commit hooks
@check *args:
    .environments/scripts/check.nu {{ args }}

# Manage environments
@environment *args:
    .environments/scripts/environment.nu {{ args }}

alias env := environment

# Search available `just` recipes
[no-exit-message]
@find-recipe *args:
    .environments/scripts/find-recipe.nu {{ args }}

alias find := find-recipe

# View project history
@history *args:
    .environments/scripts/history.nu {{ args }}

# View issues
@issue *args:
    .environments/scripts/issue.nu {{ args }}

# View remote repository
@remote *args:
    .environments/scripts/remote.nu  {{ args }}

# Find/replace
@replace *args:
    .environments/scripts/replace.nu  {{ args }}

# View repository analytics
@stats *args:
    .environments/scripts/stats.nu {{ args }}

# List TODO-style comments
@todo *args:
    .environments/scripts/todo.nu {{ args }}

alias todos := todo

# Set helix theme
@theme *args:
    .environments/scripts/theme.nu {{ args }}

# View the source code for a recipe
@view-source *args:
    .environments/scripts/view-source.nu {{ args }}

alias src := view-source

# Create a new release
@release *args:
    ./scripts/release.nu  {{ args }}

[private]
@rs *args:
    just rust {{ args }}

mod rust ".environments/just/rust.just"

alias add := rust::add
alias build := rust::build
alias clean := rust::clean
alias clippy := rust::clippy
alias deps := rust::deps
alias dev := rust::dev
alias install := rust::install
alias remove := rust::remove
alias run := rust::run
alias test := rust::test
alias update := rust::update
