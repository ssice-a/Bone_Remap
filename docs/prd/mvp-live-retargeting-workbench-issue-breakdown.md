# Issue Breakdown: MVP Live Retargeting Workbench

Draft breakdown for `docs/prd/mvp-live-retargeting-workbench.md`.

These are proposed tracer-bullet issues. They are not published yet because GitHub CLI is not authenticated in this environment.

## Proposed Slices

1. **Create Active Retarget Profile Shell**
   - **Type**: AFK
   - **Blocked by**: None
   - **User stories covered**: 1, 2, 3, 25
   - **What to build**: Add the minimal Retargeting Workbench entrypoint where users can choose a Source Armature and Target Armature, store them in an Active Retarget Profile, and have core commands read from that profile rather than transient Blender selection.

2. **Capture and Re-Enter Work Pose**
   - **Type**: AFK
   - **Blocked by**: 1
   - **User stories covered**: 4, 5, 6, 7, 8, 9
   - **What to build**: Add Work Pose Edit Mode for creating and editing a source-side Work Pose, saving full evaluated source matrices, starting from Source Rest Pose or the saved Work Pose as appropriate, and staying isolated from Motion Actions.

3. **Author Source-First Mapping Table Manually**
   - **Type**: AFK
   - **Blocked by**: 1
   - **User stories covered**: 12, 13, 14, 15, 16, 18
   - **What to build**: Add the Mapping Authoring Workbench MVP: source Mapping Rows, target Target Links, Destination Source Row assignment, latest-assignment-wins ownership, active target owner reveal, and a Mapping Health Report.

4. **Solve One Frame From Work Pose and Mapping Table**
   - **Type**: AFK
   - **Blocked by**: 2, 3
   - **User stories covered**: 26, 27, 28, 29, 30
   - **What to build**: Add a narrow one-frame retarget operator that reads the Active Retarget Profile, computes Full Matrix Delta, applies each Target Bind Matrix, and writes Solved Target Pose Matrices to mapped Deform Channels without action output or edit-mode changes.

5. **Run Live Preview for the Active Retarget Profile**
   - **Type**: AFK
   - **Blocked by**: 4
   - **User stories covered**: 19, 20, 21, 25, 30
   - **What to build**: Add Live Preview Enabled, automatic updates for relevant evaluation/profile changes, active-profile scoping, dirty/cache handling, and non-destructive disable behavior.

6. **Clear Live Preview and Removed Target Link Cleanup**
   - **Type**: AFK
   - **Blocked by**: 3, 5
   - **User stories covered**: 17, 22, 23, 24, 45
   - **What to build**: Track Last Live Written Channels, implement Clear Live Preview, clean target pose residue when target links leave the Mapping Table, and apply the same cleanup when Preset Import replaces mappings.

7. **Classify Work Pose Input and Output Compensation**
   - **Type**: AFK
   - **Blocked by**: 2, 5
   - **User stories covered**: 10, 11
   - **What to build**: Extend Work Pose Save with source channel snapshots, changed-channel detection, automatic Source Solver Input classification, sparse Input Compensation storage, Classification Report, and overrides for ambiguous channels.

8. **Edit Motion Actions Under Work Pose Layer**
   - **Type**: AFK
   - **Blocked by**: 2, 5
   - **User stories covered**: 31, 32, 33, 34, 35
   - **What to build**: Add Motion Edit Mode that sets up Blender-native keying/tweak context so manual and auto keyframes write to the active Motion Action while users view the Final Visible Pose under the Work Pose Layer.

9. **Bake the Current Live Retargeting Result**
   - **Type**: AFK
   - **Blocked by**: 5
   - **User stories covered**: 36, 37, 38, 39, 40, 41
   - **What to build**: Add Bake that samples the current visible Live Retargeting result across the Bake Range, writes a new Baked Target Action by default, supports explicit overwrite scope, and never recomputes from raw source F-curves.

10. **Import and Export Retarget Presets**
    - **Type**: AFK
    - **Blocked by**: 3, 6
    - **User stories covered**: 42, 43, 44, 45
    - **What to build**: Add Retarget Preset import/export using Bone Name References, Missing Bone Reference reports, replacement semantics for Mapping Table import, and cleanup for target channels removed by replacement.

11. **Auto Map From Work Pose Using Weighted Geometry**
    - **Type**: AFK
    - **Blocked by**: 2, 3, 6
    - **User stories covered**: 48, 49, 50
    - **What to build**: Add the first Auto Map From Work Pose command using Bound Mesh Discovery, weighted source/target regions, normalized comparison space, internal acceptance thresholds, Target Seam Clusters, and normal Target Assignment Operation semantics.

12. **Add Optional Target Calibration Commands**
    - **Type**: AFK
    - **Blocked by**: 3, 4
    - **User stories covered**: 46, 47
    - **What to build**: Add explicit target-side convenience commands such as Channel Alignment and Target Bind Refresh without making them prerequisites for mapping, Live Preview, Auto Map, or Bake.

## Suggested Implementation Order

1. Create Active Retarget Profile Shell
2. Capture and Re-Enter Work Pose
3. Author Source-First Mapping Table Manually
4. Solve One Frame From Work Pose and Mapping Table
5. Run Live Preview for the Active Retarget Profile
6. Clear Live Preview and Removed Target Link Cleanup
7. Classify Work Pose Input and Output Compensation
8. Edit Motion Actions Under Work Pose Layer
9. Bake the Current Live Retargeting Result
10. Import and Export Retarget Presets
11. Auto Map From Work Pose Using Weighted Geometry
12. Add Optional Target Calibration Commands
