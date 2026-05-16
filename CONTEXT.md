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
The target-side bind/reference matrix read as the base for solving a **Deform Channel** each frame.
_Avoid_: Hidden target application frame, source pivot copy, live-updated solve output

**Target Hierarchy Neutrality**:
The user-facing expectation that mapped target **Deform Channels** produce the same visible solved result whether target bones are flat or parented, when the solved transform is expressible by Blender pose channels.
_Avoid_: Requiring target bone detachment, treating the target parent tree as mapping semantics, assuming shear can always be represented by a flat target bone

**Pose Channel Representability**:
Whether a **Solved Target Pose Matrix** can be expressed by Blender target pose location, rotation, and scale channels without losing visible matrix information.
_Avoid_: Assuming every full matrix is keyable losslessly, silently treating shear loss as a mapping error

**Target Bind Refresh**:
An explicit update of target-side bind/reference matrices after calibration changes the **Deform Channel** rest setup.
_Avoid_: Retarget solve, source pivot alignment, automatic mapping side effect

**Retarget Profile**:
The long-lived calibration record for one **Source Armature** to **Target Armature** pairing.
_Avoid_: Motion clip, temporary session

**Active Retarget Profile**:
The single **Retarget Profile** currently used as the runtime context for Bone Remap core commands.
_Avoid_: Blender selection, inferred scene state, temporary object context

**Source Mesh Set**:
The explicit source-side mesh objects in the active **Auto Match Mesh Scope** used as weighted source geometry.
_Avoid_: Currently selected meshes, target meshes, hidden scene-wide discovery

**Target Mesh Set**:
The explicit target-side mesh objects in the active **Auto Match Mesh Scope** used as weighted target geometry.
_Avoid_: Currently selected meshes, source meshes, hidden scene-wide discovery

**Auto Match Mesh Scope**:
The explicit source mesh object references and target mesh object references used by **Auto Match Visible Meshes**.
_Avoid_: Transient Blender selection, all bound meshes by default, mapping table, armature pairing, cached point cloud, saved seam cluster, previous match result

**Bound Mesh Discovery**:
The convenience step that can find mesh objects with **Armature Modifier Binding** so users can add them into an **Auto Match Mesh Scope**.
_Avoid_: Runtime auto-match input, saved mesh membership replacement, current selection as execution context

**Armature Modifier Binding**:
A mesh binding relationship where a mesh object has an Armature modifier whose target object is the relevant **Source Armature** or **Target Armature**.
_Avoid_: Parent-only relationship, name similarity, selected mesh assumption

**Usable Vertex-Group Weight Data**:
Vertex-group weights where at least one vertex group name exactly matches a bone on the relevant armature and at least one vertex has weight greater than `1e-6` in such a group.
_Avoid_: Fuzzy bone-name match, prefix/suffix guessing, zero-weight group, unmatched vertex group

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

**Source Channel Snapshot**:
The captured source pose channel transforms and source rig/control properties used inside a **Work Pose Edit Snapshot**.
_Avoid_: Motion Action curves, target pose, Mapping Table data

**Changed Source Channel**:
A source channel whose value differs from the **Work Pose Edit Snapshot** by more than the configured comparison tolerance during **Work Pose Save**.
_Avoid_: Every non-default channel, every mapped source bone, user-selected changed flag

**Work Pose Editable Source Scope**:
The full visible **Source Armature** available for user edits during **Work Pose Edit Mode**.
_Avoid_: Mapping-only edit scope, target-link edit scope, prefiltered source controls

**Live Target Feedback**:
The realtime target response shown while editing **Work Pose** or authoring mappings.
_Avoid_: Motion Action playback, target action playback, offline preview, bake-only validation

**Unavailable Live Target Feedback**:
The state where target response cannot be shown for unresolved or invalid mapped target references.
_Avoid_: Failed Work Pose edit, Target Calibration requirement, guessed target response, silent unreliable preview

**Live Feedback Scope**:
The mapped target **Deform Channels** that can respond during **Live Target Feedback**.
_Avoid_: Full target armature, unmapped target inference, guessed target response

**Normal Preview**:
The normal playback state after **Work Pose** has been saved, where the active **Motion Action** plays under the **Work Pose Layer** and drives the target through live retargeting.
_Avoid_: Work Pose Edit Mode, target bake

**Live Retargeting**:
The realtime solve that reads the **Live Evaluated Source Pose** and writes mapped target **Deform Channels** for viewport playback before **Bake**.
_Avoid_: Baked target playback, source action conversion, target action output

**Live Preview**:
The user-facing automatic preview state where **Live Retargeting** updates the **Target Armature** from the **Active Retarget Profile**.
_Avoid_: Bake, manual apply step, hidden always-on solver

**Live Preview Enabled**:
The explicit setting that allows **Live Preview** to run automatically when relevant source, target, or profile state changes.
_Avoid_: Bake requirement, target calibration requirement, permanent background solve

**Clear Live Preview**:
The explicit command that resets target-side pose channels previously written by **Live Preview** back to their target bind/rest pose.
_Avoid_: Disabling Live Preview, Bake cleanup, source Work Pose reset, target edit-mode change

**Last Live Written Channels**:
The current **Active Retarget Profile**'s remembered set of target **Deform Channels** most recently written by **Live Matrix Write**.
_Avoid_: Current Mapping Table only, whole target armature, bake scope

