set working-directory := ".."

# View help text
@help *args:
    ./scripts/rust/help.nu {{ args }}

# Add dependencies
@add *args:
    ./scripts/rust/add.nu {{ args }}

# Build the application
@build *args:
    ./scripts/rust/build.nu {{ args }}

# Remove generated files
@clean *args:
    ./scripts/rust/clean.nu {{ args }}

# Run clippy
@clippy *args:
    ./scripts/rust/clippy.nu {{ args }}

# Show application dependencies
@deps *args:
    ./scripts/rust/deps.nu {{ args }}

# Open a pre-configured development environment
@dev *args:
    ./scripts/rust/dev.nu {{ args }}

# Install the application
@install *args:
    ./scripts/rust/install.nu {{ args }}

# Remove dependencies
@remove *args:
    ./scripts/rust/remove.nu {{ args }}

# Run the application, with any provided <args>.
@run *args:
    ./scripts/rust/run.nu {{ args }}

# Run the tests
@test *args:
    ./scripts/rust/test.nu {{ args }}

# Update dependencies
@update *args:
    ./scripts/rust/update.nu {{ args }}
