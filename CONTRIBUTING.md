# Contributing to FinceCore

Thank you for helping improve FinceCore.

This project is open source under AGPL-3.0-or-later and maintained by a startup building production software in public. We welcome high-quality contributions that improve reliability, security, and developer experience.

## Quick Start

1. Fork the repository.
2. Create a branch from main using one of these prefixes:
- feat/
- fix/
- docs/
- chore/
- refactor/
- test/
- ci/
- perf/
- build/
- security/
3. Make your changes.
4. Run checks and tests locally.
5. Open a Pull Request using the official PR template.

## Contribution Types

All commits and PR titles must use one of the allowed types:

- feat: new feature or behavior
- fix: bug fix
- docs: documentation only changes
- chore: maintenance tasks, no product behavior change
- refactor: code change with no behavior change
- test: add or update tests
- ci: CI/CD configuration changes
- perf: performance improvements
- build: dependency or build system changes
- security: hardening or vulnerability fixes
- revert: revert a previous change

## Commit Message Format

Use Conventional Commits format:

<type>(<optional-scope>): <short summary>

Examples:

- feat(dinheiro): add account sync retry guard
- fix(users): prevent duplicate device disconnect
- docs(architecture): document tenancy model
- chore(repo): add issue templates

Rules:

- Use imperative mood in the summary.
- Keep summary under 72 characters.
- Add a body when context is needed.
- Add footer references when relevant, for example: Closes #123.

## DCO Sign-off Requirement

By contributing, you certify the Developer Certificate of Origin in DCO.md.

Every commit must include a sign-off line:

Signed-off-by: Your Name <your-email@example.com>

Recommended command:

git commit -s -m "feat(scope): summary"

## Pull Request Title Standard

PR titles must follow this format:

<type>(<optional-scope>): <short summary>

Examples:

- fix(relatorios): avoid null division in margin calculation
- docs(governance): add trademark policy

## Pull Request Description Requirements

Use the PR template and fill all sections. Every PR should include:

- Problem statement
- Proposed solution
- Impact and risks
- Test evidence
- Documentation updates
- Security or privacy impact, if any
- Breaking changes, if any

## Code Quality Expectations

- Keep changes focused and small.
- Preserve existing public APIs unless change is intentional and documented.
- Add tests for behavior changes and bug fixes.
- Update docs when behavior, endpoints, or setup changes.
- Prefer explicit errors and safe defaults.

## Security and Responsible Disclosure

Do not open public issues for undisclosed vulnerabilities.

Please follow SECURITY.md.

## Legal and IP Rules

Only submit code you have the right to contribute.

Do not submit:

- copied proprietary code
- code with incompatible licenses
- confidential or personal data

By submitting contributions, you agree your changes are licensed under AGPL-3.0-or-later and project policies.

## Review and Merge Policy

Maintainers may request changes before merge.

A change may be rejected when:

- scope is unclear
- tests are missing for behavior changes
- legal or security concerns exist
- contribution does not align with project direction

## Community Conduct

All contributors must follow CODE_OF_CONDUCT.md.
