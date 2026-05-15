# Edit Motion Actions Under Work Pose Layer

Label: `ready-for-agent`

## What to build

Add **Motion Edit Mode** so users can edit the active Motion Clip's Motion Action while viewing the same Final Visible Pose that drives Live Retargeting. Bone Remap should set up the correct active Motion Action, Work Pose Layer, and Blender-native keying/tweak context.

This slice should be demoable by entering Motion Edit Mode, pressing `I` or using auto-keying on source-side bones or rig controls, and seeing the active Motion Action receive Blender-native keyframes while the target follows through Live Preview.

## Acceptance criteria

- [ ] Motion Edit Mode writes user edits to the active Motion Clip's Motion Action by default.
- [ ] If no active Motion Action exists, Motion Edit Mode creates or assigns an empty Motion Action before accepting manual keyframes.
- [ ] Motion Edit Mode runs under the active Work Pose Layer.
- [ ] Pressing `I`, auto-keying, and Blender keying sets follow Blender Native Keying behavior.
- [ ] Bone Remap does not define a transform-only keying subset.
- [ ] Target Armature keyframes are outside the retarget correction workflow and can be overwritten by live pose writes.
- [ ] Users can duplicate a Motion Action before editing when preserving the original matters.

## Blocked by

- Capture and Re-Enter Work Pose
- Run Live Preview for the Active Retarget Profile
