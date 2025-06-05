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
@find-recipe *search_term:
    ./scripts/find-recipe.nu {{ search_term }}

alias find := find-recipe

# View project history
@history *args:
    ./scripts/history.nu {{ args }}

# View issues
@issue *args:
    ./scripts/issue.nu {{ args }}

# Create a new release
@release *preview:
    ./scripts/release.nu  {{ preview }}

# View remote repository
@remote *web:
    ./scripts/remote.nu  {{ web }}

# Find/replace
@replace *help:
    ./scripts/replace.nu  {{ help }}

# View repository analytics
@stats *help:
    ./scripts/stats.nu {{ help }}

# List TODO-style comments
@todo *args:
    ./scripts/todo.nu {{ args }}

alias todos := todo

# View the source code for a recipe
@view-source *recipe:
    ./scripts/view-source.nu {{ recipe }}

alias src := view-source

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
