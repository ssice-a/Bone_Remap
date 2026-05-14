# Source Compensation Is Split Around Source Evaluation

Bone Remap separates source-side compensation by whether Blender's source rig evaluation must see it. Constraints, IK, drivers, and rig controls are evaluated between input-side compensation and output-side retarget delta measurement.

**Considered Options**

- Treat Work Pose as one undifferentiated compensation layer.
- Apply all compensation after source rig evaluation.
- Apply all compensation before source rig evaluation.
- Split compensation into input-side rig conditions, output-side retarget baseline, and action-basis compensation for rest-basis changes.
- Ask users to manually choose input compensation or output compensation for each Work Pose edit.
- Use automatic Work Pose classification based on whether the changed source channel is read by source rig evaluation.
- Allow explicit classification overrides for wrong or ambiguous automatic results.
- Hide ambiguous classification decisions from the user.
- Report ambiguous source channels for review.
- Block Work Pose saving when source channels are ambiguous.
- Allow Work Pose saving and default ambiguous channels to Output Compensation.
- Treat ordinary FK Work Pose changes as target-only offsets.
- Treat Work Pose as a source-visible calibration layer during normal playback.

**Consequences**

- Adjustments that must influence source IK or constraints are Input Compensation.
- IK target placement, pole target placement, rig control placement, solver switches, and driven source properties belong on the input side.
- Output Compensation is measured from the evaluated source pose after source animation, IK, constraints, and rig controls have produced the Final Visible Pose.
- Output Compensation is still source-visible through the Work Pose layer; "output" describes where the retarget baseline is measured, not whether the source armature sees it.
- Work Pose produces a source-visible layer that is active during normal source playback and motion editing.
- Live retargeting reads the same evaluated source pose the user sees in Blender.
- Live retargeting does not read raw Motion Action channels directly.
- Bone Remap relies on Blender's evaluated animation layer result instead of reimplementing animation layer combination order.
- Work Pose Matrices are output-side retarget baselines, not a replacement for source rig input changes.
- Work Pose stores full-source evaluated matrices as output-side baselines.
- Work Pose also stores pose transforms for changed source solver inputs so they can be replayed before source rig evaluation.
- Input Compensation Transforms are additive to the animated source solver input result; they do not replace the original solver-input animation.
- FK bones that keep their local rest basis usually need output-side retarget baseline compensation, but their Work Pose changes remain visible in source playback through the Work Pose layer.
- First-pass Work Pose editing does not modify source edit-mode bones, so Action Basis Compensation is outside the first design.
- If a future feature changes a source edit bone's local direction, roll, or local basis, existing Motion Actions require Action Basis Compensation to preserve their intended motion.
- Users edit one Work Pose; Bone Remap classifies changes automatically instead of asking users to choose a compensation layer.
- Saving Work Pose runs classification, stores compensation data, and updates the classification report.
- Automatic classification is based on whether the changed source channel is a source solver input. Solver inputs become Input Compensation; ordinary FK or mapped source bone pose transforms become Output Compensation.
- Classification overrides can force Input Compensation or Output Compensation for a source channel when automatic classification is wrong or ambiguous.
- Classification overrides are advanced settings and are not required for the normal Work Pose editing flow.
- Standard IK target and pole target relationships, including simple MMD-style IK constraints, can be classified automatically when those relationships are explicit in source constraints.
- Ambiguous source channels are reported instead of silently guessed.
- Work Pose saving can succeed with ambiguous source channels.
- Ambiguous source channels default to Output Compensation until the user resolves them.
- Target Deform Channels receive the solved output and do not participate in source constraint evaluation.
