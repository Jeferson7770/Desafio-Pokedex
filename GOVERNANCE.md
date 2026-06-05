# Governance

## Purpose

This document defines how FinceCore is maintained and how decisions are made.

## Project Roles

- Core Maintainers: responsible for roadmap, architecture, and final merge decisions.
- Maintainers: review and merge changes in owned areas.
- Contributors: submit patches, docs, tests, and issue reports.

## Decision Model

Default model:

- Maintainer consensus for normal changes.
- Core Maintainer decision for high-impact or disputed changes.

High-impact examples:

- breaking API changes
- major security model changes
- data model migrations with operational risk
- licensing, legal, or policy updates

## Technical Direction

The project balances:

- product reliability in production
- sustainable open source collaboration
- predictable API and data evolution

Maintainers may decline contributions that conflict with these principles.

## Merge Requirements

A PR is generally eligible for merge when:

- CI checks pass
- required reviews are approved
- PR template is fully completed
- legal and security expectations are satisfied

## Conflict Resolution

When disagreement happens:

1. Discuss in the PR with concrete technical arguments.
2. Escalate to a Core Maintainer if no consensus.
3. Core Maintainer decision is final for repository governance.

## Becoming a Maintainer

Contributors may be invited based on:

- consistent high-quality contributions
- reliable review behavior
- good communication and collaboration
- alignment with project security and legal standards

## Policy Changes

Governance updates are proposed by PR and approved by Core Maintainers.
