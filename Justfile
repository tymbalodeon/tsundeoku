[private]
@default:
    just help --default

# View full help text, or for a specific recipe
@help *args:
    ./scripts/help.nu {{ args }}

# Check flake and run pre-commit hooks
@check *args:
    ./scripts/check.nu {{ args }}

# Manage environments
@environment *args:
    ./scripts/environment.nu {{ args }}

alias env := environment

# Search available `just` recipes
[no-exit-message]
@find-recipe *args:
    ./scripts/find-recipe.nu {{ args }}

alias find := find-recipe

# View project history
@history *args:
    ./scripts/history.nu {{ args }}

# View issues
@issue *args:
    ./scripts/issue.nu {{ args }}

# View remote repository
@remote *args:
    ./scripts/remote.nu  {{ args }}

# Find/replace
@replace *args:
    ./scripts/replace.nu  {{ args }}

# View repository analytics
@stats *args:
    ./scripts/stats.nu {{ args }}

# List TODO-style comments
@todo *args:
    ./scripts/todo.nu {{ args }}

alias todos := todo

# View the source code for a recipe
@view-source *args:
    ./scripts/view-source.nu {{ args }}

alias src := view-source

# Create a new release
@release *args:
    ./scripts/release.nu  {{ args }}

mod rust "just/rust.just"

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
