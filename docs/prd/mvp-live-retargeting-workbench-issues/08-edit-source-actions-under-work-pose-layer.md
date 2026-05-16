# Edit Source Actions Under Work Pose Layer

Label: `ready-for-agent`

## What to build

Add **Source Actions** management and automatic **Source Action Edit Context** so users can edit the active Motion Clip's Motion Action while viewing the same Final Visible Pose that drives Live Retargeting. Bone Remap should set up the correct active Motion Action, Work Pose Layer, and Blender-native keying/tweak context when a Source Action is selected.

This slice should be demoable by selecting a Source Action, pressing `I` or using auto-keying on source-side bones or rig controls, and seeing the active Motion Action receive Blender-native keyframes while the target follows through Live Preview.

## Acceptance criteria

- [ ] Selecting a Source Action establishes Source Action Edit Context automatically; there is no separate motion edit button.
- [ ] Source Action Edit Context writes user edits to the active Motion Clip's Motion Action by default.
- [ ] Users can create, duplicate, or add a Source Action before manual keying when no active Motion Action exists.
- [ ] Source Action Edit Context runs under the active Work Pose Layer.
- [ ] Pressing `I`, auto-keying, and Blender keying sets follow Blender Native Keying behavior.
- [ ] Bone Remap does not define a transform-only keying subset.
- [ ] Target Armature keyframes are outside the retarget correction workflow and can be overwritten by live pose writes.
- [ ] Users can duplicate a Motion Action before editing when preserving the original matters.

## Blocked by

- Capture and Re-Enter Work Pose
- Run Live Preview for the Active Retarget Profile
