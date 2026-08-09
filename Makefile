# HarnessLab. One-command entry points.
#
# `make check` is the gate every spec must pass. It runs lint, types and tests
# with ZERO network calls -- the `network` and `gpu` markers are deselected, so
# a green check never depends on a provider being up or a quota being unspent.

.PHONY: help install check scaffold sync sync-check hooks lint fmt types \
        test test-network test-gpu providers pricing run smoke budget \
        ingest publish paper clean

help:
	@echo "install       Install the project and dev extras via uv"
	@echo "check         Sync + scaffold + lint + types + offline tests (per-spec gate)"
	@echo "scaffold      Verify spec dependencies, schedule ordering, docs, links"
	@echo "sync          Regenerate derived doc sections from spec frontmatter"
	@echo "hooks         Install the versioned git hooks (run once per clone)"
	@echo "lint / fmt    Ruff check / Ruff format"
	@echo "types         mypy --strict"
	@echo "test          Offline tests only (no network, no GPU)"
	@echo "test-network  Tests that hit live providers (spends quota)"
	@echo "test-gpu      Tests that need a local Ollama with Lane A models"
	@echo "providers     Re-verify live free-tier quotas, regenerate PROVIDERS.md"
	@echo "pricing       Refresh the notional pricing + GPU rental tables"
	@echo "budget        Pre-flight token forecast for a planned sweep"
	@echo "run           Single task against a single model"
	@echo "smoke         The nightly smoke suite"
	@echo "ingest        Load .eval logs into the results store"
	@echo "publish       Build the leaderboard JSON + static site"
	@echo "paper         Build the LaTeX paper with vector figures"

install:
	uv sync --extra dev --extra viz

check: sync-check scaffold lint types test

# Enforces the spec-system invariants: dependencies resolve, no cycles, and no
# dependency scheduled after its dependant. Runs early because it is instant and
# catches planning errors that are invisible to the type checker.
scaffold:
	uv run python scripts/verify_scaffold.py

# Regenerate the derived doc sections (spec statuses, counts, what is next).
# The pre-commit hook runs this with --write and re-stages what it changes.
sync:
	uv run python scripts/sync_docs.py --write

# CI form: fail if the committed docs have drifted from repository state.
sync-check:
	uv run python scripts/sync_docs.py --check

# Install the versioned hooks. Run once per clone.
hooks:
	git config core.hooksPath .githooks
	@echo "hooks installed: pre-commit (sync + verify), post-commit (DEVLOG)"

lint:
	uv run ruff check src tests
	uv run ruff format --check src tests

fmt:
	uv run ruff format src tests
	uv run ruff check --fix src tests

types:
	uv run mypy src

# -m filters out anything that would touch a provider or the GPU.
test:
	uv run pytest -m "not network and not gpu"

test-network:
	uv run pytest -m network

test-gpu:
	uv run pytest -m gpu

# --- Operational entry points ----------------------------------------------

providers:
	uv run python scripts/verify_providers.py --write-docs

pricing:
	uv run python scripts/fetch_pricing.py

budget:
	uv run harnesslab budget --plan $(PLAN)

run:
	uv run harnesslab run --task $(TASK) --model $(MODEL)

smoke:
	uv run harnesslab sweep --suite smoke

ingest:
	uv run harnesslab ingest --logs $(INSPECT_LOG_DIR)

publish:
	uv run harnesslab publish --out site/data

paper:
	uv run harnesslab publish --figures paper/figures --format pdf
	cd paper && latexmk -pdf main.tex

clean:
	rm -rf .pytest_cache .mypy_cache .ruff_cache htmlcov .coverage
