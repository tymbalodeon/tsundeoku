ROOT_DIR := $(abspath $(dir $(lastword $(MAKEFILE_LIST))))
PYPROJECT := $(ROOT_DIR)/pyproject.toml
COMMAND := $(shell awk -F '[ ="]+' '$$1 == "name" { print $$2 }' $(PYPROJECT))
VERSION := $(shell awk -F '[ ="]+' '$$1 == "version" { print $$2 }' $(PYPROJECT))
ENTRY_POINT = main.py
WHEEL := ./dist/$(COMMAND)-$(VERSION)-py3-none-any.whl
POETRY = poetry run
PRE_COMMIT = pre-commit run

all: help

binary: ## Build a binary executable with pyinstaller
	poetry run pyinstaller $(ROOT_DIR)/$(ENTRY_POINT) --name $(COMMAND)

black: ## Format code
	$(POETRY) black ./

build: ## Build the CLI and isntall it in your global pip packages
	poetry build && pip install $(WHEEL) --force-reinstall

check: format ## Check for problems
	$(PRE_COMMIT) -a

flake: ## Lint code
	$(POETRY) pflake8 ./

format: isort black ## Format code

help: ## Display the help menu
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
	| sort \
	| awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

isort: ## Sort imports
	$(POETRY) isort ./

mypy: ## Type-check code
	$(PRE_COMMIT) mypy -a

try: ## Try a command using the current state of the files without building
ifdef args
	$(POETRY) $(COMMAND) $(args)
else
	$(POETRY) $(COMMAND)
endif
