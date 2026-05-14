# Bone Remap Agent Notes

## Project working constraints

- Performance first. While designing and implementing Blender runtime logic, prefer algorithms and data flow that minimize evaluation cost. Use vectorized/numpy-based processing where it materially reduces Blender Python overhead, and avoid per-frame/per-bone work that can be precomputed, cached, or batched.
- Reuse before rebuilding. Before adding new helpers or systems, inspect the repo for existing code with overlapping responsibility. Extract shared logic when duplication would make retargeting behavior harder to reason about or maintain.
- Keep the codebase clean. Do not preserve obsolete branches merely for compatibility. Delete replaced logic when a new path is the intended path, avoid unnecessary rollback code, and keep condition trees small enough that future animation/retargeting behavior remains readable.

## Agent skills

### Issue tracker

Issues and PRDs are tracked in GitHub Issues for `ssice-a/Bone_Remap`. See `docs/agents/issue-tracker.md`.

### Triage labels

This repo uses the default mattpocock/skills triage labels. See `docs/agents/triage-labels.md`.

### Domain docs

This is a single-context repo using root `CONTEXT.md` and `docs/adr/`. See `docs/agents/domain.md`.
