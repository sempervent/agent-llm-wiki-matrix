"""Pytest configuration."""

from __future__ import annotations

from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[1]


@pytest.fixture(autouse=True)
def alwm_repo_root(monkeypatch: pytest.MonkeyPatch) -> None:
    """Resolve schemas relative to this repository during tests."""
    monkeypatch.setenv("ALWM_REPO_ROOT", str(_REPO))
    monkeypatch.chdir(_REPO)
