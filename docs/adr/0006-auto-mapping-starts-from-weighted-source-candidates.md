# Auto Mapping Runs As One Work Pose Based Command

Bone Remap's first automatic mapping workflow is a single user-facing command. It reads the source and target armatures from the active Retarget Profile, derives all bound source and target meshes from Armature modifiers targeting those armatures, detects source bones that have real source mesh influence, detects target Deform Channels that have target mesh influence, and writes matched source-to-target relationships into the Mapping Table. Users do not manage a separate target candidate list, and the command does not care about target semantic categories beyond the geometry and weight data needed for matching.

Auto Map From Work Pose requires a saved Work Pose. It compares target geometry against the source in that saved Work Pose, rather than using a temporary unsaved source pose or a random animation frame. Target-side weighted geometry and seam clusters are primary evidence. Target bone transforms are weak supporting evidence because target bones may be generated, vertical, arbitrary, or only optionally aligned for viewport readability.

The command does not match the source armature to the target mesh by source bone transforms alone. It matches source-side weighted regions, evaluated under the saved Work Pose, against target-side weighted regions represented by target Deform Channels and temporary seam clusters.

Matching happens in a normalized comparison space rather than raw world space. Source and target weighted geometry are centered and scaled independently before region comparison, so different model scale, object placement, and broad proportion differences do not dominate the first automatic mapping pass.

The comparison space preserves handedness and does not automatically mirror source or target geometry. Mirrored matching can be added later as an explicit option, but the first command must not silently swap left and right.

Because weighted geometry is the primary matching input, Auto Map From Work Pose fails when it cannot discover usable source or target meshes from the profile armatures. It does not fall back to bone-position-only matching.

Usable source and target weighted regions require exact vertex-group-name to bone-name matches on the relevant armature and at least one vertex weight greater than `1e-6`. Vertex groups that do not resolve to the relevant armature are ignored.

The first scoring pass is intentionally small: weighted region proximity, region bounds/overlap, and target seam consistency. It does not use skeleton hierarchy reasoning, target bone direction, IK/FK semantics, or body-part classification.

Auto Map From Work Pose writes only candidates that pass its internal acceptance condition. It does not force every target Deform Channel to map to some source. Candidates below the acceptance condition are skipped and remain available for manual mapping.

Auto Map From Work Pose does not run Target Calibration. Auto mapping only changes Mapping Table data; Target Calibration is an optional separate target-side convenience command and is not marked as required by auto mapping.

**Considered Options**

- Consider every source bone during auto mapping.
- Consider only source bones already present as Mapping Rows.
- Add a separate command that imports source bones with weighted vertex groups into a candidate set or Mapping Rows.
- Detect weighted source candidates internally during the auto-mapping command.
- Include helper, IK, and control-only bones automatically.
- Let users add control-only bones explicitly when they need them.
- Add a saved target candidate list.
- Derive target-side input directly from weighted target Deform Channels.
- Read only the currently selected mesh objects.
- Store explicit source and target mesh lists in the active Retarget Profile.
- Read all source and target meshes bound to the active profile's armatures.
- Fall back to bone-position-only matching when no weighted meshes are discovered.
- Fail clearly when usable source or target weighted meshes are not discovered.
- Treat target bone positions as primary evidence.
- Treat target weighted geometry and seam clusters as primary evidence.
- Match source bones to target mesh by bone transforms alone.
- Match source weighted regions to target weighted regions.
- Compare weighted regions directly in raw world space.
- Compare weighted regions in a normalized internal comparison space.
- Use skeleton hierarchy, target bone direction, IK/FK semantics, or body-part classification in the first scoring pass.
- Use only geometry/weight scoring signals in the first scoring pass.
- Automatically mirror source or target geometry during first-version auto mapping.
- Preserve handedness and avoid implicit mirroring.
- Fuzzy-match, repair, or guess vertex-group names during auto mapping.
- Require exact vertex-group-name to bone-name matches for first-version auto mapping.
- Expose auto-mapping weight threshold controls.
- Use a fixed first-version weight epsilon of `1e-6`.
- Allow Auto Map From Work Pose to run from the current unsaved source pose.
- Require a saved Work Pose before running Auto Map From Work Pose.
- Expose detailed confidence bands and scoring evidence in the first auto-mapping UI.
- Keep the first auto-mapping UI to matched assignments plus normal manual cleanup.
- Force every target Deform Channel to map to its nearest source candidate.
- Skip candidates below the internal acceptance condition.
- Expose score thresholds as first-version user-facing controls.
- Keep score thresholds internal for the first design.
- Clear the Mapping Table before every auto-mapping run.
- Preserve existing Mapping Table entries that are not touched by matched auto-mapping results.
- Run Target Calibration automatically after auto mapping.
- Keep Target Calibration separate and never create a calibration requirement flag from auto mapping.
- Skip target channels that already have Mapping Table ownership.
- Overwrite existing ownership for target channels matched by auto mapping.
- Modify source armature bone data during auto mapping.
- Treat the source armature as read-only during auto mapping.
- Require users to create every source Mapping Row before auto mapping.
- Allow auto mapping to create missing Mapping Rows for matched source bones.
- Allow auto mapping to create rows for any source bone.
- Limit auto-created rows to Auto Mapping Source Candidates.
- Expose Target Seam Clusters as a first-version user-facing list.
- Keep Target Seam Clusters internal to auto mapping in the first design.
- Save Target Seam Clusters into the Retarget Profile or Retarget Preset.
- Recompute Target Seam Clusters as temporary derived data during auto mapping.

