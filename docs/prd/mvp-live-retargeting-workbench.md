# PRD: MVP Live Retargeting Workbench

Label: `ready-for-agent`

## Problem Statement

Bone Remap needs a maintainable first version of a Blender retargeting workflow where a user-provided **Source Armature** can drive a fragmented **Target Armature** in realtime while preserving the target's existing mesh binding. The previous plugin proved the workflow is useful, but the bridge-rig architecture, unclear Work Pose semantics, and mixed animation layers made the system hard to maintain.

The user needs a WYSIWYG **Retargeting Workbench**: edit a long-lived **Work Pose**, build a one-to-many **Mapping Table**, preview the target live, correct source motion through Blender-native keying, and bake the visible target result when needed.

## Solution

Build an MVP vertical slice of Bone Remap around a single **Active Retarget Profile**. The first version should support manual setup, saved **Work Pose**, source-first mapping, realtime **Live Preview**, explicit cleanup of target-side live pose residue, Blender-native **Motion Edit Mode**, and **Bake** from the current visible live result.

The MVP's central path is:

1. User selects a **Source Armature** and **Target Armature**.
2. User creates or edits **Work Pose** on the visible **Source Armature**.
3. User creates **Mapping Rows** and adds one or more **Target Links** under each source row.
4. **Live Preview** reads the evaluated source pose and writes mapped target **Deform Channels**.
5. User edits source motion in **Motion Edit Mode** using Blender-native keying.
6. User optionally bakes the current visible target result to a **Baked Target Action**.

The first tracer bullet should prove the core retarget loop before building every convenience feature: saved **Work Pose** plus manual **Mapping Table** plus **Live Preview** driving B from A.

## User Stories

