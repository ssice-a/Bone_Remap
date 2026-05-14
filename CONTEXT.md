# Bone Remap Context

Bone Remap is a Blender add-on for non-destructive realtime bone retargeting between user-provided armatures. This glossary defines the product language used when discussing retargeting behavior.

## Language

**Retargeting Workbench**:
The product experience where a **Source Armature**'s **Final Visible Pose** drives a **Target Armature** in realtime, with **Bake** as an optional output step.
_Avoid_: Offline action converter, bridge rig pipeline

**Source Armature**:
The user-provided armature whose visible evaluated pose is used as the control input for retargeting.
_Avoid_: Hidden retarget rig, separate control skeleton

**Source Rest Pose**:
The neutral source-side pose used as the starting point for editing **Work Pose**.
_Avoid_: Current animation frame, Motion Clip pose

**Target Armature**:
The user-provided armature whose pose is driven by retargeting while preserving its existing mesh binding.
_Avoid_: Export rig, child rig

**Target Binding**:
The existing relationship between a **Target Armature** and its mesh weights that Bone Remap must preserve.
_Avoid_: Rebinding, weight transfer

**Target Bind Matrix**:
The target-side bind/reference matrix used as the base for solving a **Deform Channel**.
_Avoid_: Hidden target application frame, source pivot copy

**Target Bind Refresh**:
An explicit update of target-side bind/reference matrices after calibration changes the **Deform Channel** rest setup.
_Avoid_: Retarget solve, source pivot alignment

**Retarget Profile**:
The long-lived calibration record for one **Source Armature** to **Target Armature** pairing.
_Avoid_: Motion clip, temporary session

**Project Retarget State**:
The current working state for a **Retarget Profile** inside the active Blender project.
_Avoid_: Reusable preset, exported template, runtime cache

**Retarget Preset**:
An explicit reusable import/export record made from all or part of a **Retarget Profile**.
_Avoid_: Current working state, automatic project save, Motion Action, animation library

**Bone Name Reference**:
A preset-side reference to a source or target bone by its Blender bone name.
_Avoid_: Stable custom bone ID, implicit bone order, vertex group index

**Missing Bone Reference**:
A **Bone Name Reference** that cannot be resolved on the current **Source Armature** or **Target Armature** during preset import.
_Avoid_: Auto-guessed bone, silently dropped mapping

**Preset Import Report**:
The import result that tells the user which **Bone Name References** were resolved and which became **Missing Bone References**.
_Avoid_: Silent import, automatic fuzzy match

**Preset Import**:
Applying a **Retarget Preset** to the current **Project Retarget State** by replacing the corresponding preset-owned state.
_Avoid_: Merge import, append import, partial overlay

**Work Pose**:
The long-lived source-side calibration pose on the **Source Armature** used as the retargeting baseline for a **Retarget Profile**.
_Avoid_: Per-action correction, target pose, hidden intermediate skeleton

**Work Pose Layer**:
The source-visible calibration layer produced by **Work Pose** and applied during normal source playback.
_Avoid_: Target-only offset, hidden correction layer, per-frame pose handler

**Work Pose Edit Mode**:
The user-facing mode for creating or editing **Work Pose**, isolated from the active **Motion Clip**.
_Avoid_: Motion Edit Mode, editing the current action

**Work Pose Edit Snapshot**:
The temporary source-side state captured when entering **Work Pose Edit Mode** and used during **Work Pose Save** to detect changed source channels.
_Avoid_: User-authored marker, saved Work Pose data, Motion Action data

**Changed Source Channel**:
A source channel whose value differs from the **Work Pose Edit Snapshot** by more than the configured comparison tolerance during **Work Pose Save**.
_Avoid_: Every non-default channel, every mapped source bone, user-selected changed flag

**Work Pose Editable Source Scope**:
The full visible **Source Armature** available for user edits during **Work Pose Edit Mode**.
_Avoid_: Mapping-only edit scope, target-link edit scope, prefiltered source controls

**Live Target Feedback**:
The realtime target response shown while editing **Work Pose** or authoring mappings.
_Avoid_: Motion Action playback, target action playback, offline preview, bake-only validation

**Normal Preview**:
The normal playback state after **Work Pose** has been saved, where the active **Motion Action** plays under the **Work Pose Layer** and drives the target through live retargeting.
_Avoid_: Work Pose Edit Mode, target bake

**Live Retargeting**:
The realtime solve that reads the **Live Evaluated Source Pose** and writes mapped target **Deform Channels** for viewport playback before **Bake**.
_Avoid_: Baked target playback, source action conversion, target action output

**Live Matrix Write**:
The live target-side write where **Live Retargeting** applies solved full matrices to mapped **Deform Channels**.
_Avoid_: Live F-curve write, rotation-only live write, target action authoring

**Work Pose Matrix**:
The full evaluated source pose matrix captured for a **Control Frame**, including translation, rotation, and scale.
_Avoid_: Rotation-only baseline, source action keyframe

**Source Structure Calibration**:
Source-side calibration that changes the source rig conditions used when evaluating source animation.
_Avoid_: Target calibration, target bind refresh, output-only retarget offset

**Source Solver Input**:
A source pose channel, rig control, constraint control, IK target, pole target, switch, or driven property that Blender's source rig evaluation reads before producing the **Final Visible Pose**.
_Avoid_: Target Deform Channel, evaluated output matrix, Work Pose Matrix

