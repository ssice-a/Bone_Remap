# Solve One Frame From Work Pose and Mapping Table

Label: `ready-for-agent`

## What to build

Implement the first narrow retarget solve: read the Active Retarget Profile, current evaluated source pose, saved Work Pose Matrices, current Mapping Table, and target bind/reference matrices; compute full source deltas; write solved target pose matrices to mapped target Deform Channels for one update.

This is the core tracer bullet proving that a saved Work Pose plus manual Mapping Table can drive B from A.

## Acceptance criteria

- [ ] Solver reads source and target armatures from the Active Retarget Profile.
- [ ] Solver computes `source_delta = source_live_matrix @ inverse(source_work_pose_matrix)`.
- [ ] Solver computes `target_pose_matrix = source_delta @ target_bind_matrix` for each mapped Target Link.
- [ ] One Mapping Row computes one shared source delta for all of its Target Links.
- [ ] Target Link does not store per-target motion offset, weight, or follow rule.
- [ ] Solver writes target pose state only and does not author target action channels.
- [ ] Solver does not modify source edit bones, target edit bones, target rest data, or Target Bind Matrix values.
- [ ] Unmapped target bones are not inferred, animated, or cleared by this solve.

## Blocked by

- Capture and Re-Enter Work Pose
- Author Source-First Mapping Table Manually