1. As an animator, I want to choose one **Source Armature** and one **Target Armature**, so that Bone Remap knows which pair I am retargeting.
2. As an animator, I want the active setup stored as a **Retarget Profile**, so that I can continue working without exporting a preset first.
3. As an animator, I want core commands to use the **Active Retarget Profile**, so that transient Blender selection does not unexpectedly change the retarget target.
4. As an animator, I want to create a **Work Pose** on the visible **Source Armature**, so that I can calibrate the source control frames to the target model.
5. As an animator, I want Work Pose editing to start from **Source Rest Pose** when no Work Pose exists, so that the first calibration has a stable neutral baseline.
6. As an animator, I want later Work Pose edits to start from the saved Work Pose, so that I can refine calibration incrementally.
7. As an animator, I want Work Pose editing isolated from the active motion clip, so that I do not accidentally bake a motion frame into the calibration pose.
8. As an animator, I want to edit the full visible Source Armature in Work Pose mode, so that I can calibrate bones before the mapping table is fully correct.
9. As an animator, I want Work Pose to store full source matrices, so that mapping changes can reuse the saved calibration baseline.
10. As an animator, I want Bone Remap to classify Work Pose changes into input and output compensation, so that IK controls and ordinary FK output can both be handled from one Work Pose workflow.
11. As an animator, I want ambiguous Work Pose changes reported, so that I can inspect and override cases the plugin cannot classify confidently.
12. As an animator, I want source-first mapping rows, so that one source control frame can own multiple target deform channels.
13. As an animator, I want to add selected target deform channels to a destination source row, so that fragmented target model parts can share one source driver.
14. As an animator, I want a target channel assigned to only one source row at a time, so that many-to-one ownership does not make the live result ambiguous.
15. As an animator, I want assigning an already-owned target to a new row to move it, so that fixing wrong mappings is one direct operation.
16. As an animator, I want moving a target between source rows to avoid clearing its pose immediately, so that the next live solve simply overwrites it from the new owner.
17. As an animator, I want deleting a target link to clear that target channel to bind/rest, so that removed mappings do not leave confusing pose residue.
18. As an animator, I want a mapping health report, so that I can see unmapped rows, duplicate ownership problems, and invalid references.
19. As an animator, I want **Live Preview** to update automatically when enabled, so that I do not need to press refresh after every timeline, pose, Work Pose, or mapping change.
20. As an animator, I want to disable **Live Preview**, so that I can stop automatic writes to the target armature while inspecting or editing.
21. As an animator, I want disabling Live Preview to leave B in its current pose, so that the viewport does not jump unexpectedly.
22. As an animator, I want **Clear Live Preview** to reset B-side live pose residue, so that I can inspect the target's bind/rest state.
23. As an animator, I want Clear Live Preview to clear last live-written target channels, so that removed mappings can still be cleaned.
24. As an animator, I want Clear Live Preview to leave A, Work Pose, Motion Action, Mapping Table, B edit bones, and bind matrices untouched, so that cleanup is safe and local.
25. As an animator, I want switching Active Retarget Profile to avoid clearing the previous target pose automatically, so that profile switching is non-destructive.
26. As an animator, I want live retargeting to preserve the target binding, so that I do not need to transfer weights or bind B directly to A.
27. As an animator, I want target bone rest direction to be ignored as semantic motion, so that arbitrary generated B bones can still receive solved matrices.
28. As an animator, I want each mapped target channel solved from its own Target Bind Matrix, so that B's existing bind/reference data remains the base.
29. As an animator, I want one Mapping Row's target links to share the same source delta, so that one-to-many mapping stays simple and predictable in the MVP.
30. As an animator, I want live preview to write target pose only, so that previewing does not author target action curves or alter B edit-mode bones.
31. As an animator, I want motion corrections to be authored on the source side, so that the visible source result remains the source of truth for retargeting.
32. As an animator, I want **Motion Edit Mode** to run under the Work Pose Layer, so that I edit the same Final Visible Pose that drives the target.
33. As an animator, I want pressing `I`, auto-keying, and Blender keying sets to follow Blender-native behavior, so that I do not learn a separate Bone Remap keying system.
34. As an animator, I want Motion Edit Mode to create or assign an empty Motion Action when needed, so that I can hand-key a new clip.
35. As an animator, I want target armature keyframes to be outside the retarget correction path, so that live matrix writes do not conflict with correction data.
36. As an animator, I want Bake to record the current visible live target result, so that baked output matches what I saw in the viewport.
37. As an animator, I want Bake to sample every integer frame in the bake range by default, so that constraints, IK, drivers, Work Pose, and live retargeting are preserved.
38. As an animator, I want Bake to default to the active Motion Action's effective frame range, so that it does not accidentally bake the whole scene timeline.
39. As an animator, I want Bake Range Override for scene or custom ranges, so that I can intentionally bake outside the active action range.
40. As an animator, I want Bake to create a new Baked Target Action by default, so that existing target actions are not overwritten accidentally.
41. As an animator, I want Bake Overwrite to replace only mapped channels inside the selected bake range, so that unrelated target animation survives.
42. As an animator, I want Retarget Presets to store reusable retarget setup without Motion Actions, so that mapping and Work Pose can be reused across clips.
43. As an animator, I want Preset Import to replace the Mapping Table rather than merge, so that imported setup is clear and predictable.
44. As an animator, I want missing preset bone references reported instead of guessed, so that incorrect mappings are not silently created.
45. As an animator, I want Preset Import to clear target channels that leave the Mapping Table, so that old preset results do not leave live pose residue.
46. As an animator, I want Target Calibration to be optional, so that live preview, mapping, and bake do not depend on a target-side preparation button.
47. As an animator, I want optional Channel Alignment to move B bone heads only when I explicitly ask, so that visual alignment does not become a hidden retarget dependency.
48. As an animator, I want automatic mapping to be a helper rather than the only mapping workflow, so that I can inspect and correct the result.
49. As an animator, I want Auto Match Visible Meshes to compare the visible source and target weighted point clouds, so that mapping setup follows what I see in the viewport rather than arbitrary target bone directions.
50. As an animator, I want auto mapping to leave unmatched targets visible for manual mapping, so that low-confidence guesses do not hide mistakes.

