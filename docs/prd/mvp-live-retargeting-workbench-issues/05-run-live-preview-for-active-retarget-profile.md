# Run Live Preview for the Active Retarget Profile

Label: `ready-for-agent`

## What to build

Add **Live Preview** as the user-facing automatic preview state around the one-frame solver. When **Live Preview Enabled** is on, relevant timeline, evaluation, pose, Work Pose, Mapping Table, or target bind/reference changes update the Target Armature for the Active Retarget Profile.

This slice should be demoable by enabling live preview, dragging the timeline or posing the source, and seeing mapped target Deform Channels update automatically.

## Acceptance criteria

- [ ] Live Preview can be enabled and disabled explicitly.
- [ ] Live Preview runs only for the Active Retarget Profile.
- [ ] Live Preview does not scan the scene for every possible armature pair.
- [ ] Timeline/playback changes can update the target result.
- [ ] Source pose changes can update the target result.
- [ ] Work Pose and Mapping Table changes can update the target result.
- [ ] Disabling Live Preview stops future automatic Live Matrix Write operations but leaves the Target Armature in its current pose.
- [ ] Dirty flags and cached profile data may be used, but cache invalidation preserves the same visible result as immediate solve.

## Blocked by

- Solve One Frame From Work Pose and Mapping Table