**Input Compensation**:
Source-side compensation that must be visible to source animation evaluation, constraints, IK, or rig controls.
_Avoid_: Target matrix solve, post-evaluation retarget delta

**Input Compensation Transform**:
The saved additive pose transform for a **Source Solver Input** captured during **Work Pose Edit Mode** and replayed before source rig evaluation.
_Avoid_: Evaluated source matrix, target bind matrix, retarget output

**Input Compensation Scope**:
The changed **Source Solver Inputs** whose **Input Compensation Transforms** are saved and replayed.
_Avoid_: Full source armature, ordinary FK output bones, mapped source bone list

**Output Compensation**:
Source-visible calibration whose retarget baseline is measured after source animation evaluation and used to map evaluated source motion to target **Deform Channels**.
_Avoid_: IK target offset, source rig condition, action-basis rewrite

**Action Basis Compensation**:
The compensation needed when a source rest/edit bone local basis changes and existing **Motion Actions** must preserve their intended motion under the new basis.
_Avoid_: Work Pose Matrix, target bind matrix, pose-mode correction, first-pass Work Pose edit

**Work Pose Classification**:
The automatic classification of **Work Pose Edit Mode** changes into **Input Compensation** or **Output Compensation** according to whether the changed source channel is a **Source Solver Input**.
_Avoid_: User-selected compensation mode, manual layer picking

**Classification Report**:
The report that shows how Bone Remap classified Work Pose changes and lists ambiguous source channels that need user review.
_Avoid_: Silent classification, hidden rig inference

**Ambiguous Source Channel**:
A changed source channel whose role cannot be confidently classified as a **Source Solver Input** or ordinary output channel.
_Avoid_: Silently guessed source role, blocking save error

**Classification Override**:
A user-authored override that forces a source channel to be classified as **Input Compensation** or **Output Compensation** instead of using automatic classification.
_Avoid_: Per-edit manual classification, hidden automatic guess

**Work Pose Save**:
The operation that captures the edited Work Pose, runs **Work Pose Classification**, stores compensation data, and returns Bone Remap to **Normal Preview**.
_Avoid_: Passive file save, Motion Action keyframe insert

**Control Frame**:
The source-side coordinate frame captured from **Work Pose** that defines the pivot and basis for retargeting motion.
_Avoid_: Target bone direction, arbitrary rest bone

**Deform Channel**:
A target-side bone channel that receives solved pose matrices while preserving the **Target Binding**.
_Avoid_: Control bone, semantic source bone

**Deform Channel Rig**:
A **Target Armature** normalized into independent **Deform Channels** for retargeting and export.
_Avoid_: Original skeleton, semantic hierarchy

**Channel Normalization**:
An explicit in-place calibration operation that detaches mapped target bones into independent **Deform Channels** on the active **Target Armature**.
_Avoid_: Runtime solve, hierarchy retargeting

**Channel Alignment**:
An optional calibration operation that moves **Deform Channel** heads to visually match mapped **Control Frame** pivots.
_Avoid_: Runtime solve, required retarget correctness

**Target Calibration**:
The repeatable operation that synchronizes mapped target bones into independent **Deform Channels** and refreshes their target bind/reference data.
_Avoid_: Mapping correctness check, Work Pose, runtime solve, motion correction

**Target Channels Ready**:
The state where mapped **Deform Channels** have been normalized into independent channels and their target bind/reference data has been refreshed.
_Avoid_: Original target hierarchy, uncalibrated target rig

**Mapping Row**:
One source-side row anchored to a **Control Frame**.
_Avoid_: One-to-one bone pair

**Target Link**:
One configurable mapped **Deform Channel** attached to a **Mapping Row**.
_Avoid_: Hidden target selection, implicit child mapping

**Mapping Table**:
The current distribution rule that tells Bone Remap which source **Control Frames** drive which target **Deform Channels**.
_Avoid_: Calibration result, Work Pose data

**Target Assignment**:
The ownership of one **Deform Channel** by one **Target Link**.
_Avoid_: Many-to-one target mapping, shared target ownership

**Final Visible Pose**:
The evaluated pose of a **Source Armature** after source-side animation and adjustments are applied.
_Avoid_: Raw action, rest pose

**Live Evaluated Source Pose**:
The current **Final Visible Pose** read from Blender evaluation and used as the live retargeting input.
_Avoid_: Raw Motion Action, unevaluated pose channels, target pose

**Blender Layer Evaluation**:
The Blender-native evaluation result of the active **Work Pose Layer**, **Motion Action**, source constraints, IK, drivers, and rig controls.
_Avoid_: Hand-rolled NLA math, manual matrix layer order

**Motion Clip**:
A source-side animation unit that uses one **Motion Action** and owns action-specific settings.
_Avoid_: Retarget profile, baked target action

**Motion Action**:
The Blender Action used by the active **Motion Clip**. User-authored motion edits are written directly to this action by default.
_Avoid_: Hidden correction layer, mandatory action copy, Work Pose

**Motion Edit Mode**:
The Bone Remap-managed mode for editing the active **Motion Clip** while viewing the **Final Visible Pose**.
_Avoid_: Work Pose edit, target calibration, target bake, manual Blender NLA setup

**Source Pose Stack**:
The ordered source-side layers that produce the **Final Visible Pose**.
_Avoid_: Target correction stack, baked output

**Bake**:
An optional output step that records the current retargeted result into a target action.
_Avoid_: Retargeting itself, core runtime

