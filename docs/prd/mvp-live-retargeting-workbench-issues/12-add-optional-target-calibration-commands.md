# Add Optional Target Calibration Commands

Label: `ready-for-agent`

## What to build

Add explicit optional target-side convenience commands such as **Channel Alignment** and **Target Bind Refresh**. These commands may modify mapped target edit-mode bone placement or refresh target bind/reference data only when the user asks, and must not become prerequisites for mapping, Live Preview, Auto Map, or Bake.

This slice should be demoable by running Channel Alignment to move mapped target bone heads to source Control Frame pivots for readability, refreshing target bind/reference data, and then confirming Live Preview still uses the same core retarget pipeline.

## Acceptance criteria

- [ ] Target Calibration commands are explicit user actions.
- [ ] Target Calibration is never required for mapping, Live Preview, Auto Map, or Bake.
- [ ] Channel Alignment requires a captured Work Pose.
- [ ] Channel Alignment moves target heads only for mapped Target Links.
- [ ] Channel Alignment does not modify unmapped target bones.
- [ ] Channel Alignment does not change target length, roll, constraints, or parent hierarchy in the first design.
- [ ] Target Bind Refresh updates affected target bind/reference data after explicit target-side calibration changes.
- [ ] Target Calibration results do not prove mapping correctness.

## Blocked by

- Author Source-First Mapping Table Manually
- Solve One Frame From Work Pose and Mapping Table
