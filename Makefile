ROOT_DIR := $(dir $(realpath $(lastword $(MAKEFILE_LIST))))
SHELL := /bin/bash

include .devcontainer/.env
export

.PHONY: help
help: ## This help
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

.PHONY: bootstrap
bootstrap: ## Perform a bootstrap
	# deleting as there may be a conflict when running inside a devcontainer vs local host
	rm -rf .venv && rm -rf .tox
	curl -sSL https://install.python-poetry.org | python3 - --uninstall || true
	curl -sSL https://install.python-poetry.org | python3 -
	# help IDEs to recognize venv's python interpreter
	poetry config virtualenvs.in-project true
	poetry self add "poetry-dynamic-versioning[plugin]"
	# poetry will create .venv as well:
	poetry install --only dev
	# install pre-commit hooks
	source .venv/bin/activate \
		&& pre-commit install \
		&& pre-commit install --hook-type commit-msg
	# install app and all deps
	poetry install

.PHONY: lint
lint: ## Run linters
	tox -e lint

.PHONY: test
test: ## Run unit tests
	tox -e test

.PHONY: clean
clean: ## Remove all generated artifacts (except .venv and .env)
	find . -name '__pycache__' -exec rm -rf {} +
	find . -name '*.pyc' -exec rm -rf {} +
	rm -rf .mypy_cache
	rm -rf .pytest_cache
	rm -rf .tox
	rm -rf dist
