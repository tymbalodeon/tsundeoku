get_pyproject_value = $(shell awk -F '[ ="]+' '$$1 == "$(1)" { print $$2 }' ./pyproject.toml)
COMMAND := $(call get_pyproject_value,name)

all: help

define BEETS_CONFIG_VALUES
directory: ~/Music
library: ~/.config/beets/library.db
import:
  incremental: yes
  autotag: no
endef
BEETS_CONFIG_FOLDER = ~/.config/beets
export BEETS_CONFIG_VALUES
beets:
	mkdir -p $(BEETS_CONFIG_FOLDER)
	echo "$$BEETS_CONFIG_VALUES" > $(BEETS_CONFIG_FOLDER)/config.yaml

VERSION := $(call get_pyproject_value,version)
WHEEL := ./dist/$(COMMAND)-$(VERSION)-py3-none-any.whl
.PHONY: build
build: ## Build the project and pipx install it.
	poetry install && poetry build && pipx install $(WHEEL) --force --pip-args='--force-reinstall'

check: ## Run pre-commit checks.
	poetry run pre-commit run -a

COVERAGE = poetry run coverage report -m --skip-covered --sort=cover
coverage: test ## Run coverage report. [options: "fail-under=<percentage>", "search=<term>"]
ifdef fail-under
	$(COVERAGE) --fail-under $(fail-under)
else ifdef search
	$(COVERAGE) | grep $(search)
else
	$(COVERAGE)
endif

help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
	| sort \
	| awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-10s\033[0m %s\n", $$1, $$2}'

shell: ## Open bpython interpreter in the project's virtual environment.
	poetry run bpython

start: beets build ## Add beets config and build.

TEST = poetry run coverage run -m pytest $(args)
test: ## Run tests. [options: "print=true", "args=<args>"]
ifdef print
	$(TEST) -s
else
	$(TEST)
endif

try: ## Try a command using the current state of the files without building. [options: "args=<args>"]
	poetry run $(COMMAND) $(args)
