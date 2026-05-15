# Capture and Re-Enter Work Pose

Label: `ready-for-agent`

## What to build

Add **Work Pose Edit Mode** for creating and editing the source-side **Work Pose** on the visible **Source Armature**. Saving Work Pose captures full evaluated source matrices for the full visible source scope and stores them on the Active Retarget Profile.

This slice should be demoable by entering Work Pose Edit Mode, posing source controls, saving Work Pose, leaving edit mode, then re-entering from the saved Work Pose.

## Acceptance criteria

- [ ] Work Pose Edit Mode starts from Source Rest Pose when no Work Pose exists.
- [ ] Work Pose Edit Mode starts from the saved Work Pose when one exists.
- [ ] Work Pose Edit Mode is isolated from the active Motion Clip and Motion Action.
- [ ] Saving Work Pose stores full evaluated Work Pose Matrices for the full visible Source Armature.
- [ ] Work Pose storage is independent of the current Mapping Table.
- [ ] Resetting Work Pose back to Source Rest Pose requires an explicit user action.
- [ ] Source edit-mode bones are not modified by this workflow.

## Blocked by

- Create Active Retarget Profile Shell
