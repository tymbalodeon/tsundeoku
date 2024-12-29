# View help text
@help *recipe:
    ../scripts/rust/help.nu {{ recipe }}

# Add dependencies
@add *dependencies:
    ../scripts/rust/add.nu {{ dependencies }}

# Build the application
@build *release:
    ../scripts/rust/build.nu {{ release }}

# Remove generated files
@clean *help:
    ../scripts/rust/clean.nu {{ help }}

# Run clippy
@clippy *help:
    ../scripts/rust/clippy.nu {{ help }}

# Show application dependencies
@deps *help:
    ../scripts/rust/deps.nu {{ help }}

# Open a pre-configured development environment
@dev *help:
    ../scripts/rust/dev.nu {{ help }}

# Install the application
@install *help:
    ../scripts/rust/install.nu {{ help }}

# Remove dependencies
@remove *dependencies:
    ../scripts/rust/remove.nu {{ dependencies }}

# Run the application, with any provided <args>.
@run *args:
    ../scripts/rust/run.nu {{ args }}

# Run the tests
@test *package:
    ../scripts/rust/test.nu {{ package }}

# Update dependencies
@update *help:
    ../scripts/rust/update.nu {{ help }}
