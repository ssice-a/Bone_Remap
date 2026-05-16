# Source Action Selection Establishes Edit Context

Bone Remap does not expose a separate user-facing motion edit button in the first animation module design. Selecting a **Source Actions** row makes that action the **Active Source Action** and automatically establishes **Source Action Edit Context** for playback, keying, live retargeting, and default bake range selection.

**Considered Options**

- Store corrections in a separate correction layer.
- Always duplicate the source action into an editable action.
- Write edits directly to the active Motion Action by default.
- Require users to press an explicit Motion Edit button before keying motion.
- Establish edit context automatically when selecting a Source Action.
- Require users to manually configure Blender's NLA/tweak workflow.
- Let Bone Remap maintain the active Motion Action and Work Pose Layer context.
- Restrict manual keying to transform channels managed by Bone Remap.
- Follow Blender's native key insertion, auto-keying, keying set, and tweak behavior.
- Let users key the Target Armature as a retarget correction path.
- Keep retarget correction keyframes source-side.
- Apply Work Pose Layer through per-frame pose handlers.
- Apply Work Pose Layer through Blender-native animation layering when possible.
- Reimplement Blender animation layer combination in Bone Remap matrix math.
- Treat Blender's evaluated animation layer result as the source of truth.

**Consequences**

- The action being edited is clear: the selected Source Action's Motion Action.
- Work Pose Edit Mode remains explicit because it edits long-lived calibration data and must be isolated from motion playback.
- Motion editing has no separate Edit button; selecting a Source Action is enough.
- Work Pose remains long-lived calibration data and is not used as a per-motion correction layer.
- Work Pose Layer belongs to the Retarget Profile, not to a Motion Clip.
- Motion fixes are action-specific because they are written to the Motion Action.
- Manual keyframes and auto-inserted keyframes are written to the Active Source Action.
- Manual keyframing requires an Active Source Action; users create, duplicate, or add one before keying.
- Source Action Edit Context runs under the active Work Pose Layer so users edit the same Final Visible Pose that drives live retargeting.
- Pressing `I`, using auto-keying, or using Blender keying sets follows Blender's native keying behavior; Bone Remap does not define a transform-only keying subset.
- Bone Remap's responsibility is to maintain the correct active Motion Action and Work Pose Layer context before Blender writes keyframes.
- Manual keyframing targets source-side bones or rig controls under the Work Pose Layer, not the Target Armature.
- Target Armature keyframes are outside the retarget correction workflow and can be overwritten by live retargeting pose writes.
- Preserving an original imported action is an explicit user choice: duplicate the Motion Action before editing.
- The implementation may use Blender's NLA tweak behavior internally when it is the best fit for editing the Motion Action while viewing the Final Visible Pose.
- Bone Remap should prefer Blender-native animation layering for Work Pose Layer over per-frame pose handlers.
- Per-frame pose handlers remain a fallback for behavior that cannot be represented cleanly through native animation layering.
- Bone Remap should not define a separate matrix order for combining Work Pose Layer and Motion Action when Blender-native animation layering can produce the visible result.
- The evaluated Blender result is the source of truth for live retargeting and bake.
- Bake samples the same visible result that Source Action Edit Context lets the user inspect and adjust.
- If the active Motion Action has no usable effective frame range, Bake requires an explicit range override rather than falling back to the scene timeline.
