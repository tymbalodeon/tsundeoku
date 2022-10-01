ROOT_DIR := $(abspath $(dir $(lastword $(MAKEFILE_LIST))))
PYPROJECT := $(ROOT_DIR)/pyproject.toml
COMMAND := $(shell awk -F '[ ="]+' '$$1 == "name" { print $$2 }' $(PYPROJECT))
VERSION := $(shell awk -F '[ ="]+' '$$1 == "version" { print $$2 }' $(PYPROJECT))
WHEEL := ./dist/$(COMMAND)-$(VERSION)-py3-none-any.whl
POETRY = poetry run
PRE_COMMIT = pre-commit run
BEETS_CONFIG_FOLDER = ~/.config/beets
BEETS_CONFIG_PATH = $(BEETS_CONFIG_FOLDER)/config.yaml
TEST = $(POETRY) coverage run -m pytest
COVERAGE = $(POETRY) coverage report -m --skip-covered --sort=cover

define BEETS_CONFIG_VALUES
directory: ~/Music
library: ~/.config/beets/library.db
import:
  incremental: yes
  autotag: no
endef

all: help

export BEETS_CONFIG_VALUES
beets:
	mkdir -p $(BEETS_CONFIG_FOLDER)
	echo "$$BEETS_CONFIG_VALUES" > $(BEETS_CONFIG_PATH)

.PHONY: build
build: ## Build the CLI and isntall it in your global pip packages
	poetry install && poetry build && pipx install $(WHEEL) --force --pip-args='--force-reinstall'

check: ## Check for problems
	$(POETRY) $(PRE_COMMIT) -a

coverage: test ## Run coverage report (options: "fail-under=<percentage>", "search=<term>")
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
	| awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

shell: ## Run bpython in project virtual environment
	$(POETRY) bpython

start: beets build ## Add beets config before installing tsundeoku

test: ## Run tests (options: "print=true", "args=<args>")
ifdef print
	$(TEST) -s
else ifdef args
	$(TEST) $(args)
else
	$(TEST)
endif

try: ## Try a command using the current state of the files without building
ifdef args
	$(POETRY) $(COMMAND) $(args)
else
	$(POETRY) $(COMMAND)
endif
