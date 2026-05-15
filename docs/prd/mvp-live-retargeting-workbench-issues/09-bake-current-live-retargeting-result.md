# Bake the Current Live Retargeting Result

Label: `ready-for-agent`

## What to build

Add **Bake** that samples the current visible Live Retargeting result and writes a **Baked Target Action**. Bake must match the viewport preview for each sampled frame and must not recompute retargeting directly from raw source F-curves.

This slice should be demoable by playing Live Preview, baking the mapped target channels, disabling live preview, and playing the baked target action to see the same visible result.

## Acceptance criteria

- [ ] Bake samples the current target-side visible Live Retargeting result.
- [ ] Bake does not bypass Work Pose, Mapping Table, or Live Retargeting.
- [ ] Bake does not recompute retargeting directly from the Motion Action.
- [ ] Default Bake Range comes from the active Motion Action's effective frame range.
- [ ] If the active Motion Action has no usable effective frame range, Bake requires a Bake Range Override.
- [ ] Bake samples every integer frame inside the Bake Range by default.
- [ ] Bake writes location, rotation, and scale for mapped Deform Channels by default.
- [ ] Bake creates a new Baked Target Action by default.
- [ ] Bake Overwrite only replaces keys inside Bake Scope and Bake Range.
- [ ] Unmapped target bones are not written, cleared, inferred, or compensated.

## Blocked by

- Run Live Preview for the Active Retarget Profile
