# Auto Map From Work Pose Using Weighted Geometry

Label: `ready-for-agent`

## What to build

Add the first **Auto Map From Work Pose** command. It reads the Active Retarget Profile, requires a saved Work Pose, derives bound source/target mesh sets from armature modifiers, builds weighted source/target regions, compares them in normalized comparison space, and writes accepted matches into the Mapping Table through normal Target Assignment Operation semantics.

This slice should be demoable by running auto map on a weighted source/target pair, getting matched target channels assigned into source rows, and leaving low-confidence or unmatched targets available for manual cleanup.

## Acceptance criteria

- [ ] Auto Map requires a saved Work Pose.
- [ ] Auto Map reads source and target armatures from the Active Retarget Profile.
- [ ] Bound Mesh Discovery derives source and target mesh sets from Armature modifier bindings.
- [ ] Usable vertex-group weight data requires exact vertex-group-name to bone-name matches and nonzero weight above the project epsilon.
- [ ] Auto Map fails clearly when usable source or target weighted meshes are unavailable.
- [ ] Auto Map does not fall back to bone-position-only matching.
- [ ] Auto Map compares weighted source regions against weighted target regions in normalized comparison space.
- [ ] First-version scoring uses geometry/weight signals and does not use hierarchy, IK/FK semantics, body-part classification, or target bone direction as primary evidence.
- [ ] Auto Map only writes candidates that pass the internal acceptance condition.
- [ ] Auto Map does not force every target channel to map to a source.
- [ ] Matched target channels follow latest-assignment-wins.
- [ ] Ownership changes do not clear target pose when the target remains in the Mapping Table.
- [ ] Auto Map does not run Target Calibration or create a target calibration requirement flag.

## Blocked by

- Capture and Re-Enter Work Pose
- Author Source-First Mapping Table Manually
- Clear Live Preview and Removed Target Link Cleanup