**Removed Target Link Cleanup**:
The automatic reset of a target **Deform Channel** to its target bind/rest pose when a mapping edit removes that channel from the **Mapping Table** after it may have received live preview writes.
_Avoid_: Moving target ownership, full Clear Live Preview, Work Pose reset, target edit-mode change

**Live Matrix Write**:
The live target-side pose write where **Live Retargeting** applies solved full matrices to mapped **Deform Channels**.
_Avoid_: Live F-curve write, rotation-only live write, target action authoring, target edit-mode modification

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
A **Target Armature** viewed by Bone Remap as writable **Deform Channels** for retargeting and export.
_Avoid_: Semantic animation skeleton, source control rig, mapping table

**Channel Normalization**:
An optional explicit target-side operation that can make mapped target bones easier to solve or inspect as independent **Deform Channels** on the active **Target Armature**.
_Avoid_: Runtime solve prerequisite, mapping correctness check, automatic mapping side effect

**Channel Alignment**:
An optional calibration operation that moves **Deform Channel** heads to visually match mapped **Control Frame** pivots.
_Avoid_: Runtime solve, required retarget correctness

**Target Calibration**:
An optional explicit target-side convenience command for users who want Bone Remap to modify or align mapped target bones and refresh the affected target bind/reference data.
_Avoid_: Required retarget step, automatic mapping side effect, mapping correctness check, Work Pose, runtime solve, motion correction

**Mapping Row**:
One source-side row anchored to a **Control Frame**.
_Avoid_: One-to-one bone pair

**Target Link**:
One configurable mapped **Deform Channel** attached to a **Mapping Row**.
_Avoid_: Hidden target selection, implicit child mapping, per-target motion rule

**Source-First Mapping**:
The mapping authoring pattern where users create a source **Mapping Row** first, then add one or more target **Target Links** under that row.
_Avoid_: Target-first ownership, flat bone-pair list, one-to-one row model

**Destination Source Row**:
The **Mapping Row** that receives selected target **Deform Channels** during mapping authoring.
_Avoid_: Active armature selection, target owner by accident, hidden assignment row

**Selected Target Set**:
The target-side **Deform Channels** currently selected by the user for mapping authoring.
_Avoid_: All target bones, current Mapping Row targets, inferred target group

**Active Target Owner**:
The **Mapping Row** that currently owns the active target **Deform Channel**, if one exists.
_Avoid_: Destination by default, many-to-one owner, source bone selection

**Target Assignment Operation**:
The mapping authoring command that assigns the **Selected Target Set** to the **Destination Source Row**.
_Avoid_: Separate add and move semantics, automatic remapping, target-first mapping

**Mapping Table**:
The current distribution rule that tells Bone Remap which source **Control Frames** drive which target **Deform Channels**.
_Avoid_: Calibration result, Work Pose data

**Mapping Authoring Workbench**:
The user-facing workflow for creating, inspecting, correcting, and validating the **Mapping Table**.
_Avoid_: Hidden auto-mapper, bridge mapping editor, one-shot import wizard

**Mapping Health Report**:
The user-visible validation summary for the current **Mapping Table**.
_Avoid_: Automatic repair, hidden import log, semantic correctness proof

**Unmapped Mapping Row**:
A **Mapping Row** that has no **Target Links**.
_Avoid_: Disabled row, invalid source bone, unmapped target bone

**Invalid Mapping Reference**:
A source or target bone reference in the **Mapping Table** that cannot be resolved on the current armatures.
_Avoid_: Missing preset file, guessed replacement bone, semantic mismatch

**Duplicate Target Assignment**:
An invalid or transitional state where one **Deform Channel** is referenced by more than one **Target Link**.
_Avoid_: Supported many-to-one mapping, blended target ownership

**Auto Mapping Rule**:
An explicit project-defined rule that proposes **Mapping Table** entries for user review.
_Avoid_: Old bridge auto-build heuristic, mandatory mapping source, invisible mapping decision

**Auto Mapping Source Candidate**:
A source bone detected by automatic matching because the visible source mesh geometry has corresponding weighted source mesh influence.
_Avoid_: User-managed candidate list, every source bone by default, source control with no mesh influence, hidden helper bone

**Weighted Source Candidate Detection**:
The internal auto-mapping step that detects source bones with both a real source bone and corresponding weighted source mesh influence.
_Avoid_: Separate pre-import workflow, add all source bones, name-only source detection, helper-control import

**Auto Match Visible Meshes**:
The user-facing automatic matching command that compares the current visible source mesh point clouds against the current visible target mesh point clouds and writes matched source-to-target relationships into the **Mapping Table**.
_Avoid_: Work Pose-only matching, rest-pose-only matching, bone-transform matching, target-candidate management workflow

**Weighted Source Region**:
The source-side weighted point cloud associated with a detected **Auto Mapping Source Candidate** in **Auto Match Visible Geometry**.
_Avoid_: Source bone transform alone, source bone name alone, target mesh region, source-side seam cluster, merged source bones

**Visible Weighted Point Cloud**:
Point-level weighted mesh geometry sampled from **Auto Match Visible Geometry** for one source candidate, target **Deform Channel**, or **Target Seam Cluster**.
_Avoid_: Centroid-only region, radius-only region, bone transform proxy, cached previous-run geometry

