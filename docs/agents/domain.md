# Domain Docs

How the engineering skills should consume this repo's domain documentation when exploring the codebase.

## Layout

This is a single-context repo.

Expected domain documentation:

- `CONTEXT.md` at the repo root for project vocabulary, domain concepts, and glossary terms.
- `docs/adr/` for architectural decision records.

If these files do not exist yet, proceed silently. Producer skills such as `grill-with-docs` can create them lazily when project terms or decisions get resolved.

## Before Exploring

Read the relevant domain docs before making architecture, diagnosis, or implementation decisions:

- Root `CONTEXT.md`, if present.
- ADRs in `docs/adr/` that touch the area being changed, if present.

## Use The Glossary's Vocabulary

When output names a domain concept in an issue title, refactor proposal, hypothesis, or test name, use the term as defined in `CONTEXT.md`.

If the needed concept is not in the glossary yet, either reconsider whether the term belongs in the project language or note it as something for `grill-with-docs` to clarify.

## Flag ADR Conflicts

If an output contradicts an existing ADR, surface it explicitly rather than silently overriding the decision.
