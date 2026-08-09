"""SPEC-000: configuration and the offline guarantee."""

from __future__ import annotations

import socket
from pathlib import Path

import pytest

from harnesslab.config import Settings, git_sha, settings
from tests.conftest import NetworkAccessError


class TestSettingsPrecedence:
    """SPEC-000 AC-7: environment > .env > default."""

    def test_default_when_nothing_set(self, isolated_env: Path) -> None:
        assert Settings().log_dir == Path("./logs")

    def test_dotenv_beats_default(self, isolated_env: Path) -> None:
        (isolated_env / ".env").write_text("HARNESSLAB_LOG_DIR=./from-dotenv\n", encoding="utf-8")
        assert Settings().log_dir == Path("./from-dotenv")

    def test_environment_beats_dotenv(
        self, isolated_env: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        (isolated_env / ".env").write_text("HARNESSLAB_LOG_DIR=./from-dotenv\n", encoding="utf-8")
        monkeypatch.setenv("HARNESSLAB_LOG_DIR", "./from-env")
        assert Settings().log_dir == Path("./from-env")

    def test_settings_is_memoised(self) -> None:
        assert settings() is settings()


class TestNoCredentialsInConfig:
    """Settings must never hold an API key -- the invariant that keeps keys out
    of every log line and every serialized config."""

    @pytest.mark.parametrize(
        "forbidden", ["api_key", "groq", "google", "cerebras", "openrouter", "mistral", "token"]
    )
    def test_no_credential_shaped_field(self, forbidden: str) -> None:
        assert not [f for f in Settings.model_fields if forbidden in f.lower()]

    def test_dump_contains_no_secret(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("GROQ_API_KEY", "gsk-should-never-appear")
        assert "should-never-appear" not in str(Settings().model_dump())


class TestOfflineGuarantee:
    """SPEC-000 AC-3: `make check` makes zero network calls.

    These tests prove the guard itself works. Without them the guard could be
    silently broken and every other test would still pass.
    """

    def test_socket_creation_is_denied(self) -> None:
        with pytest.raises(NetworkAccessError):
            socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def test_connect_is_denied(self) -> None:
        with pytest.raises(NetworkAccessError):
            socket.create_connection(("example.com", 80), timeout=1)

    @pytest.mark.network
    def test_marked_tests_may_use_the_network(self) -> None:
        """A `network`-marked test is exempt -- and is excluded from `make check`."""
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.close()


def test_git_sha_is_a_sha_or_none() -> None:
    sha = git_sha()
    assert sha is None or (len(sha) == 40 and all(c in "0123456789abcdef" for c in sha))
