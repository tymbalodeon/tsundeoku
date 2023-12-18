set shell := ["nu", "-c"]

_help:
    #!/usr/bin/env nu

    (
        just --list
            --color always
            --list-heading (
                [
                    "Available recipes:"
                    "(run `<recipe> --help/-h` for more info)\n"
                ]
                | str join " "
            )
    )

alias source := src
# Display the source code for a recipe
src recipe *args="_":
    #!/usr/bin/env nu

    # Display the source code for a recipe. If no args are provided, display
    # the raw `just` code, otherwise display the code with the args provided
    # to `just` applied. Pass `""` as args to see the code when no args are
    # provided to a recipe.
    def src [
        recipe: string # The recipe command
        ...args: string # Arguments to the recipe
    ] {
        if "_" in $args {
            just --show $recipe
        } else {
            just --dry-run $recipe $args
        }
    }

    src {{ recipe }} `{{ args }}`

# Search available `just` commands
[no-exit-message]
search *regex:
    #!/usr/bin/env nu

    # Search available `just` commands, interactively, or by regex
    def search [
        regex?: string # Regex pattern to match
    ] {
        if ($regex | is-empty) {
            just --list | fzf
        } else {
            just | grep --color=always --extended-regexp $regex
        }
    }

    search {{ regex }}

# Manage project Python version
python *args:
    #!/usr/bin/env nu

    # Manage project Python version
    def python [
        --installed # Show installed Python versions
        --latest # Show the latest available Python version
        --path # Show the path of the current Python
        --use: string # Specify a new Python version to use
        --version # (default) Show the current Python version
    ] {
        if $latest {
            rtx latest python
            exit
        } else if $installed {
            rtx list python
            exit
        } else if $path {
            rtx which python
            exit
        } else if $version or ($use | is-empty) {
            ^python -V
            exit
        }

        let version = if $use == "latest" {
            (rtx latest python)
        } else {
            $use
        }

        if $version in ((^python -V) | split row " "  | last)  {
            exit
        }

        rtx local $"python@($version)"
        pdm venv create --force (rtx where $"python@($version)")
        just install --minimal
    }

    python {{ args }}

get-pyproject-value := "open pyproject.toml | get project."
application-command := "(" + get-pyproject-value + "name)"

[no-exit-message]
_install_and_run *command:
    #!/usr/bin/env nu

    let command = (
        echo `{{ command }}`
        | split row --regex "sudo pdm run |pdm run "
        | last
        | split words
        | filter { |arg| $arg != "pdm" }
        | first
    )

    if not ($command in (pdm list --fields name --csv)) {
        if $command == {{ application-command }} {
            just install --prod
        } else {
            just install
        }
    }

    {{ command }}

# Add dependencies
add *args:
    #!/usr/bin/env nu

    # Add dependencies
    def add [
        ...dependencies: string,
        --dev # Add dependencies to the development group
    ]: {
        if $dev {
            pdm add --dev $dependencies
        } else {
            pdm add $dependencies
        }
    }

    add {{ args }}

use-list-dependencies := """
    def list-dependencies [
        --dev
        --prod
        --include-version
    ] {
        let export = if $dev {
            pdm export --pyproject --no-default
        } else if $prod {
            pdm export --pyproject --prod
        } else {
            pdm export --pyproject
        }

        mut dependencies = $export
            | lines
            | filter {
                |line|

                (
                    (not ($line | is-empty))
                    and (not ($line | str starts-with "#"))
                )
            }

        if not $include_version {
            $dependencies = (
                $dependencies
                | each {
                    |dependency|

                    $dependency | split row ">=" | first
                }
            )
        }

        $dependencies | str join "\n"
    }
"""

# Remove dependencies
remove *args:
    #!/usr/bin/env nu

    {{ use-list-dependencies }}

    def is-a-dependency [
        dependency: string
        --dev
    ] {
        let dependencies = if $dev {
            list-dependencies --dev
        } else {
            list-dependencies
        }

        $dependency in $dependencies
    }

    # Remove dependencies
    def remove [...dependencies: string] {
        for $dependency in [$dependencies] {
            if (is-a-dependency $dependency --dev) {
                pdm remove --dev $dependency
            } else if (is-a-dependency $dependency) {
                pdm remove $dependency
            }
        }
    }

    remove {{ args }}

