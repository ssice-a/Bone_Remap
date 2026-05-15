# Classify Work Pose Input and Output Compensation

Label: `ready-for-agent`

## What to build

Extend Work Pose Save with source channel snapshots, changed-channel detection, automatic classification into **Input Compensation** and **Output Compensation**, sparse input compensation storage, ambiguity reporting, and user overrides.

This slice should be demoable by editing ordinary FK bones, IK targets, and ambiguous controls in Work Pose Edit Mode, then saving and seeing the expected classification report and stored compensation data.

## Acceptance criteria

- [ ] Entering Work Pose Edit Mode captures a Work Pose Edit Snapshot.
- [ ] Work Pose Save detects Changed Source Channels by comparing current source state to the snapshot.
- [ ] Standard IK target and pole target relationships visible in constraints are classified as Source Solver Inputs.
- [ ] Changed Source Solver Inputs are stored as sparse Input Compensation Transforms.
- [ ] Ordinary FK/output-only source bones rely on Work Pose Matrices rather than input compensation.
- [ ] Ambiguous Source Channels are reported without blocking Work Pose Save.
- [ ] Ambiguous channels default to Output Compensation until resolved.
- [ ] Users can add Classification Overrides for channels that are classified incorrectly.

## Blocked by

- Capture and Re-Enter Work Pose
- Run Live Preview for the Active Retarget Profile
