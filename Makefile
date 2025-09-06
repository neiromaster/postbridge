lint:
    uv run ruff check .

typecheck:
    uv run pyright

test:
    uv run pytest -v

run:
    uv run python main.py