_get-application-version:
    #!/usr/bin/env nu

    open agni/__init__.py
    | split row " "
    | last
    | str replace --all '"' ""

# Install dependencies
install *args:
    #!/usr/bin/env nu

    def not-installed [command: string] {
        (command -v $command | is-empty)
    }

    def module-not-installed [command: string] {
        (
            pdm run python -m $command --help err> /dev/null
            | complete
            | get exit_code
            | into bool
        )
    }

    # Install dependencies
    def install [
        --app # (Build and) install the application
        --dry-run # Display dependencies without installing
        --minimal # Install only dependencies necessary for other commands
        --prod # Install production dependencies only
    ] {
        if $dry_run {
            if $app or $prod {
                just dependencies --prod
            } else {
                just dependencies
            }

            exit
        }

        if (not $minimal) and (not $app) {
            mut brewfiles = ["Brewfile.prod"]

            if not $prod {
                $brewfiles = ($brewfiles | append "Brewfile.dev")
            }

            for file in $brewfiles {
                brew bundle --no-upgrade --file $file
            }
        }

        if (
            rtx outdated --log-level error
            | complete
            | get exit_code
            | into bool
        ) {
            rtx install
        }

        if not $prod {
            if (module-not-installed pip) {
                pdm run python -m ensurepip --upgrade --default-pip
            }

            if (module-not-installed pipx) {
                pdm run python -m pip install --upgrade pip pipx;
                pdm run python -m pipx ensurepath
            }

            if (not-installed speedscope) { pnpm add --global speedscope }

            if (not-installed cargo) {
                curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
            }

            if (not-installed cargo) { cargo install checkexec }
        }

        if $minimal {
            just _install_and_run pdm run pre-commit install out+err> /dev/null
        } else {
            if $app or $prod {
                pdm install --prod
            } else {
                pdm install
                just _install_and_run pdm run pre-commit install
            }
        }

        if $app {
            just build
            let application_version = (just _get-application-version)

            (
                pdm run python -m pipx install
                    $"./dist/{{ application-command }}-($application_version)-py3-none-any.whl"
                    --force
                    --pip-args="--force-reinstall"
            )
        }
    }

    install {{ args }}

# Update dependencies
update *args:
    #!/usr/bin/env nu

    # Update dependencies
    def update [
        --prod # Update production dependencies
    ] {
        if $prod {
            just install --minimal --prod
        } else {
            just install --minimal
        }

        mut brewfiles = ["Brewfile.prod"]

        if not $prod {
            $brewfiles = ($brewfiles | append "Brewfile.dev")
        }

        for file in $brewfiles {
            brew bundle --file $file
        }

        rtx upgrade

        if not $prod {
            pdm run python -m pip install --upgrade pip pipx
            pnpm update --global speedscope
            rustup update
            cargo install-update checkexec
        }

        if $prod {
            pdm update --prod
        } else {
            pdm update
        }

        just pre-commit --update
    }

    update {{ args }}

# Show application dependencies
dependencies *args:
    #!/usr/bin/env nu

    {{ use-list-dependencies }}

    def indent [text: string] {
        $text
        | lines
        | each { |line| $"\t($line)" }
        | str join "\n"
    }

    def get-brew-dependencies [--dev] {
        let brewfile = if $dev {
            "Brewfile.dev"
        } else {
            "Brewfile.prod"
        }

        mut dependencies = indent (
            brew bundle list --file $brewfile
            | lines
            | str join "\n"
        )

        if not $dev {
            $dependencies = "Production build:\n" + $dependencies
        }

        $dependencies
    }

    # Show application dependencies
    def show-dependencies [
        --dev # Show only development dependencies
        --prod # Show only production dependencies
        --installed # Show installed dependencies
        --tree # Show installed dependencies as a tree
    ] {
        if $tree {
            pdm list --tree
        } else if $installed {
            (
                pdm list
                    --fields name,version
                    --sort name
            )
        } else {
            let dependencies = if $dev {
                list-dependencies --include-version --dev
            } else if $prod {
                (
                    (list-dependencies --include-version --prod)
                    + "\n\n"
                    + (get-brew-dependencies)
                )
            } else {
                let prod_dependencies = (
                    indent (list-dependencies --include-version --prod)
                )

                let dev_dependencies = (
                    indent (list-dependencies --include-version --dev)
                )

                let brew_prod_dependencies = (
                    get-brew-dependencies
                )

                let brew_dev_dependencies = (
                    get-brew-dependencies --dev
                )

                [
                    Production:
                    $prod_dependencies
                    ""
                    $brew_prod_dependencies
                    ""
                    Development:
                    $dev_dependencies
                    $brew_dev_dependencies
                ]
                | str join "\n"
            }

            if (command -v bat | is-empty) {
                just install
            }

            let bat_command = (
                "bat --language pip --plain --theme gruvbox-dark"
            )
            zsh -c $"echo \"($dependencies)\" | ($bat_command)"
        }
    }

    show-dependencies {{ args }}