**Auto Match Visible Geometry**:
The source and target mesh geometry as evaluated for automatic matching in the user-visible scene state.
_Avoid_: Rest-only mesh data, hidden bone-transform proxy, stale live retarget output, theoretical bind-only geometry

**Auto Match Visible Space**:
The shared world-space coordinate space used by automatic matching after evaluated mesh vertices are transformed by their mesh object's current world matrix.
_Avoid_: Per-region local origin, independent candidate normalization space, armature object-space retarget solve, rest mesh space

**Auto Match Geometry Sampling Adapter**:
The Blender-facing internal boundary that reads evaluated source and target mesh objects, vertex-group weights, visible mesh state, and object transforms, then outputs **Visible Weighted Point Clouds**.
_Avoid_: Matching algorithm, Mapping Table writer, persistent cache, hidden scene-wide discovery

**Auto Match Array Core**:
The Blender-independent matching logic that consumes **Visible Weighted Point Clouds**, builds target **Target Seam Clusters**, computes point-cloud matches, and returns planned **Target Assignment Operations**.
_Avoid_: `bpy` access, Blender object mutation, UI operator, evaluated mesh reader

**Auto Match Core Test Surface**:
The Blender-independent test surface for **Auto Match Array Core**, covering target seam clustering, point-cloud compression, spatial-hash nearest lookup, visible-space scoring, and assignment-plan generation.
_Avoid_: Manual viewport-only validation, UI-first matching verification, tests that require Blender scene state for pure matching math

**Auto Match Assignment Plan**:
The temporary result produced by **Auto Match Array Core** that lists which target **Deform Channels** should be assigned to which source **Mapping Rows**.
_Avoid_: Direct Mapping Table mutation, saved preset data, separate auto-map write path, persistent match cache

**Visible-Space Weighted Point-Cloud Score**:
The first-version auto-match score that compares source and target **Visible Weighted Point Clouds** in **Auto Match Visible Space**.
_Avoid_: Per-region translation normalization, per-region scale normalization, bone-name fallback, bone-transform fallback, hierarchy fallback, body-part semantic classifier, manual rule cascade

**Bidirectional Weighted Nearest-Point Distance**:
The concrete distance used by **Visible-Space Weighted Point-Cloud Score**, computed by combining target-to-source and source-to-target weighted nearest-point distances in **Auto Match Visible Space**.
_Avoid_: One-way containment score, centroid-only distance, equal vertex count assumption, ICP alignment, semantic fallback

**Deterministic Point-Cloud Compression**:
The repeatable point-cloud reduction step used before scoring, preserving high-weight samples and spatial coverage through visible-space grid representatives.
_Avoid_: Random sampling, first-N vertex truncation, centroid-only summary, dropping weight peaks, hidden non-deterministic match input

**Visible-Space Spatial Hash**:
The grid index used by auto matching to find nearby weighted points in **Auto Match Visible Space** without brute-force all-pairs distance checks.
_Avoid_: Full `N*M` distance matrix, scene-wide object discovery, semantic partition, candidate normalization

**Weighted Target Region**:
The target-side **Visible Weighted Point Cloud** associated with a target **Deform Channel** or derived **Target Seam Cluster**.
_Avoid_: Target bone transform alone, target bone name alone, source mesh region, live-retarget-contaminated geometry

**Target Seam Cluster**:
A group of target **Deform Channels** whose weighted vertex groups are joined by duplicate seam vertices with matching positions and matching weights.
_Avoid_: Merged vertex group, renamed target bone, required one-to-one target bone, first-version user-facing editor concept, name similarity, bone proximity, nearby-but-not-duplicate regions

**Target Seam Aggregation**:
The auto-mapping step that builds **Target Seam Clusters** from target-side duplicate seam vertices before target geometry is matched against source geometry.
_Avoid_: Post-match cleanup, user-facing candidate editing, modifying target vertex groups, source-side clustering, skeleton hierarchy reasoning, nearest-region guessing

**Target Geometry Evidence**:
Target-side weighted vertex positions, seam clusters, point-cloud shape, and weight distribution used by auto mapping.
_Avoid_: Target bone transform, target animation, source action curve

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

**Blender Native Keying**:
Blender's built-in key insertion, auto-keying, keying sets, and action/tweak behavior used while editing a **Motion Action**.
_Avoid_: Bone Remap custom keying subset, transform-only restriction

**Motion Clip**:
A source-side animation unit that uses one **Motion Action** and owns action-specific settings.
_Avoid_: Retarget profile, baked target action

**Motion Action**:
The Blender Action used by the active **Motion Clip**. User-authored motion edits are written directly to this action by default.
_Avoid_: Hidden correction layer, mandatory action copy, Work Pose

**Motion Edit Mode**:
The Bone Remap-managed mode for editing the active **Motion Clip** while viewing the **Final Visible Pose**.
_Avoid_: Work Pose edit, target calibration, target bake, manual Blender NLA setup

**Manual Motion Keyframing**:
User-inserted or auto-inserted source-side keyframes authored through **Blender Native Keying** during **Motion Edit Mode** and written to the active **Motion Action**.
_Avoid_: Target Armature keying, Work Pose Save, baked target edits, Bone Remap-only channel filter

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

