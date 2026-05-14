# Source Control Frames Drive Target Deform Channels

Bone Remap treats **Work Pose** as the source-side control baseline: each source bone's **Control Frame** defines the pivot and basis used to measure motion delta. Target bones are treated as **Deform Channels** that preserve the target mesh binding and receive solved matrices, even when their rest directions are arbitrary, instead of treating the target armature as the semantic animation skeleton.

**Considered Options**

- Calibrate target bones as the semantic source of pivot and basis.
- Use source **Control Frames** as the semantic source of pivot and basis, and write the resulting solved matrices into target **Deform Channels**.
- Preserve target armature hierarchy in the first solver.
- Normalize mapped target bones into a parentless **Deform Channel Rig** for the first solver.
- Duplicate the target armature before normalization.
- Normalize the active target armature in place.

**Consequences**

- Retarget correctness depends on Work Pose calibration quality.
- The realtime workflow is WYSIWYG relative to the visible evaluated Source Armature; Bone Remap does not use a hidden intermediate skeleton as the real control surface.
- Work Pose calibration must be visible on the Source Armature because those visible Control Frames are the pivots users inspect while driving the Target Armature.
- Work Pose editing must show the target response live so calibration can be judged by target deformation, not only by source pose appearance.
- Work Pose editing shows only target feedback from the current Work Pose edit state; it does not play source motion or baked target actions.
- After Work Pose is saved, normal source playback remains under the source-visible Work Pose layer.
- After Work Pose is saved, Bone Remap returns to normal preview: the active Motion Action plays under Work Pose Layer and drives the target live.
- Work Pose editing does not play or evaluate the active Motion Action; it starts from Source Rest Pose or the saved Work Pose.
- Entering Work Pose Edit Mode captures a temporary Work Pose Edit Snapshot; saving compares the current edit state against that snapshot to detect changed source channels without user marking.
- Work Pose is captured from the visible evaluated Source Armature after editing Work Pose; users may use pose rotation, pose scale, IK controls, rig controls, and constraints to place the visible Control Frames.
- Work Pose Edit Mode allows editing the full visible Source Armature, not only source bones currently present in the Mapping Table, because mapping may still be wrong during calibration.
- Source rest/edit bones are not modified by the first Work Pose design.
- Work Pose editing uses pose-mode visible source controls and automatic classification rather than edit-mode bone changes.
- Work Pose stores full evaluated pose matrices for the full visible Source Armature, including translation, rotation, and scale, so mapping can be authored and debugged after calibration.
- Work Pose matrix storage is independent of the current Mapping Table; later mapping edits can reuse already-saved source baselines without recapturing Work Pose.
- Work Pose stores source solver input pose transforms separately from evaluated pose matrices.
- Input Compensation storage is sparse: only changed Source Solver Inputs are saved as Input Compensation Transforms; ordinary output-only bones rely on full-source Work Pose matrices instead.
- Saving Work Pose classifies edited source channels before returning to normal preview.
- Work Pose matrices affect retarget delta measurement but do not modify the Motion Action by themselves.
- Live Retargeting is the normal unbaked preview path: during playback the Target Armature shows the current retargeted result before any Bake output exists.
- Live Retargeting writes solved full matrices to mapped Deform Channels; it does not author target action channels during preview.
- Bake records the visible target result produced by Live Retargeting into location, rotation, and scale action channels.
- Target bone rest direction is not assumed to be meaningful.
- The first solver should transfer full matrix deltas, not rotation-only values.
- Runtime solve should not continuously edit target rest bones; target head positions may be updated only by an explicit Channel Alignment calibration command, followed by bind refresh.
- Runtime solve uses each mapped Deform Channel's Target Bind Matrix as the target base.
- Channel Alignment, when used, directly changes target edit-mode bone placement; it does not create a separate hidden target application base.
- Channel Alignment is optional visual alignment; retarget correctness does not require target heads to match source Control Frame pivots.
- When Channel Alignment is used, it aligns target heads only; target length, roll, constraints, and parent hierarchy are not part of the first retargeting model.
- First-pass target bones are normalized into independent channels; original target hierarchy restoration or projection is a separate future feature area.
- Channel Normalization modifies the active target armature directly instead of creating a duplicate rig, keeping the workflow shorter and the core state simpler.
- Channel Normalization only touches mapped target bones referenced by the mapping table.
- The primary Target Calibration path runs normalization and target bind refresh; optional Channel Alignment is a separate command.
- Live retargeting requires Target Channels Ready: mapped target bones must be normalized into independent Deform Channels and target bind/reference data must be refreshed before realtime solve runs.
- Bone Remap's first solver deliberately does not support realtime solving through the original target hierarchy.
- Target Calibration is in-place and limited to mapped Target Links; it must not modify unmapped target bones.
- Bone Remap supports one-to-many source-to-target mapping, but not many-to-one target mapping.
- One Deform Channel may have at most one Target Assignment.
- When a Deform Channel is assigned again, the latest assignment wins and replaces the previous mapping.
- The mapping table is the live distribution rule: runtime retargeting reads current Mapping Rows and Target Links and distributes solved source matrices accordingly.
- Mapping table changes affect the next solve and do not require recapturing Work Pose.
- Target Calibration is repeatable and synchronizes mapped target bones into independent Deform Channels with refreshed target bind/reference data.
- Target Calibration is a target-bone structure synchronization tool, not a semantic mapping correctness check.
- Mapping edits affect live distribution immediately; target bones newly introduced by the mapping may require Target Calibration before they are reliable Deform Channels.
- Live retargeting uses overwrite writes: mapped Deform Channels are solved from target bind/reference each frame instead of accumulating on the current target pose.
- Live retargeting does not read existing target animation or target pose as input; motion corrections belong on the source side and are written to the active Motion Action by default.
- Live retargeting reads Blender's evaluated visible source pose, not raw source action channels.
- Live retargeting solves in each armature's own object space; source and target object transforms do not define retarget motion.
- Live retargeting transfers full matrix delta from Work Pose to current evaluated source pose, not rotation-only values.
- Live retargeting measures delta from the saved Work Pose matrices to the current evaluated visible source pose so Work Pose is not double-applied to the target.
- MVP one-to-many mapping uses shared source delta: one Mapping Row computes one full matrix delta, and each Target Link applies that delta to its own target bind/reference.
- MVP excludes per-target weighted follow and per-target driver rules; those remain future advanced features.
- Bake samples the current target-side visible live retargeting result frame by frame and writes it to a Target Armature action; it is not a separate retargeting algorithm and does not recompute retargeting directly from the source Motion Action.
- Bake defaults to the active Motion Action's effective frame range; scene or custom frame ranges require an explicit range override.
- Bake samples every integer frame in the bake range by default; source keyframe-only sampling is not sufficient for correctness because the visible result may include Work Pose, constraints, IK, drivers, and live retargeting.
- Curve simplification may be added later as an optional post-process, but it is not part of the first correctness path.
- Bake writes each mapped Deform Channel's sampled target-side pose transform as location, rotation, and scale by default; source actions that contain only rotation keys still bake the complete target result.
- Sparse omission of default or unchanged location/scale channels may be added later as an optimization, but it must preserve the same visible baked result.
- Bake writes rotation using each target pose bone's current rotation mode; it does not force a global baked rotation representation by default.
- Bake creates a new Baked Target Action by default; overwriting an existing target action requires an explicit user choice.
- Bake writes only mapped Deform Channels from the current Mapping Table; unmapped target bones are not written, cleared, inferred, or compensated.
- When overwriting an existing target action, Bake replaces prior keys only inside the current mapped Deform Channel scope and bake frame range; keys outside that scope or range are left unchanged.
- Optional Channel Alignment requires a captured Work Pose, because target heads align to source Control Frame pivots.