**Bake Source**:
The current visible live retargeted result on the **Target Armature** that **Bake** records.
_Avoid_: Raw source action replay, separate retarget solve, source F-curve conversion

**Baked Target Action**:
The target-side Blender Action produced by **Bake** from the current **Bake Source**.
_Avoid_: Source Motion Action, live retargeting state, Retarget Preset data

**Bake Scope**:
The set of mapped target **Deform Channels** that **Bake** records.
_Avoid_: Whole target armature, unmapped target bones, target cleanup pass

**Bake Range**:
The frame interval that **Bake** samples from the **Bake Source** and writes into a **Baked Target Action**.
_Avoid_: Whole timeline by accident, implicit scene lifetime

**Bake Range Override**:
An explicit user-selected frame interval that replaces the default **Bake Range**.
_Avoid_: Accidental scene timeline bake, hidden range expansion

**Bake Sampling**:
The frame-by-frame capture of the **Bake Source** inside the **Bake Range**.
_Avoid_: Source keyframe-only sampling, curve simplification as correctness path

**Bake Curve Simplification**:
An optional post-process that may reduce baked key density after **Bake Sampling**.
_Avoid_: Default bake behavior, retarget correctness requirement

**Baked Deform Channel Transform**:
The target-side pose transform recorded for one **Deform Channel** during **Bake**, derived from the current visible target pose and written as location, rotation, and scale.
_Avoid_: Source action channel set, rotation-only bake, source F-curve copy

**Baked Rotation Mode**:
The rotation representation used when writing a **Baked Deform Channel Transform**, taken from the target pose bone's current rotation mode.
_Avoid_: Forced quaternion bake, source rotation mode, global bake rotation mode

**Bake Overwrite**:
The explicit user-selected mode where **Bake** writes into an existing target action by replacing prior keys only inside the current **Bake Scope** and **Bake Range**.
_Avoid_: Clear target action, overwrite all target bones, delete unmapped animation

**Overwrite Retargeting**:
The runtime write strategy where mapped **Deform Channels** are solved from target bind/reference each frame instead of accumulating on the current target pose.
_Avoid_: Additive target correction, target pose layering

**Armature Object Space Solve**:
The solve convention where source and target bone matrices are interpreted in their own armature object spaces rather than world space.
_Avoid_: World-space retargeting, object-transform-driven fitting

**Full Matrix Delta**:
The source motion delta measured as a complete matrix difference from **Work Pose Matrix** to **Live Evaluated Source Pose**.
_Avoid_: Rotation-only retargeting

**Shared Source Delta**:
The one-to-many distribution rule where one **Mapping Row** computes one **Full Matrix Delta** and all of its **Target Links** receive that same delta against their own target bind/reference.
_Avoid_: Per-target weighted follow, per-target driver rule

## Relationships

