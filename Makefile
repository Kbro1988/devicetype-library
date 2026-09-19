PYTHON ?= python3
PYTEST ?= $(PYTHON) -m pytest
PRE_COMMIT ?= pre-commit
YAMLLINT ?= yamllint

.PHONY: install validate validate-file lint format

install:
	$(PYTHON) -m pip install -r requirements.txt

validate:
	DTL_USE_LOCAL_KNOWN_SLUGS=1 $(PYTEST) tests/definitions_test.py --tb=short -v

validate-file:
	@test -n "$(FILE)" || (echo "Usage: make validate-file FILE=path/to/definition.yaml" >&2; exit 2)
	$(PYTHON) scripts/validate-definition.py "$(FILE)"

lint:
	$(YAMLLINT) --format github --strict device-types/ module-types/

format:
	$(PRE_COMMIT) run --config .pre-commit-hooks-config.yaml --all-files
	$(PRE_COMMIT) run --config .pre-commit-yamlfmt-config.yaml --all-files
