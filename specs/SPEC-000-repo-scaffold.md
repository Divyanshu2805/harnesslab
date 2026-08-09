---
spec: 000
title: Repo scaffold, uv, tooling, CI skeleton
status: Accepted
depends_on: []
day: 1
---

# SPEC-000 — Repo scaffold, uv, tooling, CI skeleton

## Motivation

Everything downstream assumes a reproducible environment, a strict type and lint
gate, and a test path that never touches a paid endpoint. Establishing those on
Day 1 costs a few hours; retrofitting them costs a rewrite, because by then the
code has grown against their absence.

The one non-obvious requirement is the **offline default**. This project spends
scarce free-tier quota, and a test suite that quietly burns tokens on every run
would consume the very budget the experiment needs. `make check` must be runnable
a hundred times a day at zero cost.

## Scope

**In scope**

- `pyproject.toml` with dependencies pinned by `uv.lock`, Python 3.12.
- Ruff (lint + format), mypy `--strict`, pytest with marker-based network/GPU
  isolation.
- Package skeleton at `src/harnesslab/` with `config.py` and `cli.py` entry point.
- `.github/workflows/ci.yml` — lint, types, offline tests. Must pass on fork PRs,
  which cannot read secrets.
- A hello-world Inspect task proving the framework is wired up end to end.

**Out of scope**

- The sweep, smoke, and publish workflows — SPEC-022.
- The results database — SPEC-018.
- Any provider registry content — SPEC-001 owns that.

## Interface contract

```python
# src/harnesslab/config.py
from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Process-wide configuration, layered env > .env > defaults."""

    model_config = SettingsConfigDict(
        env_prefix="HARNESSLAB_",
        env_file=".env",
        extra="ignore",
    )

    # Paths
    log_dir: Path = Field(default=Path("./logs"))
    data_dir: Path = Field(default=Path("./data"))

    # Results store. None selects the SQLite backend (local dev and fork CI).
    database_url: str | None = Field(default=None)

    # Admission control. Off only for deliberate manual overrides.
    enforce_budget: bool = Field(default=True)

    # Provenance stamped onto every result row.
    git_sha: str | None = Field(default=None)


def settings() -> Settings:
    """Cached accessor. Import this, never construct Settings directly."""
```

```python
# src/harnesslab/cli.py
import typer

app = typer.Typer(no_args_is_help=True, add_completion=False)

# Subcommands are registered by later specs:
#   run      SPEC-005    sweep    SPEC-022
#   budget   SPEC-006    ingest   SPEC-019
#   publish  SPEC-020
```

**Invariants**

- `Settings` never reads a provider API key. Keys are consumed by the provider
  SDKs directly from the environment, so no code path can log one by accident.
- `settings()` is memoised; configuration is resolved once per process.

## Design notes

**uv over pip/poetry.** Lockfile-clean, fast enough that CI cold-starts are not a
consideration, and it manages the Python 3.12 toolchain itself — the development
machine has 3.10 system-wide, and pinning through `.python-version` avoids a
class of "works on my machine" failure.

**mypy `--strict` from the first commit.** The project's core data structures are
Pydantic models that cross a serialization boundary into `.eval` logs and then
into Postgres. Type drift between those layers is the failure mode most likely
to silently corrupt results, and it is exactly what strict mode catches.

**Marker-based test isolation over a separate test directory.** `-m "not network
and not gpu"` keeps the offline guarantee in one place and lets an integration
test live beside the unit tests it complements. Inspect's `mockllm/model`
provider makes most integration tests offline anyway.

**Rejected: committing `uv.lock` only for CI.** The lock is committed for
everyone. Reproducing a result six months from now means reproducing the
environment that produced it, and the paper claims reproducibility.

## Acceptance criteria

- **AC-1.** `uv sync --extra dev` on a clean checkout produces a working
  environment on Python 3.12, with `uv.lock` committed and unchanged by the sync.
- **AC-2.** `make check` runs ruff, mypy `--strict`, and pytest, and exits zero.
- **AC-3.** `make check` makes **zero network calls**. Verified by a test that
  installs a socket guard failing any outbound connection, and by the absence of
  provider keys in the CI job environment.
- **AC-4.** `ci.yml` passes on a pull request from a fork, where no repository
  secret is readable.
- **AC-5.** `uv run harnesslab --help` lists the CLI and exits zero.
- **AC-6.** A hello-world Inspect task runs against one Groq model and writes a
  readable `.eval` log that opens in `inspect view`. Marked `network`; excluded
  from the default path.
- **AC-7.** `settings()` resolves `log_dir` from `HARNESSLAB_LOG_DIR`, then
  `.env`, then the default, in that precedence order.

## Test plan

| Level | What it covers |
|---|---|
| unit | Settings precedence (AC-7); `settings()` memoisation |
| unit | Socket guard fixture proves the offline invariant (AC-3) |
| integration | `harnesslab --help` exits zero (AC-5) |
| integration | Hello-world eval against Groq — marked `network` (AC-6) |

## Definition of done

- [ ] `make check` green
- [ ] Every AC demonstrated by a named test
- [ ] Docs updated: `README.md` install section, `docs/ARCHITECTURE.md` module map
- [ ] Status set to `Accepted`
