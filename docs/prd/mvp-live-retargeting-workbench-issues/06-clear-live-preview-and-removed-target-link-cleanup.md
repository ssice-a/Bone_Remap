# Clear Live Preview and Removed Target Link Cleanup

Label: `ready-for-agent`

## What to build

Track **Last Live Written Channels** and implement **Clear Live Preview** plus automatic **Removed Target Link Cleanup**. Clear resets B-side live pose residue to target bind/rest without touching A, Work Pose, Motion Action, Mapping Table, target edit bones, or target bind matrices.

This slice should be demoable by live-writing target channels, clearing them, deleting a Target Link, and confirming only the affected B-side pose channels return to bind/rest.

## Acceptance criteria

- [ ] Live Matrix Write records Last Live Written Channels for the Active Retarget Profile.
- [ ] Clear Live Preview resets Last Live Written Channels to target bind/rest.
- [ ] If Last Live Written Channels is empty, Clear Live Preview falls back to current mapped Deform Channels.
- [ ] Clear Live Preview does not modify Source Armature, Work Pose, Motion Action, Mapping Table, target edit bones, or Target Bind Matrix values.
- [ ] Deleting or unassigning a Target Link so it leaves the Mapping Table resets that target channel to bind/rest.
- [ ] Moving a target between Mapping Rows does not trigger removed-link cleanup.
- [ ] Removed-link cleanup removes the channel from Last Live Written Channels.

## Blocked by

- Author Source-First Mapping Table Manually
- Run Live Preview for the Active Retarget Profile