**Solved Target Pose Matrix**:
The target-side pose matrix produced by applying a source **Full Matrix Delta** to a target **Target Bind Matrix**.
_Avoid_: Target rest edit, target action keyframe, accumulated target pose

**Shared Source Delta**:
The one-to-many distribution rule where one **Mapping Row** computes one **Full Matrix Delta** and all of its **Target Links** receive that same delta against their own target bind/reference.
_Avoid_: Per-target weighted follow, per-target driver rule

## Relationships

- A **Retargeting Workbench** has exactly one active **Source Armature** and one active **Target Armature**.
- A **Retargeting Workbench** has exactly one **Active Retarget Profile**.
- The **Active Retarget Profile** is the only runtime context for Bone Remap core commands.
- Switching the **Active Retarget Profile** changes which profile receives future core commands and **Live Preview** updates.
- Switching the **Active Retarget Profile** does not automatically run **Clear Live Preview** on the previous profile.
- A **Retarget Profile** belongs to one **Source Armature** and **Target Armature** pairing.
- A **Retarget Profile** explicitly stores its **Source Armature**, **Target Armature**, **Mapping Table**, **Work Pose**, and motion clip list.
- A **Retarget Profile** explicitly stores its **Auto Match Mesh Scope** when the user uses automatic mapping.
- Optional **Target Calibration** may leave target-side metadata or reports for inspection, but that metadata is not a required state for core retargeting commands.
- **Auto Match Mesh Scope** contains one **Source Mesh Set** and one **Target Mesh Set**.
- **Auto Match Mesh Scope** stores mesh object membership only.
- **Auto Match Mesh Scope** does not store point clouds, weighted regions, seam clusters, scores, or match results.
- **Auto Match Visible Meshes** recomputes point clouds, weighted regions, and **Target Seam Clusters** from current visible mesh geometry each time it runs.
- Blender selection may add objects to an **Auto Match Mesh Scope**, but selection does not define the scope at execution time.
- **Bound Mesh Discovery** can help fill an **Auto Match Mesh Scope** from the active profile's armature bindings.
- **Bound Mesh Discovery** only suggests mesh objects with **Armature Modifier Binding** to the relevant armature.
- **Bound Mesh Discovery** requires discovered mesh objects to have **Usable Vertex-Group Weight Data**.
- **Bound Mesh Discovery** does not infer binding from object parent relationships or object names.
- If a mesh has multiple Armature modifiers, **Bound Mesh Discovery** may suggest it for an armature when any Armature modifier targets that armature.
- A mesh must not belong to both the **Source Mesh Set** and **Target Mesh Set**; that overlap is a profile configuration error.
- An empty **Auto Match Mesh Scope** does not make the whole **Retarget Profile** invalid, but **Auto Match Visible Meshes** must fail clearly instead of guessing.
- Vertex groups that do not exactly match a bone name on the relevant armature are ignored during mesh discovery and auto mapping.
- Bone Remap does not fuzzy-match, repair, or guess vertex-group names during first-version **Bound Mesh Discovery**.
- A **Retarget Profile** is stored as **Project Retarget State** by default.
- **Project Retarget State** keeps the current working setup for the active Blender project.
- Core commands read the **Active Retarget Profile** instead of inferring objects from transient Blender selection.
- Blender selection may help fill profile fields or drive manual mapping operations, but it does not define the runtime context for core commands.
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
- **Preset Import** runs **Removed Target Link Cleanup** for previously mapped target **Deform Channels** that leave the **Mapping Table** after replacement.
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
- **Live Preview** is automatic only when **Live Preview Enabled** is on.
- **Live Preview** runs from the **Active Retarget Profile**; it does not scan the scene for other profiles or armatures to update.
- **Live Preview** updates after relevant Blender evaluation changes, timeline/playback changes, source pose edits, **Work Pose** changes, **Mapping Table** changes, or target bind/reference changes.
- **Live Preview** may use dirty flags and cached profile data for performance, but caching must not change the visible result.
- Disabling **Live Preview Enabled** stops future automatic **Live Matrix Write** operations but does not reset the **Target Armature**.
- **Clear Live Preview** is the explicit command for resetting B-side live pose residue to target bind/rest.
- **Clear Live Preview** affects the current **Active Retarget Profile**'s **Last Live Written Channels**.
- If **Last Live Written Channels** is empty, **Clear Live Preview** falls back to the current mapped **Deform Channels**.
- **Clear Live Preview** does not modify the **Source Armature**, **Work Pose**, **Motion Action**, **Mapping Table**, target edit-mode bones, or **Target Bind Matrix** values.
- A previously active profile's target armature may remain in its last preview pose until the user explicitly clears or changes it.
- **Live Retargeting** lets the **Target Armature** show the current retargeted result during playback without requiring **Bake**.
- **Live Retargeting** uses **Live Matrix Write** for mapped **Deform Channels**.
- **Live Matrix Write** applies the solved full matrix result; it does not author target action channels.
- **Live Matrix Write** modifies target pose state only; it does not modify target edit-mode bones, target rest data, or **Target Bind Matrix** values.
- **Target Hierarchy Neutrality** means the target parent-child hierarchy must not change the visible solved result for mapped **Deform Channels** when **Pose Channel Representability** holds.
- **Bake** converts the current visible target result into keyable action channels after **Live Retargeting** has produced it.
- **Work Pose** calibration must be visible on the **Source Armature** because those visible **Control Frames** are the pivots users inspect while driving the **Target Armature**.
- **Work Pose Edit Mode** starts from **Source Rest Pose** when no **Work Pose** has been saved.
- **Work Pose Edit Mode** starts from the saved **Work Pose** when one exists.
- Entering **Work Pose Edit Mode** captures a **Work Pose Edit Snapshot**.
- A **Work Pose Edit Snapshot** contains **Source Channel Snapshots** for the full visible **Source Armature** and recognized source rig/control properties.
- A **Work Pose Edit Snapshot** does not contain **Motion Action** curves.
- A **Work Pose Edit Snapshot** does not contain target pose data.
- Resetting **Work Pose** back to **Source Rest Pose** requires an explicit user command.
- **Work Pose Edit Mode** is isolated from the active **Motion Clip** and **Motion Action**.
- **Work Pose Edit Mode** does not play or evaluate the active **Motion Action**.
- **Work Pose Edit Mode** uses the full **Work Pose Editable Source Scope**.
- **Work Pose Editable Source Scope** is not limited to source bones currently present in the **Mapping Table**.
- Users may edit source bones before their mapping has been finalized so mapping mistakes can be discovered through **Live Target Feedback**.
- **Work Pose Edit Mode** shows **Live Target Feedback** from the current edited **Work Pose** state.
- **Live Target Feedback** during **Work Pose Edit Mode** does not come from the active **Motion Action** or a **Baked Target Action**.
- **Work Pose Edit Mode** does not require **Target Calibration**.
- **Live Target Feedback** uses the target armature's current bind/reference state unless the user has explicitly run an optional **Target Calibration** command.
- **Unavailable Live Target Feedback** is used only for unresolved or invalid mapped target references.
- **Live Target Feedback** uses the current **Mapping Table** to define its **Live Feedback Scope**.
- The **Live Feedback Scope** contains only mapped target **Deform Channels**.
- **Live Target Feedback** does not infer or animate unmapped target bones.
- If editing a source area produces no target response, that absence can indicate missing or incorrect mapping.
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
- A **Target Armature** is treated as a **Deform Channel Rig** by the solver, even when no optional **Target Calibration** has been applied.
- A **Deform Channel Rig** exposes mapped **Deform Channels** that receive the realtime retargeted pose.
- **Channel Normalization**, when explicitly used, modifies only mapped **Deform Channels** on the active **Target Armature**.
- **Target Bind Refresh** preserves target-side bind/reference data after optional calibration changes **Deform Channel** rest setup.
- Runtime retargeting uses each mapped **Deform Channel**'s **Target Bind Matrix** as the target base.
- Runtime retargeting reads the current **Target Bind Matrix** but does not refresh or rewrite it during playback.
- Changing the target armature's edit-mode bones is outside live solve and must come from an explicit user action such as **Channel Alignment** or another **Target Calibration** command.
- **Channel Alignment** directly modifies target edit-mode bone placement when used; it does not create a separate hidden target base.
- **Target Calibration** may run **Channel Normalization**, **Channel Alignment**, and **Target Bind Refresh** for mapped **Target Links**, depending on the explicit user command.
- Optional **Target Calibration** results do not prove that **Work Pose** or **Mapping Table** semantics are correct.
- **Target Calibration** does not modify unmapped target bones.
- **Target Calibration** is an in-place optional edit of the active **Target Armature**.
- **Target Calibration** is repeatable but never automatic.
- **Target Calibration** is a target-bone convenience tool; it does not validate whether the mapping is semantically correct.
- Changing the **Mapping Table** changes runtime distribution immediately and does not require **Target Calibration**.
- Live retargeting does not require **Target Calibration** or any target-side readiness flag.
- **Channel Alignment** is optional and exists for visual clarity or authoring comfort, not for retarget correctness.
- **Channel Alignment** requires **Work Pose** because **Control Frames** provide the alignment pivots.
- When **Channel Alignment** is used, that optional preprocessing step depends on the current **Work Pose** result.
- Retargeting does not require **Deform Channel** heads to align with **Control Frame** pivots.
- A **Mapping Row** may own multiple **Target Links**.
- One **Deform Channel** may have at most one **Target Assignment**.
- Bone Remap supports one-to-many source-to-target mapping, but not many-to-one target mapping.
- When a user assigns a **Deform Channel** that already has a **Target Assignment**, the latest assignment wins and replaces the previous mapping.
- The **Mapping Table** is the live distribution rule for retargeting.
- Runtime retargeting reads the current **Mapping Table** and distributes solved source matrices according to its current **Mapping Rows** and **Target Links**.
- Changing the **Mapping Table** changes what Bone Remap distributes on the next solve; it does not require recapturing **Work Pose**.
- **Mapping Authoring Workbench** owns the workflows for building and correcting the **Mapping Table**.
- **Mapping Authoring Workbench** uses **Source-First Mapping**.
- **Mapping Authoring Workbench** supports creating **Mapping Rows** from selected source bones.
- **Mapping Authoring Workbench** supports adding selected target **Deform Channels** to the active **Mapping Row**.
- A source **Mapping Row** may contain many **Target Links**.
- **Mapping Authoring Workbench** uses one **Destination Source Row** for target assignment.
- A **Destination Source Row** can be chosen from the source row list without switching the active Blender armature.
- **Mapping Authoring Workbench** uses the **Selected Target Set** as the target-side input for assignment.
- The **Active Target Owner** is displayed for inspection and can be explicitly used to fill the **Destination Source Row**.
- The **Active Target Owner** does not automatically replace the **Destination Source Row**.
- A **Target Assignment Operation** assigns every channel in the **Selected Target Set** to the **Destination Source Row**.
- A **Target Assignment Operation** adds unmapped targets, moves targets owned by other rows, and leaves already-owned targets unchanged.
- Moving a target **Deform Channel** from one **Mapping Row** to another is not **Removed Target Link Cleanup** because the target remains mapped.
- When a mapping edit makes a previously mapped target **Deform Channel** leave the **Mapping Table**, **Removed Target Link Cleanup** resets that channel to target bind/rest.
- **Removed Target Link Cleanup** does not modify the **Source Armature**, **Work Pose**, **Motion Action**, target edit-mode bones, or **Target Bind Matrix** values.
- After **Removed Target Link Cleanup**, that channel is removed from **Last Live Written Channels** for the current **Active Retarget Profile**.
- **Mapping Authoring Workbench** keeps target-side candidate **Deform Channels** visible for explicit user addition.
- Activating a **Mapping Row** highlights its **Target Links**.
- Activating a target **Deform Channel** that already has a **Target Assignment** can reveal its owning **Mapping Row**.
- **Mapping Authoring Workbench** shows a **Mapping Health Report**.
- A **Mapping Health Report** includes **Unmapped Mapping Rows**, **Duplicate Target Assignments**, and **Invalid Mapping References**.
- **Duplicate Target Assignments** should normally be zero because **Target Assignment** is unique and latest assignment wins.
- **Mapping Health Report** helps diagnose missing or incorrect mappings, but it does not prove semantic mapping correctness.
- **Auto Mapping Rules** may propose mappings, but the **Mapping Table** remains user-reviewable and editable.
- Bone Remap does not inherit the old bridge/child-rig auto-build heuristic as its default **Auto Mapping Rule**.
- **Auto Match Visible Meshes** reads its **Source Mesh Set** and **Target Mesh Set** from the active profile's **Auto Match Mesh Scope**.
- **Auto Match Visible Meshes** compares **Auto Match Visible Geometry** from the source and target mesh sets.
- **Auto Match Visible Meshes** is WYSIWYG: the mesh shapes visible to the user are the shapes used for matching.
- **Auto Match Visible Meshes** assumes the source and target mesh sets are already approximately aligned in **Auto Match Visible Space**.
- **Auto Match Visible Meshes** may pause **Live Preview** and clear previous **Live Matrix Write** results before reading target geometry so old mappings do not pollute the match.
- **Auto Match Visible Meshes** detects **Auto Mapping Source Candidates** from visible source weighted point clouds.
- Helper, IK, or control-only source bones are not auto-mapping source candidates unless they have source mesh influence.
- **Auto Match Visible Meshes** matches **Weighted Source Regions** against **Weighted Target Regions**.
- **Auto Match Geometry Sampling Adapter** is the only auto-match layer that reads Blender evaluated mesh data, vertex-group weights, visible object state, and object transforms.
- **Auto Match Array Core** runs after sampling and works on array data only; it does not access `bpy`, Blender objects, or `mathutils` objects.
- **Auto Match Core Test Surface** is implemented before Blender UI wiring for the first Auto Match rewrite.
- **Auto Match Core Test Surface** covers **Target Seam Aggregation**, **Deterministic Point-Cloud Compression**, **Visible-Space Spatial Hash**, **Bidirectional Weighted Nearest-Point Distance**, and **Auto Match Assignment Plan** behavior.
- **Auto Match Array Core** returns an **Auto Match Assignment Plan** instead of mutating the **Mapping Table** directly.
- **Auto Match Visible Meshes** replaces the current **Mapping Table** with the new **Auto Match Assignment Plan**; rerunning Auto Match is an overwrite operation, not an explicit merge.
- The first auto-match algorithm uses a single **Visible-Space Weighted Point-Cloud Score** to compare each target-side matching unit with source candidates.
- **Visible-Space Weighted Point-Cloud Score** is computed from weighted point distribution in **Auto Match Visible Space** and keeps visible-space position as match evidence.
- **Visible-Space Weighted Point-Cloud Score** uses **Bidirectional Weighted Nearest-Point Distance** as its first concrete scoring formula.
- **Visible-Space Weighted Point-Cloud Score** ranks source candidates; **Auto Match Visible Meshes** does not leave a target-side matching unit unmapped only because its best score crosses a global hard cutoff.
- **Bidirectional Weighted Nearest-Point Distance** uses a **Visible-Space Spatial Hash** for nearest-point lookup instead of brute-force all-pairs distance checks.
- **Deterministic Point-Cloud Compression** may reduce each region before scoring, but it must preserve high-weight samples and visible-space coverage.
- **Deterministic Point-Cloud Compression** must be stable for the same visible input; it does not use random sampling.
- **Visible-Space Weighted Point-Cloud Score** does not independently recenter or rescale each candidate before scoring.
- **Visible-Space Weighted Point-Cloud Score** does not fall back to names, bone transforms, hierarchy, body-part semantics, or IK/FK semantics.
- **Weighted Source Regions** and **Weighted Target Regions** retain point-level coordinates and weights as **Visible Weighted Point Clouds**.
- Centroids, bounds, radii, and other summaries are derived from **Visible Weighted Point Clouds** and are not the only region data.
- **Auto Match Visible Meshes** does not use source or target bone transforms, target bone direction, source/target skeleton hierarchy, IK/FK semantics, or body-part classification.
- **Auto Match Visible Meshes** does not require a saved **Work Pose**; a saved **Work Pose** may influence matching only by changing the visible source mesh shape.
- **Target Seam Aggregation** happens before target weighted geometry is matched against source weighted geometry.
- **Target Seam Aggregation** is target-side only.
- **Target Seam Aggregation** only joins target **Deform Channels** through duplicate seam vertices with matching positions and matching weights.
- **Target Seam Aggregation** does not use target bone names, target bone transforms, target hierarchy, region centroid proximity, or merely adjacent mesh areas.
- Auto matching does not merge multiple source bones into one source candidate.
- Each **Auto Mapping Source Candidate** remains a possible source **Mapping Row**.
- When a **Target Seam Cluster** matches a source candidate, all target **Deform Channels** in the cluster are assigned under the matched source **Mapping Row**.
- **Target Seam Clusters** are internal to auto matching in the first design and are not shown as a separate user-facing list.
- **Target Seam Clusters** are derived during auto matching and are not saved in the **Retarget Profile** or **Retarget Preset**.
- Auto matching keeps its user-facing result simple: target channels with usable visible weighted geometry are assigned into the **Mapping Table**, and any remaining cleanup happens through manual mapping after the overwrite.
- Auto matching overwrites the current **Mapping Table** instead of merging with older rows.
- Auto matching does not run **Target Calibration** automatically.
- Auto matching does not create or update any **Target Calibration** requirement flag; calibration remains an optional user command.
- Auto matching treats source armature bones as read-only; it may update **Mapping Rows** and **Target Links**, but it does not edit source bone data.
- Auto matching may create missing **Mapping Rows** for matched source bones; this creates mapping data only and does not create source bones.
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
- **Live Matrix Write** writes the **Solved Target Pose Matrix** for each mapped **Target Link**.
- **Solved Target Pose Matrix** is the visible target result; target hierarchy may affect internal channel storage, but not the user-facing solved result when **Pose Channel Representability** holds.
- Live retargeting uses **Shared Source Delta** for one-to-many mapping.
- In **Shared Source Delta**, one **Mapping Row** computes source motion once, and each **Target Link** applies it to its own target bind/reference.
- First-version **Target Links** do not define their own motion offset, weight, or follow rule.
- Corrections to retargeted motion should be authored on the source side through **Motion Edit Mode**.
- A **Retarget Profile** stores long-lived calibration data; a **Motion Clip** stores action-specific data.
- **Work Pose Layer** belongs to the **Retarget Profile**, not to a **Motion Clip**.
- A **Motion Clip** uses one active **Motion Action**.
- By default, **Motion Edit Mode** writes user edits directly to the active **Motion Action**.
- **Manual Motion Keyframing** belongs to the current **Motion Clip**'s active **Motion Action**.
- If **Motion Edit Mode** starts without an active **Motion Action**, Bone Remap creates or assigns an empty **Motion Action** before accepting manual keyframes.
- **Manual Motion Keyframing** follows **Blender Native Keying**; Bone Remap does not redefine which source-side properties Blender can key.
- Bone Remap's responsibility is to enter the correct **Motion Edit Mode**, active **Motion Action**, and **Work Pose Layer** context before Blender keying writes.
- **Manual Motion Keyframing** keys source-side bones or rig controls under the active **Work Pose Layer**, not the **Target Armature**.
- Target-side keyframes are outside the retarget correction workflow and can be overwritten by **Live Matrix Write**.
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
- **Bake** must not produce a result that differs from the current Live Retargeting preview for the same frame.
- If the preview result is wrong, the retargeting setup or live solve is wrong; **Bake** is not a second correction path.
- The default **Bake Range** comes from the active **Motion Action**'s effective frame range.
- If the active **Motion Action** has no usable effective frame range, **Bake** requires a **Bake Range Override**.
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
> **Domain expert:** "No. The first solver treats mapped target bones as **Deform Channels**. Optional **Channel Normalization** may make them easier to inspect or solve, but live retargeting is not gated on that button."