**Consequences**

- Auto mapping starts from source bones that actually influence the source mesh.
- The default auto-mapping candidate set is smaller and easier to inspect.
- Helper, IK, and control-only bones do not accidentally receive target Deform Channels.
- Users still can add source rows manually for non-weighted controls when the retargeting design needs them.
- The command is a mapping authoring helper, not a substitute for manual review.
- The user-facing workflow stays as one button followed by normal Mapping Table cleanup.
- There is no long-lived target candidate state to synchronize with the Mapping Table.
- Fragmented target models are handled because all bound target meshes participate in detection and seam analysis.
- Auto mapping can work with generated target bones whose orientation or hierarchy is not meaningful.
- Large source/target shape differences still require user review, anchors, or manual correction; point-cloud evidence is a suggestion mechanism, not semantic proof.
- Auto mapping avoids low-quality guesses when the weighted geometry needed for point-cloud matching is unavailable.
- Normalized comparison reduces sensitivity to object placement and scale, but it does not prove semantic correctness.
- Auto mapping avoids hidden left/right swaps by not mirroring implicitly.
- Auto mapping ignores unresolved vertex groups instead of treating them as candidate regions.
- Naming cleanup or fuzzy matching can be added later as a separate tool instead of being hidden inside the first auto-mapping command.
- The first scoring pass stays small enough to implement and debug without becoming a hidden semantic classifier.
- Auto Map From Work Pose is reproducible because its source-side comparison pose is saved profile data.
- Users must save or update Work Pose before using this automatic mapping rule.
- Internal matching scores may exist for deterministic selection and debugging, but the first user-facing workflow should stay simple.
- The command assigns matched target channels into the Mapping Table and leaves unmatched target channels for manual mapping.
- Incorrect automatic mappings are more expensive to debug than visibly unmapped target channels.
- Auto mapping can report a simple count of mapped and remaining unmapped target channels without exposing detailed scores.
- Matched target channels follow the same latest-assignment-wins rule as manual mapping.
- Existing mappings that are not touched by the auto-mapping result remain unchanged.
- Auto mapping can be rerun as an incremental correction step without wiping manual mappings outside its matched result set.
- Auto mapping ownership changes do not reset target pose when the target channel remains in the Mapping Table; the next live solve overwrites it with the new source row's result.
- Auto mapping only uses removed-target cleanup for target channels that leave the Mapping Table.
- Auto mapping and target calibration remain separate user-visible operations.
- Auto mapping does not create or update a target calibration requirement flag.
- Users may run target-side calibration later only when they explicitly want Bone Remap to adjust target bones or refresh target bind/reference data after such changes.
- Auto mapping updates mapping data only; it does not move, rotate, scale, rename, create, or delete source bones.
- Auto mapping may create Mapping Rows because Mapping Rows are profile mapping data, not source armature bones.
- Auto-created Mapping Rows are limited to source candidates detected during that command.
- Target Seam Clusters help assign split target Deform Channels together, but the first UI still presents the result as normal source rows and target links.
- Target Seam Clusters are not stored as long-lived profile or preset data; the saved result is the Mapping Table.