# Type-check
[no-exit-message]
type-check *args:
    #!/usr/bin/env nu

    # Type-check
    def type-check [
        ...files: string # Files to check
    ] {
        just _install_and_run pdm run pyright $files
    }

    type-check {{ args }}

# Lint and apply fixes
lint *args:
    #!/usr/bin/env nu

    def lint [] {
        just _install_and_run pdm run ruff check --fix
    }

    lint {{ args }}

alias format := fmt
# Format
fmt *args:
    #!/usr/bin/env nu

    # Format
    def fmt [] {
        just --unstable --fmt
        just _install_and_run pdm run ruff format
    }

    fmt {{ args }}

# Run pre-commit hooks
pre-commit *args:
    #!/usr/bin/env nu

    # Run pre-commit hook by name, all hooks, or update all hooks
    def pre-commit [
        hook?: string # The hook to run
        --hooks # Display all hook ids
        --update # Update all pre-commit hooks
    ] {
        if $hooks {
            echo (
                grep id .pre-commit-config.yaml
                | str replace --all --regex "- +id:" ""
                | lines
                | each { |line| ($line | str trim) }
                | sort
                | str join "\n"
            )

            exit
        }

        if $update {
            just _install_and_run pdm run pre-commit autoupdate
            exit
        }

        if not ($hook | is-empty) {
            just _install_and_run pdm run pre-commit run $hook --all-files
        } else {
            just _install_and_run pdm run pre-commit run --all-files
        }
    }

    pre-commit {{ args }}

# Open an interactive python shell
shell *args:
    #!/usr/bin/env nu

    # Open an interactive python shell
    def shell [] {
        just _install_and_run pdm run bpython
    }

    shell {{ args }}

# Run the application
run *args:
    #!/usr/bin/env nu

    let args = (
        ["{{ args }}"]
        | split row " "
        | each { |arg| $"\"($arg)\"" }
        | str join " "
    )

    if $args == '""' {
        just _install_and_run pdm run {{ application-command }}
    } else {
        just _install_and_run pdm run {{ application-command }} $"`($args)`"
    }

# Profile a command and view results
profile *args:
    #!/usr/bin/env nu

    # Profile a command and view results
    def profile [
        ...args: string # Arguments to the command being profiled
    ] {
        just install --minimal

        let output_directory = "profiles"
        mkdir $output_directory

        let output_file = $"($output_directory)/profile.json"

        (
            just _install_and_run sudo pdm run py-spy record
                --format speedscope
                --output $output_file
                --subprocesses
                -- pdm run python -m {{ application-command }} $args
        )

        speedscope $output_file
    }

    profile {{ args }}

# Run coverage report
coverage *args:
    #!/usr/bin/env nu

    # Run coverage report
    def coverage [
        --fail-under: string # Fail if coverage is less than this percentage
    ] {
        just test out+err> /dev/null

        if not ($fail_under | is-empty) {
            (
                just _install_and_run pdm run coverage report -m
                    --skip-covered
                    --sort "cover"
                    --fail-under $fail_under
            )
        } else {
            (
                just _install_and_run pdm run coverage report -m
                    --skip-covered
                    --sort "cover"
            )
        }
    }

    coverage {{ args }}

