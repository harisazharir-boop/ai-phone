"""Tests use fake subscription CLIs unless a live integration run is explicitly requested.

Those two spend the person's own Claude or ChatGPT plan: a turn is real money and a shared resource, and a suite that
quietly uses one is also a suite that fails on a machine where nobody is logged in. A green run has to mean the fakes
were used, so an unexpected attempt to start either CLI fails loudly, saying what to do instead.

A fake installed under the real name is fine, and that is the point: what is refused is one of those names from
anywhere outside the test's own temporary directory. The live_brains integration tests are skipped before fixtures
run unless AI_PHONE_TEST_LIVE_BRAINS=1. Unit tests never get that exemption.
"""
from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest

REAL_CLIS = {"claude", "codex", "claude.exe", "codex.exe"}


def pytest_configure():
    # The shell peer reads this too; keep its target and the Python daemon fixtures on the same test ports.
    os.environ.setdefault("AI_PHONE_TEST_SIP_PORT", "5080")


def pytest_collection_modifyitems(items):
    if os.environ.get("AI_PHONE_TEST_LIVE_BRAINS") == "1":
        return
    skip = pytest.mark.skip(reason="uses a real subscription; opt in with AI_PHONE_TEST_LIVE_BRAINS=1")
    for item in items:
        if item.get_closest_marker("live_brains"):
            item.add_marker(skip)


@pytest.fixture(autouse=True)
def _no_real_subscription_cli(request, monkeypatch, tmp_path_factory):
    is_unit = "tests/unit" in Path(str(request.node.fspath)).as_posix()
    if (not is_unit and request.node.get_closest_marker("live_brains")
            and os.environ.get("AI_PHONE_TEST_LIVE_BRAINS") == "1"):
        return
    ours = tmp_path_factory.getbasetemp().resolve()

    def refuse(argv) -> None:
        try:
            first = argv if isinstance(argv, (str, bytes)) else argv[0]
        except (IndexError, TypeError):
            return
        path = Path(str(first))
        if path.name not in REAL_CLIS:
            return
        try:
            if path.resolve().is_relative_to(ours):
                return  # a fake this test installed under that name
        except OSError:
            pass
        raise AssertionError(
            f"a test tried to run {str(first)!r}. That spends a turn of the owner's plan and fails on a machine "
            f"with no login: install the fake CLI (tests/unit/test_cli_brain.FAKE_CLI) under that name on an isolated "
            f"PATH, or pass its path to the backend."
        )

    for name in ("Popen", "run"):
        real = getattr(subprocess, name)

        def guarded(args, *a, _real=real, **kw):
            refuse(args)
            return _real(args, *a, **kw)

        monkeypatch.setattr(subprocess, name, guarded)
