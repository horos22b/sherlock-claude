.PHONY: install install-dev docs clean test venv venv-create venv-activate venv-deactivate

# Virtual environment name
VENV_NAME := venv

# Python interpreter
PYTHON := python3

# Create a virtual environment
venv-create:
	$(PYTHON) -m venv $(VENV_NAME)

# Activate the virtual environment (Note: this will only work in certain shells)
venv-activate:
	@echo "To activate the virtual environment, use:"
	@echo "source $(VENV_NAME)/bin/activate"

# Deactivate the virtual environment (Note: this will only work in certain shells)
venv-deactivate:
	@echo "To deactivate the virtual environment, use:"
	@echo "deactivate"

# Ensure the virtual environment is created and activated before running other commands
venv: venv-create

# Install dependencies from requirements.txt and then install the package
install: venv
	. $(VENV_NAME)/bin/activate && pip install -r requirements.txt && pip install .

# Install dev dependencies, requirements, and the package in editable mode
install-dev: venv
	. $(VENV_NAME)/bin/activate && pip install -r requirements-dev.txt && pip install -r requirements.txt && pip install -e .

# Build the documentation
docs: install-dev
	. $(VENV_NAME)/bin/activate && $(MAKE) -C docs html

# Clean up build artifacts and remove the virtual environment
clean:
	$(MAKE) -C docs clean
	rm -rf build dist *.egg-info
	rm -rf $(VENV_NAME)

# Alias for docs target
html: docs

# Run tests (adjust the command if you're using a different test runner)
test: install-dev
	. $(VENV_NAME)/bin/activate && python -m pytest tests/

# Install Sphinx for documentation (now part of dev dependencies)
install-docs: install-dev
