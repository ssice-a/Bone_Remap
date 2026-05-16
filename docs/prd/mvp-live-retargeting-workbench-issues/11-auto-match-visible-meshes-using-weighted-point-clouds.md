# Auto Match Visible Meshes Using Weighted Point Clouds

Label: `ready-for-agent`

## What to build

Add the first **Auto Match Visible Meshes** command. It reads the Active Retarget Profile, uses the explicit Auto Match Mesh Scope, builds weighted source/target point clouds from the currently visible mesh geometry, runs target-side seam clustering, and writes accepted matches into the Mapping Table through normal Target Assignment Operation semantics.

This slice should be demoable by visually posing or arranging source and target meshes, running auto match, getting matched target channels assigned into source rows, and leaving unmatched targets available for manual cleanup.

## Acceptance criteria

- [ ] Auto Match reads source and target mesh sets from the active profile's Auto Match Mesh Scope.
- [ ] Auto Match fails clearly when usable source or target weighted meshes are unavailable.
- [ ] Auto Match uses current visible evaluated source and target mesh geometry.
- [ ] Auto Match may pause Live Preview and clear previous Live Matrix Write results before sampling target geometry.
- [ ] Usable vertex-group weight data requires exact vertex-group-name to bone-name matches and nonzero weight above the project epsilon.
- [ ] Auto Match does not fall back to bone-position-only matching.
- [ ] Auto Match builds source candidates from visible source weighted point clouds.
- [ ] Auto Match builds target regions from visible target weighted point clouds.
- [ ] Auto Match performs target-side seam clustering before point-cloud matching.
- [ ] Target seam clustering only joins target channels through duplicate seam vertices with matching positions and matching weights.
- [ ] Auto Match does not use hierarchy, IK/FK semantics, body-part classification, target bone direction, or target bone positions as matching evidence.
- [ ] Auto Match overwrites the current Mapping Table with the visible weighted-geometry result.
- [ ] Matched target channels follow latest-assignment-wins.
- [ ] Ownership changes do not clear target pose when the target remains in the Mapping Table.
- [ ] Auto Match does not run Target Calibration or create a target calibration requirement flag.

## Blocked by

- Author Source-First Mapping Table Manually
- Clear Live Preview and Removed Target Link Cleanup