# Run tests
test *args:
    #!/usr/bin/env nu

    # Run tests
    def test [] {
        just _install_and_run pdm run coverage run -m pytest tests
    }

    test {{ args }}

# Build and install the application
build *args:
    #!/usr/bin/env nu

    # Build and install the application
    def build [] {
        pdm build
    }

    build {{ args }}

generated_files := """
[
    [Option "Files to clean"];
    [<default> "<all EXCEPT dist and venv>"]
    [--all <all>]
    [coverage .coverage]
    [dist dist/]
    [ds-store **/.DS_Store]
    [pdfs **/*.pdf]
    [profiles profiles]
    [pycache **/__pycache__]
    [pytest .pytest_cache]
    [ruff .ruff_cache]
    [venv .venv]
]
"""

# Clean generated files
clean *args:
    #!/usr/bin/env nu

    # Remove generated files
    def clean [
        --choices, # Display possible values for ...(files)
        --all (-a), # Clean all files
        ...files: string # Which files to clean (see --choices for available files)
    ] {
        if ($choices) {
            echo {{ generated_files }}
            exit
        }

        let default_files_to_clean = [
            coverage
            ds-store
            pdfs
            profiles
            pycache
            pytest
            ruff
        ]

        let files_to_clean = if $all {
            $default_files_to_clean | append [dist venv] | sort
        } else if ($files | is-empty) {
            $default_files_to_clean
        } else {
            $files
        }

        for file in $files_to_clean {
            let files_list = (
                {{ generated_files }}
                | where Option == $file
                | get "Files to clean"
            )

            if ($files_list | is-empty) {
                echo $"Unknown option: \"($file)\""
                continue
            }

            if $file == "venv" and (
                not (command -v pdm | is-empty)) and (
                not (pdm run command -v pre-commit | is-empty)
            ) {
                echo "Uninstalling pre-commit..."
                pdm run pre-commit uninstall
            }

            let files = $files_list | first

            echo $"Removing generated ($file) files..."
            rm --recursive --force $files
        }
    }

    clean {{ args }}

# Release a new version of the application
release *target:
    #!/usr/bin/env nu

    # Release a new version of the application
    def release [
        target = "patch" # Type of release to target (major, minor, or patch)
    ] {
        let current_version = just _get-application-version | split row "."

        mut major = ($current_version.0 | into int)
        mut minor = ($current_version.1 | into int)
        mut patch = ($current_version.2 | into int)

        if $target in [major minor patch] {
            if $target == "major" {
                $major += 1
                $minor = 0
                $patch = 0
            } else if $target == "minor" {
                $minor += 1
                $patch = 0
            } else if $target == "patch" {
               $patch += 1
            }

            let new_version = ([$major $minor $patch] | str join ".")
            $"($current_version | str join ".") --> ($new_version)"
        } else {
            just release --help
        }
    }

    release {{ target }}


# Open the repository page in the browser
@repo:
    gh browse

# List repository issues
@issues:
    gh issue list

# Create issue interactively or view issue by <id>
issue *args:
    #!/usr/bin/env nu

    # Create issue interactively or view issue by <id>
    def issue [
        id?: string # The ID of the issue to view
        --web # View the issue in the browser
    ] {
        if $id == null {
            gh issue create
        } else if $web {
            gh issue view $id --web
        } else {
            gh issue view $id
        }
    }

    issue {{ args }}

# Show project statistics
stats *args:
    #!/usr/bin/env nu

    # Show project statistics
    def stats [
        --code # Show stats about the project code
        --git # Show stats related to git activity
    ] {
        let default = not ([$code $git] | any { |arg| $arg })

        if $default or $git {
            onefetch
        }

        if $default or $code {
            tokei --sort code
        }
    }

    stats {{ args }}

beets_config_values := """
directory: ~/Music
library: ~/.config/beets/library.db
import:
  incremental: yes
  autotag: no
"""

_beets:
    #!/usr/bin/env nu

    let beets_config_folder = $"($env.HOME)/.config/beets"
    mkdir $beets_config_folder
    echo "{{beets_config_values}}" | save --raw $"($beets_config_folder)/config.yaml"

# Add beets config and build
setup: _beets build
