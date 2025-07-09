set working-directory := "../.."

# View help text
@help *args:
    .environments/scripts/rust/help.nu {{ args }}

# Add dependencies
@add *args:
    .environments/scripts/rust/add.nu {{ args }}

# Build the application
@build *args:
    .environments/scripts/rust/build.nu {{ args }}

# Remove generated files
@clean *args:
    .environments/scripts/rust/clean.nu {{ args }}

# Run clippy
@clippy *args:
    .environments/scripts/rust/clippy.nu {{ args }}

# Show application dependencies
@deps *args:
    .environments/scripts/rust/deps.nu {{ args }}

# Open a pre-configured development environment
@dev *args:
    .environments/scripts/rust/dev.nu {{ args }}

# Install the application
@install *args:
    .environments/scripts/rust/install.nu {{ args }}

# Remove dependencies
@remove *args:
    .environments/scripts/rust/remove.nu {{ args }}

# Run the application, with any provided <args>.
@run *args:
    .environments/scripts/rust/run.nu {{ args }}

# Run the tests
@test *args:
    .environments/scripts/rust/test.nu {{ args }}

# Update dependencies
@update *args:
    .environments/scripts/rust/update.nu {{ args }}
