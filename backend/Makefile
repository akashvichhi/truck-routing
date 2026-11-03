.PHONY: check lint format typecheck test

check: lint format typecheck test

lint:
	uv run ruff check . --fix

format:
	uv run ruff format .

typecheck:
	uv run mypy api config

test:
	uv run pytest