## Implementation Decisions

- Build around a single **Active Retarget Profile** as the runtime context for core commands.
- Store **Source Armature**, **Target Armature**, **Mapping Table**, **Work Pose**, and motion clip list in the **Retarget Profile**.
- Store an explicit **Auto Match Mesh Scope** so automatic matching knows which source and target mesh fragments participate.
- Use **Work Pose** as the source-side control baseline and store full evaluated pose matrices for the full visible Source Armature.
- Work Pose editing is pose-mode, visible-source editing. The first design does not modify source edit-mode bones.
- Work Pose saving captures source channel snapshots, runs automatic Work Pose classification, stores input compensation for changed solver inputs, and stores Work Pose matrices for output-side baselines.
- Use Blender layer evaluation as the source of truth for the source Final Visible Pose.
- **Mapping Table** is source-first: source **Mapping Rows** own one or more target **Target Links**.
- One target **Deform Channel** may have at most one owner. Latest assignment wins.
- Moving a target link between source rows is not deletion and does not clear its pose.
- Removing a target link from the Mapping Table triggers **Removed Target Link Cleanup**.
- Retargeting uses **Armature Object Space Solve**. Source and target object transforms do not define retarget motion.
- Runtime source delta is measured as full matrix delta from Work Pose to live evaluated source pose.
- First-version matrix order is fixed: source delta is live source matrix multiplied by inverse Work Pose matrix; target pose matrix is source delta multiplied by target bind matrix.
- **Live Matrix Write** writes target pose state only. It does not write target F-curves, target edit bones, target rest data, or Target Bind Matrix values.
- **Live Preview** is automatic only when enabled and runs only for the Active Retarget Profile.
- Live preview may use dirty flags and cached profile data for performance, but cache behavior must preserve visible results.
- Disabling Live Preview stops future writes but does not reset the target armature.
- **Clear Live Preview** resets B-side live pose residue to target bind/rest for the profile's last live-written channels.
- Clear Live Preview falls back to current mapped channels if no last-written set exists.
- Switching Active Retarget Profile changes future live writes but does not automatically clear the previous profile's target pose.
- **Target Calibration** is optional and never a prerequisite for mapping, live preview, bake, or auto mapping.
- Optional **Channel Alignment** may move target edit-mode bone heads to source control frame pivots when explicitly run.
- **Motion Edit Mode** writes directly to the active Motion Clip's Motion Action by default.
- Motion Edit Mode uses Blender-native key insertion, auto-keying, keying sets, and action/tweak behavior.
- If Motion Edit Mode starts without an active Motion Action, Bone Remap creates or assigns an empty action before accepting manual keyframes.
- **Bake** records the visible target result produced by Live Retargeting. It is not a separate retargeting algorithm.
- Bake defaults to the active Motion Action's effective frame range. Scene and custom ranges require explicit Bake Range Override.
- Bake writes only mapped Deform Channels from the current Mapping Table.
- Bake writes location, rotation, and scale by default because source rotation-only actions can still produce full target transforms.
- Bake creates a new Baked Target Action by default. Overwrite is explicit and scoped.
- Retarget Presets identify bones by Blender bone name for the first design.
- Preset Import replaces the Mapping Table, reports missing bone references, and does not preserve old mappings as fallback.
- Preset Import runs removed-target cleanup for previously mapped target channels that leave the table.
- Auto Match Visible Meshes compares current visible source/target weighted point clouds from the Auto Match Mesh Scope.
- Auto Match may pause Live Preview and clear prior Live Matrix Write results before reading target geometry so old mappings do not pollute the match.
- Auto matching writes matched target channels through normal assignment semantics and does not run Target Calibration.

Major modules for implementation:

