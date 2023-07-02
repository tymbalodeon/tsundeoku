@_help:
    just --list

@_get_pyproject_value value:
    printf "$(awk -F '[ =\"]+' '$1 == "{{value}}" { print $2 }' pyproject.toml)"

@_get_command_name:
    just _get_pyproject_value "name"

# Try a command using the current state of the files without building.
try *args:
    #!/usr/bin/env zsh
    command="$(just _get_command_name)"
    pdm run "${command}" {{args}}

pre_commit := "pdm run pre-commit"

# Run pre-commit checks or autoupdate ("autoupdate").
check *autoupdate:
    #!/usr/bin/env zsh
    if [ "{{autoupdate}}" = "autoupdate" ]; then
        {{pre_commit}} autoupdate
    else
        {{pre_commit}} run --all-files
    fi

# Clean Python cache.
clean:
    #!/usr/bin/env zsh
    cached_files=(**/**(cache|__pycache__)(N))
    cached_files+=(.*cache(N))
    if [ -z "${cached_files[*]}" ]; then
        echo "No cached files found."
        exit
    fi
    for file in "${cached_files[@]}"; do
        if [ -d "${file}" ]; then
            rm -rf "${file}"
        else
            rm "${file}"
        fi
        echo "Removed ${file}."
    done

coverage := "pdm run coverage"

# Run coverage report.
@coverage *args: test
    {{coverage}} report -m \
        --omit "*/pdm/*" \
        --skip-covered \
        --sort "cover" \
        {{args}}

# Run tests.
test *args:
    #!/usr/bin/env zsh
    if [ -z "{{args}}" ]; then
        args="tests"
    else
        args="{{args}}"
    fi
    {{coverage}} run -m pytest "${args}"


_get_wheel:
    #!/usr/bin/env zsh
    command="$(just _get_command_name)"
    version="$(just _get_pyproject_value "version")"
    printf "./dist/${command}-${version}-py3-none-any.whl"

# Build the project and install it using pipx, or optionally with pip ("--pip").
build *pip:
    #!/usr/bin/env zsh
    pdm install
    pdm build
    wheel="$(just _get_wheel)"
    if [ "{{pip}}" = "--pip" ]; then
        pip install --user "${wheel}" --force-reinstall
    else
        pipx install "${wheel}" --force --pip-args="--force-reinstall"
    fi

beets_config_values := """
directory: ~/Music
library: ~/.config/beets/library.db
import:
  incremental: yes
  autotag: no
"""

_beets:
    #!/usr/bin/env zsh
    beets_config_folder="$HOME/.config/beets"
    mkdir -p "${beets_config_folder}"
    printf "{{beets_config_values}}" > "${beets_config_folder}/config.yaml"

# Add beets config and build.
setup: _beets build
