[private]
@default:
    just help --default

# View full help text, or for a specific recipe
@help *args:
    ./scripts/help.nu {{ args }}

# Check flake and run pre-commit hooks
@check *args:
    ./scripts/check.nu {{ args }}

# List dependencies
@dependencies *args:
    ./scripts/dependencies.nu {{ args }}

alias deps := dependencies

# Manage environments
@environment *args:
    ./scripts/environment.nu {{ args }}

alias env := environment

# Search available `just` recipes
[no-cd]
[no-exit-message]
@find-recipe *search_term:
    ./scripts/find-recipe.nu {{ search_term }}

alias find := find-recipe

# View project history
[no-cd]
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

# View repository analytics
@stats *help:
    ./scripts/stats.nu {{ help }}

# Run tests
@test *args:
    ./scripts/test.nu {{ args }}

# View the source code for a recipe
[no-cd]
@view-source *recipe:
    ./scripts/view-source.nu {{ recipe }}

alias src := view-source

mod rust "just/rust.just"

# alias for `rust add`
[group("aliases")]
@add *args:
    just rust add {{ args }}

# alias for `rust build`
[group("aliases")]
@build *args:
    just rust build {{ args }}

# alias for `rust clean`
[group("aliases")]
@clean *args:
    just rust clean {{ args }}

# alias for `rust clippy`
[group("aliases")]
@clippy *args:
    just rust clippy {{ args }}

# alias for `rust dev`
[group("aliases")]
@dev *args:
    just rust dev {{ args }}

# alias for `rust install`
[group("aliases")]
@install *args:
    just rust install {{ args }}

# alias for `rust remove`
[group("aliases")]
@remove *args:
    just rust remove {{ args }}

# alias for `rust run`
[group("aliases")]
@run *args:
    just rust run {{ args }}

# alias for `rust update`
[group("aliases")]
@update *args:
    just rust update {{ args }}
