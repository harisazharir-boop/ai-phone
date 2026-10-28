# Contributing

Bug reports, documentation fixes, tests and code contributions are welcome. For a larger feature or
architecture change, open an issue first so we can agree on the scope before you start.
For a smaller starting point, see the [good first issues](https://github.com/oxnw/ai-phone/labels/good%20first%20issue).
Please follow the [code of conduct](CODE_OF_CONDUCT.md) in issues, reviews and discussions.

## Reporting a bug

Search [existing issues](https://github.com/oxnw/ai-phone/issues) first. A useful report includes:

- What you expected and what happened instead.
- Steps or commands that reproduce the problem.
- Your ai-phone commit (`git rev-parse --short HEAD`), operating system and hardware.
- The relevant configuration, model choices and log or traceback excerpts.

Remove passwords, API keys, phone numbers and private conversation content before sharing configuration
or logs. If a problem also occurs with `--fake` backends, mention that; it helps separate call handling
from model behavior. Report suspected vulnerabilities privately using [SECURITY.md](SECURITY.md), rather
than opening a public issue.

## Development setup

Runtime development currently requires macOS on Apple Silicon, Git, [Homebrew](https://brew.sh) and
[uv](https://docs.astral.sh/uv/). The project supports Python 3.11–3.13.
The native build also needs Apple's command-line developer tools (`clang++`).

Fork the repository, then replace `YOUR-USERNAME` below with your GitHub username:

```bash
git clone https://github.com/YOUR-USERNAME/ai-phone.git
cd ai-phone
./scripts/install.sh
git switch -c my-change
```

The installer sets up the Python environment, including test dependencies, and builds the native SIP
library. It does not download model weights or change your phone configuration. You do not need to run
the setup wizard or connect a carrier account to run the unit tests.

Before changing runtime behavior, read [Architecture essentials](architecture-essentials.md), then the
relevant sections of the [full architecture](architecture.md). They explain the audio format, threading,
cancellation and single-call constraints.

## Running tests

Run the unit suite before committing:

```bash
env -u NO_COLOR uv run pytest tests/unit -q
```

Unsetting `NO_COLOR` keeps the terminal rendering assertions consistent. Run one suite at a time.

For SIP, pipeline or model changes, also run the relevant integration tests. This local SIP smoke test
uses fake models and needs no model downloads or carrier account:

```bash
env -u NO_COLOR AI_PHONE_TEST_SIP_PORT=5080 \
  uv run pytest tests/integration/test_daemon_smoke.py -q
```

Integration tests default to SIP port 5080, separate from a normal daemon on 5060. The explicit setting
above makes that choice visible; you can choose another free test range with the same variable. Check
that the test ports are free before running them.

Other integration tests exercise real model backends and may require downloaded weights.
The two tests in `tests/integration/test_cli_brains.py` use your logged-in Claude or ChatGPT subscription
and consume plan usage. They are skipped unless you explicitly set `AI_PHONE_TEST_LIVE_BRAINS=1`.
Enable this only for a deliberate check of your own account, and select the test you intend to run.
A bare `uv run pytest` includes the integration tests too, with these live-account tests skipped by default.

## Pull requests

Open a pull request against `main`. Keep it focused on one change, and include:

- The problem it solves, with a link to the issue if there is one.
- What changes for someone using ai-phone.
- The tests you ran and their results, including anything you could not verify.

For carrier-specific changes, distinguish local SIP tests from calls verified against the real provider.

For bug fixes, add a regression test that demonstrates the failure where practical. Keep documentation
and configuration examples in step with behavior changes. Follow the surrounding code's style and keep
unrelated refactors separate.

The project uses [AGPL-3.0-or-later](LICENSE). License notes for the native SIP interface are in
[native/pjsua2/README.md](native/pjsua2/README.md).
