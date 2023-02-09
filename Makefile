.PHONY: format
format:
	python3 -m black .

.PHONY: lint
lint:
	python3 -m ruff .

.PHONY: mypy
mypy:
	python3 -m mypy --strict .