- A **Retargeting Workbench** has exactly one active **Source Armature** and one active **Target Armature**.
- A **Retarget Profile** belongs to one **Source Armature** and **Target Armature** pairing.
- A **Retarget Profile** is stored as **Project Retarget State** by default.
- **Project Retarget State** keeps the current working setup for the active Blender project.
- A **Retarget Preset** is created explicitly when the user wants reusable data outside the current project.
- A **Retarget Preset** may contain a full **Retarget Profile** or selected reusable parts such as **Mapping Table** or **Work Pose** data.
- A **Retarget Preset** does not contain **Motion Action** data by default.
- A **Retarget Preset** describes how a source-target pair is retargeted, not which animation clip is being played.
- A **Retarget Preset** uses **Bone Name References** to restore source and target bone mappings.
- Importing a **Retarget Preset** may partially resolve its **Bone Name References**.
- A **Missing Bone Reference** does not participate in live retargeting until the user resolves it.
- Preset import produces a **Preset Import Report** instead of silently guessing unmatched bones.
- Bone Remap does not fuzzy-match **Bone Name References** during preset import by default.
- **Preset Import** replaces the current **Mapping Table** with the preset's **Mapping Table**.
- **Preset Import** does not merge imported mappings with the existing **Mapping Table**.
- If **Preset Import** produces **Missing Bone References**, old mappings are not kept as fallback mappings.
- A **Retarget Profile** owns one active **Work Pose**.
- A **Retarget Profile** owns the **Work Pose Layer** produced from its **Work Pose**.
- **Work Pose** and **Work Pose Layer** are long-lived retarget calibration data, not **Motion Clip** data.
- A **Work Pose** defines **Control Frames** for source-side retargeting.
- A **Work Pose** produces a **Work Pose Layer**.
- A **Work Pose Layer** is active during normal source playback after Work Pose has been saved.
- A **Work Pose Layer** participates in the **Final Visible Pose**.
- Bone Remap owns **Work Pose Layer** setup and teardown.
- After saving **Work Pose**, Bone Remap returns to **Normal Preview**.
- The visible evaluated **Source Armature** is the user-facing control surface for retargeting.
- Bone Remap's realtime workflow is WYSIWYG relative to the **Source Armature**, not a hidden intermediate skeleton.
- **Live Retargeting** is the normal unbaked preview path.
- **Live Retargeting** lets the **Target Armature** show the current retargeted result during playback without requiring **Bake**.
- **Live Retargeting** uses **Live Matrix Write** for mapped **Deform Channels**.
- **Live Matrix Write** applies the solved full matrix result; it does not author target action channels.
- **Bake** converts the current visible target result into keyable action channels after **Live Retargeting** has produced it.
- **Work Pose** calibration must be visible on the **Source Armature** because those visible **Control Frames** are the pivots users inspect while driving the **Target Armature**.
- **Work Pose Edit Mode** starts from **Source Rest Pose** when no **Work Pose** has been saved.
- **Work Pose Edit Mode** starts from the saved **Work Pose** when one exists.
- Entering **Work Pose Edit Mode** captures a **Work Pose Edit Snapshot**.
- Resetting **Work Pose** back to **Source Rest Pose** requires an explicit user command.
- **Work Pose Edit Mode** is isolated from the active **Motion Clip** and **Motion Action**.
- **Work Pose Edit Mode** does not play or evaluate the active **Motion Action**.
- **Work Pose Edit Mode** uses the full **Work Pose Editable Source Scope**.
- **Work Pose Editable Source Scope** is not limited to source bones currently present in the **Mapping Table**.
- Users may edit source bones before their mapping has been finalized so mapping mistakes can be discovered through **Live Target Feedback**.
- **Work Pose Edit Mode** shows **Live Target Feedback** from the current edited **Work Pose** state.
- **Live Target Feedback** during **Work Pose Edit Mode** does not come from the active **Motion Action** or a **Baked Target Action**.
- **Work Pose** is captured from the visible evaluated **Source Armature** after editing **Work Pose**.
- **Work Pose Edit Mode** may use source pose rotation, pose scale, IK controls, rig controls, and constraints to place visible **Control Frames**.
- **Work Pose Edit Mode** does not modify the source rest skeleton.
- **Work Pose Edit Mode** does not modify source edit-mode bones in the first design.
- **Work Pose** stores **Work Pose Matrices** for the full visible **Source Armature**.
- **Work Pose** stores **Work Pose Matrices** for source bones even when they are not currently used by the **Mapping Table**.
- Later **Mapping Table** edits can use already-saved **Work Pose Matrices** without recapturing **Work Pose**.
- **Work Pose** stores **Input Compensation Transforms** for changed **Source Solver Inputs**.
- The **Input Compensation Scope** contains only changed **Source Solver Inputs**.
- The **Input Compensation Scope** is sparse; it does not mirror the full-source **Work Pose Matrix** storage.
- Ordinary FK or output-only source bones are not stored as **Input Compensation Transforms** unless they are also **Source Solver Inputs**.
- Unchanged **Source Solver Inputs** are not stored as **Input Compensation Transforms**.
- A **Work Pose Matrix** changes how source motion delta is measured for retargeting.
- A **Work Pose Matrix** does not modify the **Motion Action** by itself.
- An **Input Compensation Transform** is added to the animated result of its **Source Solver Input** before source rig evaluation.
- An **Input Compensation Transform** does not replace the original animated solver-input motion.
- **Source Structure Calibration** changes what source animation evaluation sees before producing the **Final Visible Pose**.
- **Input Compensation** is used for source adjustments that constraints, IK, drivers, or rig controls must see.
- **Output Compensation** is used after source animation evaluation to compute retarget motion from the evaluated source pose.
- Changing IK targets, pole targets, rig controls, solver switches, or driven source properties is **Input Compensation**.
- Pose-mode calibration transforms on ordinary FK or mapped source bones are **Output Compensation** unless those channels are **Source Solver Inputs**.
- **Output Compensation** is not target-only; ordinary FK Work Pose changes remain visible through the **Work Pose Layer** during source playback.
- **Work Pose Classification** is automatic; users do not choose whether a Work Pose change is input-side or output-side.
- Standard IK target and pole target relationships can be classified automatically when they are visible in source constraints.
- A **Classification Report** exposes ambiguous channels instead of silently guessing their role.
- **Work Pose Save** runs **Work Pose Classification** before returning to **Normal Preview**.
- **Work Pose Save** detects **Changed Source Channels** by comparing the current edit state against the **Work Pose Edit Snapshot**.
- Users do not manually mark **Changed Source Channels**.
- Existing non-default source values are not treated as **Changed Source Channels** unless they changed during the current **Work Pose Edit Mode** session.
- Channel comparison uses tolerances so floating-point noise does not create accidental **Changed Source Channels**.
- **Work Pose Save** produces or updates the **Classification Report**.
- **Work Pose Save** can succeed with **Ambiguous Source Channels**.
- An **Ambiguous Source Channel** defaults to **Output Compensation** until the user resolves it.
- **Ambiguous Source Channels** are visible in the **Classification Report**.
- Users may add a **Classification Override** when automatic classification is wrong or ambiguous.
- A **Classification Override** is an explicit advanced setting, not part of the normal Work Pose editing flow.
- **Action Basis Compensation** is outside the first Work Pose design because source edit-mode bones are not modified.
- A **Source Armature** provides a **Final Visible Pose** to the retargeting process.
- Live retargeting reads **Live Evaluated Source Pose**, not raw **Motion Action** channels.
- **Live Evaluated Source Pose** includes **Work Pose Layer**, source animation, source constraints, IK, drivers, and rig controls as evaluated by Blender.
- **Live Evaluated Source Pose** is defined by **Blender Layer Evaluation**, not by Bone Remap reimplementing Blender's animation layer math.
- A **Target Armature** is normalized into a **Deform Channel Rig** before first-pass retargeting.
- A **Deform Channel Rig** exposes independent **Deform Channels** that receive the realtime retargeted pose.
- **Channel Normalization** modifies only mapped **Deform Channels** on the active **Target Armature**.
- **Target Bind Refresh** preserves target-side bind/reference data after calibration changes **Deform Channel** rest setup.
- Runtime retargeting uses each mapped **Deform Channel**'s **Target Bind Matrix** as the target base.
- **Channel Alignment** directly modifies target edit-mode bone placement when used; it does not create a separate hidden target base.
- **Target Calibration** runs **Channel Normalization** and **Target Bind Refresh** for all mapped **Target Links**.
- **Target Calibration** produces **Target Channels Ready** for mapped target bones.
- **Target Calibration** does not modify unmapped target bones.
- **Target Calibration** is an in-place calibration of the active **Target Armature**.
- **Target Calibration** is repeatable and synchronizes the active **Target Armature** to the current **Mapping Table**.
- **Target Calibration** is a target-bone structure synchronization tool; it does not validate whether the mapping is semantically correct.
- Changing the **Mapping Table** changes runtime distribution immediately, but target bones newly introduced by the mapping may require **Target Calibration** before they are reliable **Deform Channels**.
- Live retargeting requires **Target Channels Ready**.
- **Channel Alignment** is optional and exists for visual clarity or authoring comfort, not for retarget correctness.
- **Channel Alignment** requires **Work Pose** because **Control Frames** provide the alignment pivots.
- Retargeting does not require **Deform Channel** heads to align with **Control Frame** pivots.
- A **Mapping Row** may own multiple **Target Links**.
- One **Deform Channel** may have at most one **Target Assignment**.
- Bone Remap supports one-to-many source-to-target mapping, but not many-to-one target mapping.
- When a user assigns a **Deform Channel** that already has a **Target Assignment**, the latest assignment wins and replaces the previous mapping.
- The **Mapping Table** is the live distribution rule for retargeting.
- Runtime retargeting reads the current **Mapping Table** and distributes solved source matrices according to its current **Mapping Rows** and **Target Links**.
- Changing the **Mapping Table** changes what Bone Remap distributes on the next solve; it does not require recapturing **Work Pose**.
- Mapping authoring keeps target-side **Deform Channels** visible for explicit addition.
- Unmapped target bones are outside Bone Remap's retargeting, calibration, and bake scope.
- Runtime retargeting writes all mapped **Target Links** and resets those **Deform Channels** to bind/rest before solving.
- Live retargeting uses **Overwrite Retargeting** for mapped **Deform Channels**.
- **Overwrite Retargeting** does not read existing target animation or target pose as input.
- Live retargeting uses **Armature Object Space Solve**.
- Source object transforms and target object transforms do not define retarget motion.
- Live retargeting transfers **Full Matrix Delta** from source **Control Frames** to mapped target **Deform Channels**.
- **Full Matrix Delta** preserves translation, rotation, and scale effects captured by **Work Pose**.
- **Full Matrix Delta** is measured from **Work Pose Matrix** to **Live Evaluated Source Pose** so Work Pose itself is not double-applied to the target.
- Live retargeting uses **Shared Source Delta** for one-to-many mapping.
- In **Shared Source Delta**, one **Mapping Row** computes source motion once, and each **Target Link** applies it to its own target bind/reference.
- Corrections to retargeted motion should be authored on the source side through **Motion Edit Mode**.
- A **Retarget Profile** stores long-lived calibration data; a **Motion Clip** stores action-specific data.
- **Work Pose Layer** belongs to the **Retarget Profile**, not to a **Motion Clip**.
- A **Motion Clip** uses one active **Motion Action**.
- By default, **Motion Edit Mode** writes user edits directly to the active **Motion Action**.
- Users enter and exit **Motion Edit Mode** through Bone Remap controls.
- A user may duplicate a **Motion Action** before editing when preserving the original action matters.
- **Motion Edit Mode** runs under the active **Work Pose Layer**.
- A **Source Pose Stack** combines the **Work Pose Layer** and the active **Motion Action** into the **Final Visible Pose**.
- **Motion Edit Mode** writes user edits to the active **Motion Action**, not to **Work Pose**.
- **Bake** records the visible retargeted result, but does not define the realtime retargeting workflow.
- **Bake** samples the **Bake Source** frame by frame and writes it to a **Target Armature** action.
- The **Bake Source** is the target-side visible result produced by current Live Retargeting.
- **Bake** does not reinterpret source F-curves or bypass **Work Pose**, **Mapping Table**, or Live Retargeting.
- **Bake** does not recompute retargeting directly from the **Motion Action**.
- The default **Bake Range** comes from the active **Motion Action**'s effective frame range.
- Users may set a **Bake Range Override** when they need a scene range or custom frame range.
- **Bake** does not default to the whole scene timeline.
- **Bake Sampling** captures the **Bake Source** on each integer frame inside the **Bake Range** by default.
- **Bake Sampling** does not rely on source **Motion Action** keyframes as the only sampled frames.
- **Bake Curve Simplification** is optional and happens after **Bake Sampling**; it is not part of the correctness path.
- **Bake** records a **Baked Deform Channel Transform** for each channel in the **Bake Scope**.
- A **Baked Deform Channel Transform** is derived from the target-side visible pose, not from the channel set present in the source **Motion Action**.
- A source **Motion Action** containing only rotation keys does not imply rotation-only **Bake** output.
- **Baked Rotation Mode** follows each target pose bone's current rotation mode.
- **Bake** does not force all baked rotations into one global representation by default.
- **Bake** creates a new **Baked Target Action** by default.
- **Bake** does not overwrite an existing target action unless the user explicitly chooses overwrite.
- A **Baked Target Action** is an output artifact, not reusable **Retarget Preset** data.
- The **Bake Scope** contains only mapped **Deform Channels** from the current **Mapping Table**.
- **Bake** writes only channels inside the **Bake Scope**.
- **Bake** does not write, clear, infer, or compensate unmapped target bones.
- **Bake Overwrite** clears old keyframes only inside the current **Bake Scope** and **Bake Range** before writing new baked keyframes.
- **Bake Overwrite** leaves **Bake Scope** channels outside the current **Bake Range** unchanged.
- **Bake Overwrite** leaves all channels outside the **Bake Scope** unchanged.

