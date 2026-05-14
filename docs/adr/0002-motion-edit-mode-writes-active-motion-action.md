# Motion Edit Mode Writes Active Motion Action

Bone Remap treats **Motion Edit Mode** as the user-facing way to correct a motion while seeing the same **Final Visible Pose** that drives live retargeting. By default, edits are written directly to the active **Motion Action** for the current **Motion Clip**.

**Considered Options**

- Store corrections in a separate correction layer.
- Always duplicate the source action into an editable action.
- Write edits directly to the active Motion Action by default.
- Require users to manually configure Blender's NLA/tweak workflow.
- Let Bone Remap own Motion Edit Mode setup and teardown.
- Apply Work Pose Layer through per-frame pose handlers.
- Apply Work Pose Layer through Blender-native animation layering when possible.
- Reimplement Blender animation layer combination in Bone Remap matrix math.
- Treat Blender's evaluated animation layer result as the source of truth.

**Consequences**

- The action being edited is clear: the active Motion Clip's Motion Action.
- Work Pose remains long-lived calibration data and is not used as a per-motion correction layer.
- Work Pose Layer belongs to the Retarget Profile, not to a Motion Clip.
- Motion fixes are action-specific because they are written to the Motion Action.
- Motion Edit Mode runs under the active Work Pose Layer so users edit the same Final Visible Pose that drives live retargeting.
- Preserving an original imported action is an explicit user choice: duplicate the Motion Action before editing.
- Bone Remap owns entering and exiting Motion Edit Mode; users should not need to manually manage Blender NLA/tweak state.
- The implementation may use Blender's NLA tweak behavior internally when it is the best fit for editing the Motion Action while viewing the Final Visible Pose.
- Bone Remap should prefer Blender-native animation layering for Work Pose Layer over per-frame pose handlers.
- Per-frame pose handlers remain a fallback for behavior that cannot be represented cleanly through native animation layering.
- Bone Remap should not define a separate matrix order for combining Work Pose Layer and Motion Action when Blender-native animation layering can produce the visible result.
- The evaluated Blender result is the source of truth for live retargeting and bake.
- Bake samples the same visible result that Motion Edit Mode lets the user inspect and adjust.
