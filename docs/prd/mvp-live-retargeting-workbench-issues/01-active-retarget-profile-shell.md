# Create Active Retarget Profile Shell

Label: `ready-for-agent`

## What to build

Build the first usable **Retargeting Workbench** shell around one **Active Retarget Profile**. Users can choose a **Source Armature** and **Target Armature**, store them in project state, and have core commands read from the active profile instead of transient Blender selection.

This slice should be demoable by creating a profile, assigning source/target armatures, switching the active profile, and seeing validation/reporting for missing or invalid profile references.

## Acceptance criteria

- [ ] Users can create or select one Active Retarget Profile.
- [ ] Users can assign one Source Armature and one Target Armature to the profile.
- [ ] The profile persists as Project Retarget State in the Blender file.
- [ ] Core command entrypoints read source/target objects from the Active Retarget Profile, not current selection.
- [ ] Switching Active Retarget Profile changes future core command context without clearing any target pose.
- [ ] Basic profile validation reports missing or invalid source/target armature references.

## Blocked by

None - can start immediately.
