# Security

## Supported versions

Security fixes target the current `main` branch. Older commits and forks do not have a separate security maintenance policy.

## Reporting a vulnerability

Report suspected vulnerabilities through [GitHub's private vulnerability reporting](https://github.com/oxnw/ai-phone/security/advisories/new). Please keep exploit details out of public issues and pull requests while the report is investigated.

Include:

- The affected commit, operating system and relevant dependency versions.
- The configuration needed to reproduce the problem, with credentials and personal data removed.
- Minimal reproduction steps or a small test using synthetic data.
- What happened, what you expected, and the potential impact.

Do not attach credentials, `secrets.env`, real phone numbers, account identifiers, call recordings or real call transcripts. Use synthetic examples and review any log excerpts before sharing them, including in a private report.

Use [issues](https://github.com/oxnw/ai-phone/issues) for ordinary bugs and setup questions. If you are unsure whether a finding is security-sensitive, report it privately first. Response and fix times depend on maintainer availability.

## Scope

Relevant reports include unauthorized call control, disclosure of credentials or private data, and callers gaining access to the host through a model backend. ai-phone is self-hosted; its owner controls its configuration and source. Built-in limits are not a guarantee against misuse of a modified deployment.
