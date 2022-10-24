command := `awk -F '[ ="]+' '$1 == "name" { print $2 }' pyproject.toml`
version := `awk -F '[ ="]+' '$1 == "version" { print $2 }' pyproject.toml`
wheel := "./dist/" + command + "-" + version + "-py3-none-any.whl"
beets_config_values := """
directory: ~/Music
library: ~/.config/beets/library.db
import:
  incremental: yes
  autotag: no
"""

@_help:
    just --list

_beets:
    #!/usr/bin/env zsh
    beets_config_folder=$HOME/.config/beets
    mkdir -p $beets_config_folder
    echo "{{beets_config_values}}" > $beets_config_folder/config.yaml

# try a command using the current state of the files without building.
@try *args:
    poetry run {{command}} {{args}}

# run pre-commit checks.
@check:
    poetry run pre-commit run -a

# run tests.
@test *args:
    poetry run coverage run -m pytest {{args}}

# run coverage report.
@coverage *args:
    poetry run coverage report -m --skip-covered --sort=cover {{args}}

# build the project and pipx install it.
@build:
    poetry install
    poetry build
    pipx install {{wheel}} --force --pip-args='--force-reinstall'

# Add beets config and build.
@start: _beets build
