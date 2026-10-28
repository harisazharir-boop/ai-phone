"""Exercise pytest's live-account boundary without discovering or running either real CLI."""
from pathlib import Path
import runpy

import pytest
import yaml

pytest_plugins = ["pytester"]
ROOT = Path(__file__).resolve().parents[2]

# Append these stand-ins to the actual integration module. A missing skip therefore runs a fake, never an account.
FAKE_BRAINS = '''
from pathlib import Path
from types import SimpleNamespace

def record(event):
    with Path("cli-calls.txt").open("a") as out:
        out.write(event + "\\n")

def which(name):
    record("discover " + name)
    return "/fake/" + name

def login(args, **kwargs):
    record("login " + args[0])
    return SimpleNamespace(stdout="Logged in", stderr="", returncode=0)

def available_models():
    record("models codex")
    return [SimpleNamespace(id="gpt-5.6-luna", name="Fake model")]

class FakeBrain:
    _spent = False
    last_timings = {"first_token_ms": 0}

    def __init__(self, **kwargs):
        record("construct " + kwargs["model"])

    def cli_version(self):
        return "fake"

    def prepare(self, prompt):
        record("prepare")

    def stream(self, *args):
        record("turn")
        yield "Hello from a fake CLI."

    def close(self):
        record("close")

shutil = SimpleNamespace(which=which)
subprocess = SimpleNamespace(run=login)
codex_models = available_models
ClaudeCodeLLM = CodexLLM = FakeBrain
'''


@pytest.fixture
def live_suite(pytester):
    pytester.makeconftest((ROOT / "tests/conftest.py").read_text())
    pytester.makeini("[pytest]\nmarkers =\n    integration: integration\n    live_brains: real subscription\n")
    source = (ROOT / "tests/integration/test_cli_brains.py").read_text()
    pytester.makepyfile(test_cli_brains=source + FAKE_BRAINS)
    return pytester


@pytest.mark.parametrize("opt_in", [None, "", "0", "true"])
def test_live_brains_skip_before_discovery_login_or_turns(live_suite, monkeypatch, opt_in):
    if opt_in is None:
        monkeypatch.delenv("AI_PHONE_TEST_LIVE_BRAINS", raising=False)
    else:
        monkeypatch.setenv("AI_PHONE_TEST_LIVE_BRAINS", opt_in)
    result = live_suite.runpytest_inprocess("-q", "-rs", "--strict-markers")
    result.assert_outcomes(skipped=2)
    result.stdout.fnmatch_lines(["*AI_PHONE_TEST_LIVE_BRAINS=1*"])
    assert not (live_suite.path / "cli-calls.txt").exists()


def test_explicit_opt_in_reaches_both_brains_using_only_fakes(live_suite, monkeypatch):
    monkeypatch.setenv("AI_PHONE_TEST_LIVE_BRAINS", "1")
    result = live_suite.runpytest_inprocess("-q", "--strict-markers")
    result.assert_outcomes(passed=2)
    calls = (live_suite.path / "cli-calls.txt").read_text().splitlines()
    assert "discover claude" in calls and "discover codex" in calls
    assert "login codex" in calls and "models codex" in calls
    assert calls.count("turn") == 2
    assert calls.count("close") == 2


@pytest.mark.parametrize("override, expected", [(None, 5080), ("5090", 5090)])
def test_shell_peer_inherits_the_same_test_port(pytester, monkeypatch, override, expected):
    if override is None:
        monkeypatch.delenv("AI_PHONE_TEST_SIP_PORT", raising=False)
    else:
        monkeypatch.setenv("AI_PHONE_TEST_SIP_PORT", override)
    monkeypatch.delenv("PJSUA_PEER_PORT", raising=False)
    pytester.makeconftest((ROOT / "tests/conftest.py").read_text())
    pytester.makepyfile(f'''
        import os
        import subprocess

        def test_peer(tmp_path, monkeypatch):
            assert os.environ["AI_PHONE_TEST_SIP_PORT"] == "{expected}"
            peer = tmp_path / "pjsua"
            peer.write_text('#!/bin/sh\\nprintf "%s\\\\n" "$@"\\n')
            peer.chmod(0o700)
            monkeypatch.setenv("PATH", str(tmp_path) + os.pathsep + os.environ["PATH"])
            result = subprocess.run(["bash", {str(ROOT / "scripts/pjsua_peer.sh")!r}, "in.wav", "out.wav"],
                                    capture_output=True, text=True, check=True)
            args = result.stdout.splitlines()
            assert args[args.index("--local-port") + 1] == "{expected + 2}"
            assert args[-1] == "sip:ai@127.0.0.1:{expected}"
    ''')
    pytester.runpytest_inprocess("-q").assert_outcomes(passed=1)


@pytest.mark.parametrize("override, expected", [(None, 5080), ("5090", 5090), ("5100", 5100)])
def test_integration_ports_default_away_from_production_and_honor_overrides(monkeypatch, override, expected):
    if override is None:
        monkeypatch.delenv("AI_PHONE_TEST_SIP_PORT", raising=False)
    else:
        monkeypatch.setenv("AI_PHONE_TEST_SIP_PORT", override)
    ports = runpy.run_path(str(ROOT / "tests/integration/ports.py"))
    assert ports["SIP_PORT"] == expected
    assert ports["PEER_PORT"] == expected + 2
    assert ports["SECOND_SIP_PORT"] == expected + 4
    assert 5060 not in range(expected, expected + 7)
    low = 10000 + (expected - 5060) * 100
    assert (ports["RTP_MIN"], ports["RTP_MAX"]) == (low, low + 100)
    parsed = yaml.safe_load(ports["SIP_CONFIG"])
    assert parsed["sip"]["bind"] == {"udp_port": expected, "tcp_port": expected, "tls_port": expected + 1}
    assert parsed["rtp"] == {"port_min": low, "port_max": low + 100}
    config = ports["config"]()
    assert (config.sip.bind.udp_port, config.sip.bind.tcp_port, config.sip.bind.tls_port) == (
        expected, expected, expected + 1,
    )
    assert (config.rtp.port_min, config.rtp.port_max) == (low, low + 100)
