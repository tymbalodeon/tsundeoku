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
    beets_config_folder="$HOME/.config/beets"
    mkdir -p "${beets_config_folder}"
    printf "{{beets_config_values}}" > "${beets_config_folder}/config.yaml"

@_get_pyproject_value value:
    printf $(awk -F '[ =\"]+' '$1 == "{{value}}" { print $2 }' pyproject.toml)

# Try a command using the current state of the files without building.
try *args:
    #!/usr/bin/env zsh
    command=$(just _get_pyproject_value "name")
    poetry run "${command}" {{args}}

pre_commit := "poetry run pre-commit"

# Run pre-commit checks or autoupdate ("--autoupdate").
check *autoupdate:
    #!/usr/bin/env zsh
    if [ "{{autoupdate}}" = "--autoupdate" ]; then
        {{pre_commit}} autoupdate
    else
        {{pre_commit}} run --all-files
    fi

# Clean Python cache.
clean:
    #!/usr/bin/env zsh
    cached_files=(**/**.pyc(N))
    if [ -z "${cached_files[*]}" ]; then
        echo "No cached files found."
        exit
    fi
    for file in "${cached_files[@]}"; do
        rm "${file}"
        echo "Removed ${file}."
    done

# Run tests.
@test *args:
    poetry run coverage run -m pytest {{args}}

# Run coverage report.
@coverage *args:
    poetry run coverage report -m --skip-covered --sort=cover {{args}}

_get_wheel:
    #!/usr/bin/env zsh
    command=$(just _get_pyproject_value "name")
    version=$(just _get_pyproject_value "version")
    printf "./dist/${command}-${version}-py3-none-any.whl"

# Build the project and install it, optionally using pipx ("--pipx").
build *pipx:
    #!/usr/bin/env zsh
    poetry install
    poetry build
    wheel="$(just _get_wheel)"
    if [ "{{pipx}}" = "--pipx" ]; then
        pipx install "${wheel}" --force --pip-args="--force-reinstall"
    else
        pip install --user "${wheel}" --force-reinstall
    fi

# Add beets config and build.
start: _beets build