> **Dev:** "Should normalization create a duplicate rig?"
> **Domain expert:** "No. If the user explicitly runs **Channel Normalization**, it modifies the active **Target Armature** directly to avoid extra workflow steps."

> **Dev:** "Should Target Calibration always move target bone heads to source pivots?"
> **Domain expert:** "No. **Target Calibration** is itself an optional target-side convenience command. **Channel Alignment** is one possible calibration action, and it exists for readability and authoring comfort."

> **Dev:** "What target-side base does the solver use?"
> **Domain expert:** "It uses the **Target Bind Matrix**. If **Channel Alignment** is used, it directly edits target bone placement and bind data is refreshed."

> **Dev:** "Can live retargeting run before mapped target bones are detached into independent channels?"
> **Domain expert:** "Yes. Live retargeting uses the current target bind/reference data and current **Mapping Table**. **Target Calibration** is optional and must not become a hidden prerequisite."

> **Dev:** "Should Target Calibration process the whole target armature?"
> **Domain expert:** "No. When explicitly used, it only processes mapped **Target Links** and does not touch unmapped target bones."

> **Dev:** "Can Channel Alignment run before Work Pose exists?"
> **Domain expert:** "No. **Channel Alignment** needs **Control Frames**, and those come from **Work Pose**."

> **Dev:** "When editing Work Pose, should the current Motion Clip stay visible?"
> **Domain expert:** "No. **Work Pose Edit Mode** edits **Work Pose** without the active **Motion Clip**; the first edit starts from **Source Rest Pose**, and later edits start from the saved **Work Pose**."