## Example Dialogue

> **Dev:** "Are we building an offline converter that turns one source action into one target action?"
> **Domain expert:** "No. Bone Remap is a **Retargeting Workbench**: the **Source Armature**'s **Final Visible Pose** drives the **Target Armature** live, and **Bake** is only the optional output step."

> **Dev:** "Can we make the target mesh bind directly to the source skeleton?"
> **Domain expert:** "No. The **Target Binding** must be preserved, so retargeting drives the **Target Armature** instead."

> **Dev:** "If the target bones all point upward, do their directions define how the model moves?"
> **Domain expert:** "No. The **Control Frames** come from **Work Pose**; target bones are **Deform Channels** that receive the solved matrices."

> **Dev:** "Can Bone Remap use a hidden intermediate skeleton as the real control surface?"
> **Domain expert:** "No. The realtime workflow is WYSIWYG relative to the visible evaluated **Source Armature**."

> **Dev:** "Must target bone heads align to source rotation centers for retargeting to work?"
> **Domain expert:** "No. **Control Frames** define the source-side pivots; **Channel Alignment** is only an optional visual alignment command."

> **Dev:** "Should a deep target hierarchy participate in the first retargeting solver?"
> **Domain expert:** "No. **Channel Normalization** turns mapped target bones into a **Deform Channel Rig** so each channel is solved independently."

