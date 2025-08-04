.PHONY: clean clean-build clean-pyc clean-test dist install test lint format coverage help
.DEFAULT_GOAL := help

help: ## Show this help message
	@echo "Available commands:"
	@awk 'BEGIN {FS = ":.*##"} /^[a-zA-Z_-]+:.*##/ { printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2 }' $(MAKEFILE_LIST)

clean: clean-build clean-pyc clean-test ## Remove all build, test, coverage and Python artifacts

clean-build: ## Remove build artifacts
	rm -fr build/
	rm -fr dist/
	rm -fr .eggs/
	find . -name '*.egg-info' -exec rm -fr {} +
	find . -name '*.egg' -exec rm -f {} +

clean-pyc: ## Remove Python file artifacts
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -fr {} +

clean-test: ## Remove test and coverage artifacts
	rm -fr .tox/
	rm -f .coverage
	rm -fr htmlcov/
	rm -fr .pytest_cache

lint: ## Check code style with flake8
	flake8 --ignore=E501,W503,W504 spade_llm

format: ## Format code with black and isort
	black spade_llm/
	isort spade_llm/

test: ## Run tests quickly with pytest
	pytest

test-all: ## Run tests on every Python version with tox
	tox

coverage: ## Check code coverage quickly with pytest
	pytest --cov=spade_llm --cov-report=term-missing
	pytest --cov=spade_llm --cov-report=html
	@echo "HTML coverage report generated in htmlcov/"

build: clean ## Build source and wheel package
	python -m build
	ls -l dist

dist: clean ## Build source and wheel package (alias for build)
	python -m build
	ls -l dist

install: clean ## Install the package to the active Python's site-packages
	pip install .

install-dev: clean ## Install the package in development mode
	pip install -e ".[dev]"

upload-test: dist ## Upload to test PyPI
	twine check dist/*
	twine upload --repository-url https://test.pypi.org/legacy/ dist/*

upload: dist ## Upload to PyPI
	twine check dist/*
	twine upload dist/*

release: clean build upload ## Package and upload a release
	@echo "Release completed successfully!"

check: ## Check package before upload
	twine check dist/*
	@echo "Package check completed"