- **Profile State Module**: owns Active Retarget Profile data, validation, and project persistence.
- **Work Pose Module**: owns Work Pose edit session, snapshots, classification, compensation storage, and Work Pose Layer setup.
- **Mapping Module**: owns source rows, target links, assignment, owner lookup, health report, and removed-link cleanup triggers.
- **Live Solver Module**: computes source deltas and solved target pose matrices from cached profile data.
- **Live Preview Module**: owns enabled state, dependency/dirty tracking, event/update entrypoints, last live-written channel tracking, and Clear Live Preview.
- **Motion Edit Module**: enters/exits the Blender-native edit/tweak context and ensures manual keying writes to the active Motion Action under Work Pose Layer.
- **Bake Module**: samples the visible live result and writes a Baked Target Action.
- **Preset Module**: imports/exports reusable profile data and applies table replacement cleanup.
- **Auto Matching Module**: derives visible weighted point clouds, target seam clusters, and mapping assignments from Auto Match Mesh Scope.
- **Optional Target Calibration Module**: contains explicit target-side convenience commands such as Channel Alignment and bind refresh.

## Testing Decisions

- Tests should verify external behavior of domain modules rather than Blender UI implementation details.
- Matrix solve tests should cover full matrix delta, target bind application, one-to-many shared source delta, and no accumulation on prior target pose.
- Mapping tests should cover add, move, latest-assignment-wins, duplicate prevention, invalid references, owner reveal, and removed target cleanup.
- Live preview tests should cover enabled/disabled behavior, active-profile scoping, last live-written channel tracking, Clear Live Preview, profile switching, and cache invalidation preserving visible results.
- Work Pose tests should cover snapshot capture, changed source channel detection, full-source matrix storage, source solver input classification, ambiguous channel reporting, and override behavior.
- Motion edit tests should verify that edit setup targets the active Motion Action and that missing actions are created or assigned before manual keying.
- Bake tests should verify that bake samples the live preview result, uses the action effective range by default, honors range overrides, samples integer frames, writes only bake scope, and handles overwrite scope correctly.
- Preset tests should verify bone-name resolution, missing reference reports, table replacement, no fallback merge, and cleanup of target channels that leave the mapping table.
- Auto mapping tests should focus on deterministic matching behavior from weighted geometry and should avoid asserting UI-specific score displays.
- Performance-oriented tests or benchmarks should cover batch matrix solving and avoid per-frame/per-bone Blender Python overhead where pure data tests can run outside Blender.

## Out of Scope

- Full UI polish for every mapping and preset workflow.
- Per-target motion offsets, per-target weights, per-target follow rules, or driver rules.
- Many-to-one target mapping.
- Rebinding target meshes to the source armature.
- Treating target bone direction or hierarchy as the semantic source of motion.
- Automatic target-side Target Calibration as a prerequisite.
- Source edit-mode bone modification and Action Basis Compensation in the first Work Pose design.
- Hidden intermediate skeletons or bridge rigs as the core control surface.
- Target-side correction layers as the default motion fix workflow.
- Baking from raw source action curves through a separate offline solver.
- Scene-wide multi-profile live solving.
- Automatic fuzzy matching or repair of missing preset bone references.
- Auto mapping as a semantic body-part classifier.
- Mirrored auto mapping in the first version.
- Long-lived saved Target Seam Clusters.
- Full target hierarchy restoration or projection after independent Deform Channel solving.

## Further Notes

The MVP should prioritize the tracer bullet that proves the core retargeting loop:

1. Active Retarget Profile with Source and Target Armatures.
2. Saved Work Pose matrices.
3. Manually authored Mapping Table.
4. Live Preview enabled.
5. Source delta to target bind matrix solve.
6. Live Matrix Write to mapped target Deform Channels.
7. Clear Live Preview and removed target cleanup.

Auto mapping, presets, bake, and motion edit are important but can follow after this core path is demonstrably correct.

The repo currently cannot publish this PRD to GitHub Issues from this environment until `gh` is authenticated.
