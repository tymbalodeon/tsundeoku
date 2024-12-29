# View help text
@help *recipe:
    ./scripts/help.nu {{ recipe }}

# Check flake and run pre-commit hooks
@check *args:
    ./scripts/check.nu {{ args }}

# List dependencies (alias: `deps`)
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

mod python "just/python.just"

# alias for `python add`
@add *args:
    just python add {{ args }}

# alias for `python profile`
@profile *args:
    just python profile {{ args }}

# alias for `python shell`
@shell *args:
    just python shell {{ args }}

mod rust "just/rust.just"

# alias for `rust clean`
@clean *args:
    just rust clean {{ args }}

# alias for `rust clippy`
@clippy *args:
    just rust clippy {{ args }}

# alias for `rust dev`
@dev *args:
    just rust dev {{ args }}

# alias for `rust install`
@install *args:
    just rust install {{ args }}