> **Dev:** "How does Bone Remap know what changed when the user saves Work Pose?"
> **Domain expert:** "It compares the current edit state to the **Work Pose Edit Snapshot** captured when entering Work Pose Edit Mode. The user only edits and saves."

> **Dev:** "What does the Work Pose Edit Snapshot contain?"
> **Domain expert:** "It contains **Source Channel Snapshots** for source pose transforms and recognized source rig/control properties. It does not store Motion Action curves or target pose data."

> **Dev:** "Can Work Pose Edit Mode play the active Motion Action?"
> **Domain expert:** "No. **Work Pose Edit Mode** does not play or evaluate the active **Motion Action**; Work Pose remains long-lived calibration, not a captured animation frame."

> **Dev:** "Should Work Pose editing show the target result live?"
> **Domain expert:** "Yes. **Work Pose Edit Mode** shows **Live Target Feedback** so users can judge whether calibration drives the target correctly."

> **Dev:** "During Work Pose editing, should the target play the source motion or a baked action?"
> **Domain expert:** "No. **Work Pose Edit Mode** is isolated from motion playback. The target only shows **Live Target Feedback** from the current Work Pose edit state."

> **Dev:** "Can users enter Work Pose Edit Mode before running optional Target Calibration?"
> **Domain expert:** "Yes. **Work Pose Edit Mode** does not require **Target Calibration**. Target feedback is unavailable only for unresolved or invalid mapped target references."