> **Dev:** "Should normalization create a duplicate rig?"
> **Domain expert:** "No. **Channel Normalization** modifies the active **Target Armature** directly to avoid extra workflow steps."

> **Dev:** "Should Target Calibration always move target bone heads to source pivots?"
> **Domain expert:** "No. **Target Calibration** prepares mapped **Deform Channels** and refreshes target bind data; **Channel Alignment** is a separate optional command."

> **Dev:** "What target-side base does the solver use?"
> **Domain expert:** "It uses the **Target Bind Matrix**. If **Channel Alignment** is used, it directly edits target bone placement and bind data is refreshed."

> **Dev:** "Can live retargeting run before mapped target bones are detached into independent channels?"
> **Domain expert:** "No. Live retargeting requires **Target Channels Ready**, and **Target Calibration** produces that state."

> **Dev:** "Should Target Calibration process the whole target armature?"
> **Domain expert:** "No. It only processes mapped **Target Links** and does not touch unmapped target bones."

> **Dev:** "Can Channel Alignment run before Work Pose exists?"
> **Domain expert:** "No. **Channel Alignment** needs **Control Frames**, and those come from **Work Pose**."

> **Dev:** "When editing Work Pose, should the current Motion Clip stay visible?"
> **Domain expert:** "No. **Work Pose Edit Mode** edits **Work Pose** without the active **Motion Clip**; the first edit starts from **Source Rest Pose**, and later edits start from the saved **Work Pose**."

> **Dev:** "How does Bone Remap know what changed when the user saves Work Pose?"
> **Domain expert:** "It compares the current edit state to the **Work Pose Edit Snapshot** captured when entering Work Pose Edit Mode. The user only edits and saves."

> **Dev:** "Can Work Pose Edit Mode play the active Motion Action?"
> **Domain expert:** "No. **Work Pose Edit Mode** does not play or evaluate the active **Motion Action**; Work Pose remains long-lived calibration, not a captured animation frame."

> **Dev:** "Should Work Pose editing show the target result live?"
> **Domain expert:** "Yes. **Work Pose Edit Mode** shows **Live Target Feedback** so users can judge whether calibration drives the target correctly."

> **Dev:** "During Work Pose editing, should the target play the source motion or a baked action?"
> **Domain expert:** "No. **Work Pose Edit Mode** is isolated from motion playback. The target only shows **Live Target Feedback** from the current Work Pose edit state."

> **Dev:** "Should Work Pose Edit Mode only allow editing currently mapped source bones?"
> **Domain expert:** "No. The **Work Pose Editable Source Scope** is the full visible Source Armature because mapping may still be wrong while calibration is being authored."

> **Dev:** "Can Work Pose calibration use scale or IK controls?"
> **Domain expert:** "Yes. **Work Pose Edit Mode** may use pose scale, IK controls, rig controls, and constraints as long as the visible evaluated **Source Armature** provides the **Control Frames**."

> **Dev:** "Does saving Work Pose scale modify the source animation?"
> **Domain expert:** "No. **Work Pose Matrices** affect retarget delta measurement; they do not write to the **Motion Action** by themselves."

