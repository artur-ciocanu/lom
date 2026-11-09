set dotenv-load := false

default:
    @just --list

sync:
    uv sync --locked

install-hooks:
    uv run --locked pre-commit install --install-hooks

lint:
    uv run --locked ruff check .

format-check:
    uv run --locked ruff format --check .

format:
    uv run --locked ruff format .

type-check:
    uv run --locked pyright

audit:
    uv audit --locked

test:
    uv run --locked python -m unittest discover -s tests -v

check: lint format-check type-check test
