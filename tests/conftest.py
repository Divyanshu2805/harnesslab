"""Shared fixtures.

The important one is `_no_network`, which enforces the project's offline
guarantee: `make check` must never make a network call.

This is a *budget* property, not hygiene. Free-tier quota is the experiment's
scarcest resource, and a test suite that quietly spent tokens on every run would
consume the very thing the experiment needs. It is also what lets CI pass on
fork pull requests, which cannot read repository secrets.
"""

from __future__ import annotations

import socket
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent


class NetworkAccessError(RuntimeError):
    """Raised when an offline test reaches for the network."""


@pytest.fixture(autouse=True)
def _no_network(request: pytest.FixtureRequest, monkeypatch: pytest.MonkeyPatch) -> None:
    """Fail any test that opens a socket, unless it is marked `network`.

    Autouse and opt-out rather than opt-in: a new test that accidentally hits a
    provider should fail loudly on the first run, not spend quota silently for
    weeks before anyone notices.
    """
    if request.node.get_closest_marker("network"):
        return

    def denied(*args: Any, **kwargs: Any) -> Any:
        raise NetworkAccessError(
            "network access from an offline test. Mark it @pytest.mark.network "
            "if it genuinely needs a provider -- but then it will not run in "
            "`make check`, by design."
        )

    monkeypatch.setattr(socket, "socket", denied)
    monkeypatch.setattr(socket, "create_connection", denied)


@pytest.fixture(autouse=True)
def _no_io(request: pytest.FixtureRequest, monkeypatch: pytest.MonkeyPatch) -> None:
    """Forbid filesystem and clock access in tests marked `pure`.

    Used by SPEC-002's determinism tests and SPEC-004's scorer tests, where
    purity is the property under test rather than an implementation detail.
    """
    if not request.node.get_closest_marker("pure"):
        return

    import time

    def denied(*args: Any, **kwargs: Any) -> Any:
        raise RuntimeError("a `pure` unit touched the clock or the filesystem")

    monkeypatch.setattr(time, "time", denied)
    monkeypatch.setattr(time, "monotonic", denied)


@pytest.fixture
def repo_root() -> Path:
    return REPO_ROOT


@pytest.fixture
def isolated_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Iterator[Path]:
    """Run with no HARNESSLAB_* variables and no .env in scope.

    Settings precedence tests need a clean slate; a developer's real .env would
    otherwise change the result depending on whose machine ran the suite.
    """
    for key in list(os_environ_keys()):
        if key.startswith("HARNESSLAB_"):
            monkeypatch.delenv(key, raising=False)
    monkeypatch.chdir(tmp_path)
    yield tmp_path


def os_environ_keys() -> list[str]:
    import os

    return list(os.environ)