> **Dev:** "Should Work Pose store the whole Source Armature?"
> **Domain expert:** "Yes. **Work Pose** stores **Work Pose Matrices** for the full visible **Source Armature** so mapping can be authored and debugged after calibration."

> **Dev:** "If a source bone is not mapped yet, should Work Pose still save its matrix?"
> **Domain expert:** "Yes. Mapping may change later, so **Work Pose** saves full-source matrices instead of only mapped or edited bones."

> **Dev:** "What data does Work Pose save after automatic classification?"
> **Domain expert:** "It stores full-source **Work Pose Matrices** for output-side baselines and **Input Compensation Transforms** for changed **Source Solver Inputs**."

> **Dev:** "Should Input Compensation be saved for every source bone?"
> **Domain expert:** "No. Full-source storage belongs to **Work Pose Matrix**. **Input Compensation Scope** only contains changed **Source Solver Inputs**."

> **Dev:** "Does an Input Compensation Transform replace the IK controller's original animation?"
> **Domain expert:** "No. It is additive: the original animated solver input remains, and the Work Pose compensation is applied before source rig evaluation."

> **Dev:** "After saving Work Pose, should normal playback still look like it is under Work Pose?"
> **Domain expert:** "Yes. **Work Pose** produces a source-visible **Work Pose Layer**. Normal source playback and motion editing happen under that layer."

> **Dev:** "Does Work Pose Layer belong to the current Motion Clip?"
> **Domain expert:** "No. **Work Pose Layer** belongs to the **Retarget Profile** because it is source-target calibration reused across Motion Clips."

> **Dev:** "What happens after Work Pose is saved?"
> **Domain expert:** "Bone Remap returns to **Normal Preview**: the active **Motion Action** plays under the **Work Pose Layer** and the target follows live."

> **Dev:** "Can the target show the final retargeted result before Bake?"
> **Domain expert:** "Yes. **Live Retargeting** is the normal unbaked preview path; **Bake** only records that visible result into a target action."

> **Dev:** "Does Live Retargeting write target F-curves while previewing?"
> **Domain expert:** "No. Live preview uses **Live Matrix Write**; **Bake** later records the visible target result into action channels."

> **Dev:** "When does Bone Remap classify Work Pose edits?"
> **Domain expert:** "**Work Pose Save** runs **Work Pose Classification**, stores **Input Compensation Transforms** and **Work Pose Matrices**, updates the **Classification Report**, then returns to **Normal Preview**."

> **Dev:** "Can Work Pose Save succeed when some channels are ambiguous?"
> **Domain expert:** "Yes. **Ambiguous Source Channels** default to **Output Compensation** and are listed in the **Classification Report** for user review."

> **Dev:** "Can users override a channel's automatic Work Pose classification?"
> **Domain expert:** "Yes. A **Classification Override** can force **Input Compensation** or **Output Compensation** for a source channel when automatic classification is wrong or ambiguous."

> **Dev:** "Should users manually manage the Work Pose Layer?"
> **Domain expert:** "No. Bone Remap owns **Work Pose Layer** setup and teardown."

> **Dev:** "What does live retargeting read from the source armature?"
> **Domain expert:** "It reads **Live Evaluated Source Pose**, the same evaluated pose visible in Blender, not raw **Motion Action** channels."

> **Dev:** "Should Bone Remap define its own matrix order for combining Work Pose Layer and Motion Action?"
> **Domain expert:** "No. Bone Remap uses **Blender Layer Evaluation** as the source of truth for the visible source result."

> **Dev:** "Are source calibration changes all the same kind of compensation?"
> **Domain expert:** "No. Adjustments that IK or constraints must see are **Input Compensation**. Retarget baseline deltas measured after source evaluation are **Output Compensation**. Changing edit bone local basis requires **Action Basis Compensation**."

> **Dev:** "Does the user choose whether a Work Pose edit is input compensation or output compensation?"
> **Domain expert:** "No. The user edits one **Work Pose**. Bone Remap uses **Work Pose Classification** to classify changes automatically: **Source Solver Inputs** become **Input Compensation**, and ordinary FK or mapped source bone pose transforms become **Output Compensation**."

> **Dev:** "Can simple MMD-style IK be classified automatically?"
> **Domain expert:** "Yes. When IK target and pole target relationships are explicit in source constraints, they become **Source Solver Inputs** automatically. Ambiguous rig channels are shown in a **Classification Report**."

> **Dev:** "Is mapping a hidden one-to-one pairing flow?"
> **Domain expert:** "No. A **Mapping Row** can have many **Target Links**, and target channels should stay visible so users can add them explicitly."

> **Dev:** "Can two source Mapping Rows drive the same Deform Channel?"
> **Domain expert:** "No. Bone Remap supports one-to-many mapping, not many-to-one mapping. If the same **Deform Channel** is assigned again, the latest **Target Assignment** replaces the previous mapping."

> **Dev:** "If the mapping table changes, does Work Pose need to be rebuilt?"
> **Domain expert:** "No. The **Mapping Table** is the live distribution rule; changing it changes matrix distribution on the next solve."

> **Dev:** "Does Target Calibration prove that the mapping is correct?"
> **Domain expert:** "No. **Target Calibration** only prepares the currently mapped **Deform Channels**; mapping correctness is judged by live visual feedback."

> **Dev:** "Does every mapping edit require Target Calibration?"
> **Domain expert:** "No. Mapping edits change live distribution immediately; **Target Calibration** is only needed to synchronize mapped target bones into reliable **Deform Channels**."

