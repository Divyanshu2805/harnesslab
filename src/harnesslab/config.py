"""Process-wide configuration.

Deliberately narrow. `Settings` never reads a provider API key: keys are consumed
by the provider SDKs straight from the environment, so no code path in this
project can log one by accident. If you find yourself wanting to add an API key
field here, that is the invariant telling you not to.
"""

from __future__ import annotations

import functools
import subprocess
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    """Configuration, layered: environment > .env > defaults."""

    model_config = SettingsConfigDict(
        env_prefix="HARNESSLAB_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- paths -------------------------------------------------------------
    log_dir: Path = Field(
        default=Path("./logs"),
        description="Where Inspect writes .eval logs before ingestion.",
    )
    data_dir: Path = Field(default=Path("./data"))

    # --- results store -----------------------------------------------------
    database_url: str | None = Field(
        default=None,
        description=(
            "Postgres connection string. None selects the SQLite backend, which "
            "is what local development and fork-PR CI use -- forks cannot read "
            "repository secrets."
        ),
    )

    # --- guard rails -------------------------------------------------------
    enforce_budget: bool = Field(
        default=True,
        description=(
            "Admission control. When true a sweep shard that cannot finish "
            "inside the remaining daily quota is refused rather than started, "
            "because a half-finished shard leaves an unbalanced cell. Disable "
            "only for a deliberate manual override."
        ),
    )

    @property
    def uses_postgres(self) -> bool:
        return bool(self.database_url)


@functools.lru_cache(maxsize=1)
def settings() -> Settings:
    """Cached accessor. Import this; never construct `Settings` directly.

    Caching matters for more than speed: configuration resolved twice in one
    process could disagree, and every result row is stamped with provenance
    derived from it.
    """
    return Settings()


@functools.lru_cache(maxsize=1)
def git_sha() -> str | None:
    """The commit that is running, stamped onto every result row.

    Returns None outside a git checkout rather than raising -- an installed
    wheel has no repository, and that is not an error.
    """
    try:
        out = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError, OSError):
        return None
    return out.stdout.strip() or None