> **Dev:** "Should Work Pose Edit Mode only allow editing currently mapped source bones?"
> **Domain expert:** "No. The **Work Pose Editable Source Scope** is the full visible Source Armature because mapping may still be wrong while calibration is being authored."

> **Dev:** "Should Live Target Feedback animate target bones that are not in the mapping table?"
> **Domain expert:** "No. **Live Feedback Scope** comes from the current **Mapping Table**; missing target response is useful evidence that mapping may be missing or wrong."

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

> **Dev:** "Should Bone Remap reuse the old plugin's bridge auto-build heuristic as the default auto-mapper?"
> **Domain expert:** "No. **Auto Mapping Rules** must be redesigned for direct Source-to-Target retargeting; old bridge heuristics are only reference material."

> **Dev:** "Should Auto Mapping consider every source bone by default?"
> **Domain expert:** "No. **Auto Match Visible Meshes** uses **Weighted Source Candidate Detection** during the command, so default source candidates are source bones with matching weighted source mesh influence."

> **Dev:** "Should Auto Mapping require users to manage a target candidate list?"
> **Domain expert:** "No. **Auto Match Visible Meshes** is a single command. It derives target-side input from weighted target **Deform Channels** in the active **Retarget Profile** and writes matched results into the **Mapping Table**."