> **Dev:** "Does Bone Remap add onto the current target pose?"
> **Domain expert:** "No. Live retargeting uses **Overwrite Retargeting**: mapped **Deform Channels** are solved from target bind/reference each frame."

> **Dev:** "Is Bake a separate retargeting algorithm?"
> **Domain expert:** "No. **Bake** samples the current Live Retargeting result frame by frame and writes the visible target result to an action."

> **Dev:** "Does Bake replay the source action and solve retargeting again from raw F-curves?"
> **Domain expert:** "No. **Bake** records the **Bake Source**: the current target-side visible result produced by Live Retargeting."

> **Dev:** "What frame range should Bake use by default?"
> **Domain expert:** "Use the active **Motion Action**'s effective frame range. A scene or custom range must be an explicit **Bake Range Override**."

> **Dev:** "Can Bake sample only the source action's existing keyframes?"
> **Domain expert:** "No. Default **Bake Sampling** captures every integer frame in the **Bake Range** so constraints, IK, drivers, Work Pose, and live retargeting are preserved."

> **Dev:** "If the source action only has rotation keys, should Bake write only rotation?"
> **Domain expert:** "No. **Bake** records **Baked Deform Channel Transforms** from the target's current visible result, so location, rotation, and scale may all be needed."

> **Dev:** "Should Bake convert every rotation to quaternion?"
> **Domain expert:** "No. **Baked Rotation Mode** follows the target pose bone's current rotation mode so the baked action matches the target rig's visible channels."

> **Dev:** "Should Bake overwrite the target armature's current action by default?"
> **Domain expert:** "No. **Bake** creates a new **Baked Target Action** by default; overwriting an existing target action must be an explicit user choice."

> **Dev:** "Should Bake record the whole target armature?"
> **Domain expert:** "No. The **Bake Scope** is only the mapped **Deform Channels** from the current **Mapping Table**; unmapped target bones stay outside Bone Remap's bake responsibility."

> **Dev:** "If the user overwrites an existing target action, should we clear the whole action?"
> **Domain expert:** "No. **Bake Overwrite** only replaces old keyframes inside the current **Bake Scope** and **Bake Range**."

> **Dev:** "Does moving the Source or Target object in the scene change retarget motion?"
> **Domain expert:** "No. Live retargeting uses **Armature Object Space Solve**; each armature's bone matrices are interpreted in that armature's own object space."

> **Dev:** "Does Bone Remap copy only rotation?"
> **Domain expert:** "No. Live retargeting transfers **Full Matrix Delta** so Work Pose translation, rotation, and scale calibration can affect the target result."

> **Dev:** "Does each Target Link under the same Mapping Row get a different source motion?"
> **Domain expert:** "No. MVP live retargeting uses **Shared Source Delta**: all Target Links under one Mapping Row receive the same source delta against their own target bind/reference."

> **Dev:** "Should a clipping fix be stored on the target rig or in Work Pose?"
> **Domain expert:** "No. In **Motion Edit Mode**, the fix is written to the current **Motion Clip**'s **Motion Action**."

> **Dev:** "Does Motion Edit Mode run under Work Pose Layer?"
> **Domain expert:** "Yes. Users edit the active **Motion Action** while viewing the **Final Visible Pose** under the active **Work Pose Layer**."

> **Dev:** "Do we edit the source action for motion fixes?"
> **Domain expert:** "Yes. By default, **Motion Edit Mode** writes motion fixes directly to the active **Motion Action**. If preserving the original matters, the user duplicates the action first."

> **Dev:** "Should users manually enter Blender's NLA tweak workflow before editing motion?"
> **Domain expert:** "No. Users enter **Motion Edit Mode** through Bone Remap; Bone Remap owns the edit-mode setup and teardown."

> **Dev:** "Is a Retarget Profile always an external preset file?"
> **Domain expert:** "No. The current working setup is **Project Retarget State** by default. A **Retarget Preset** is created only when the user explicitly exports reusable data."

> **Dev:** "Should a Retarget Preset include the concrete animation being edited?"
> **Domain expert:** "No. A **Retarget Preset** stores reusable retargeting setup, not **Motion Action** data or animation-library content."

> **Dev:** "How should a Retarget Preset identify bones?"
> **Domain expert:** "Use **Bone Name References**. Bone Remap does not require custom stable bone IDs for the first preset design."

> **Dev:** "What happens if a preset references bone names that do not exist in the current armatures?"
> **Domain expert:** "Import the resolvable parts, report **Missing Bone References**, and do not auto-guess unmatched bones."

> **Dev:** "Does importing a preset merge its Mapping Table into the current Mapping Table?"
> **Domain expert:** "No. **Preset Import** replaces the current **Mapping Table**. Missing references are reported, but old mappings are not kept as fallback."

## Flagged Ambiguities

- "bridge" belongs to the old plugin architecture; resolved: it is not core product language for Bone Remap's first design pass.
- "target bone" can mean either a semantic animation bone or a Blender bone used for deformation; resolved: use **Deform Channel** when discussing Bone Remap's target-side channels.
- "B skeleton" can mean either the original hierarchy or the normalized retargeting output; resolved: first-pass Bone Remap works on the **Deform Channel Rig**.
- "static pose" can mean either a current animation frame or the neutral source-side pose; resolved: use **Source Rest Pose** when discussing the starting point for **Work Pose Edit Mode**.
