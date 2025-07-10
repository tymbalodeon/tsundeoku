[private]
@default:
    just help

# View full help text, or for a specific recipe
@help *args:
    .environments/generic/scripts/help.nu {{ args }}

# Check flake and run pre-commit hooks
@check *args:
    .environments/generic/scripts/check.nu {{ args }}

# Manage environments
@environment *args:
    .environments/generic/scripts/environment.nu {{ args }}

alias env := environment

# Search available `just` recipes
[no-exit-message]
@find-recipe *args:
    .environments/generic/scripts/find-recipe.nu {{ args }}

alias find := find-recipe

# View project history
@history *args:
    .environments/generic/scripts/history.nu {{ args }}

# View issues
@issue *args:
    .environments/generic/scripts/issue.nu {{ args }}

# View remote repository
@remote *args:
    .environments/generic/scripts/remote.nu  {{ args }}

# Find/replace
@replace *args:
    .environments/generic/scripts/replace.nu  {{ args }}

# View repository analytics
@stats *args:
    .environments/generic/scripts/stats.nu {{ args }}

# List TODO-style comments
@todo *args:
    .environments/generic/scripts/todo.nu {{ args }}

alias todos := todo

# Set helix theme
@theme *args:
    .environments/generic/scripts/theme.nu {{ args }}

# View the source code for a recipe
@view-source *args:
    .environments/generic/scripts/view-source.nu {{ args }}

alias src := view-source

# Create a new release
@release *args:
    .environments/git/scripts/release.nu  {{ args }}

[private]
@rs *args:
    just rust {{ args }}

mod rust ".environments/rust/Justfile"

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