> **Dev:** "What should the first Mapping Authoring Workbench make obvious?"
> **Domain expert:** "Users must be able to add source rows from selected source bones, add visible target channels to the active row, inspect ownership, and read a **Mapping Health Report**."

> **Dev:** "Should users build mappings as flat source-target pairs?"
> **Domain expert:** "No. Bone Remap uses **Source-First Mapping**: add the source Mapping Row first, then add many target links under that row."

> **Dev:** "When remapping target bones, should add and move be separate concepts?"
> **Domain expert:** "No. A **Target Assignment Operation** always assigns the **Selected Target Set** to the **Destination Source Row**; it adds, moves, or leaves targets unchanged as needed."

> **Dev:** "Should selecting an already-mapped target automatically switch the destination source row?"
> **Domain expert:** "No. The **Active Target Owner** is shown for inspection and may be explicitly used as the **Destination Source Row**, but it does not switch automatically."

> **Dev:** "Does a duplicate target mean many-to-one mapping is supported?"
> **Domain expert:** "No. **Duplicate Target Assignment** is a health-report problem state; normal assignment is unique and latest assignment wins."

> **Dev:** "Does Target Calibration prove that the mapping is correct?"
> **Domain expert:** "No. **Target Calibration** only performs optional target-side edits or reference refreshes; mapping correctness is judged by live visual feedback."

> **Dev:** "Does every mapping edit require Target Calibration?"
> **Domain expert:** "No. Mapping edits change live distribution immediately. **Target Calibration** is never required for mapping, live preview, or bake; users run it only when they explicitly want Bone Remap to adjust target bones."

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
- "B skeleton" can mean either the original hierarchy or the target-side writable channels; resolved: first-pass Bone Remap treats mapped target bones as **Deform Channels**, while **Target Calibration** remains optional.
- "static pose" can mean either a current animation frame or the neutral source-side pose; resolved: use **Source Rest Pose** when discussing the starting point for **Work Pose Edit Mode**.
