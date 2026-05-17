# Auto Matching Uses Visible Weight Projection

Bone Remap's automatic matching workflow reads the currently visible source and target mesh geometry, projects target weighted point clouds onto the source mesh's visible weight field, and writes the resulting source-to-target assignments into the **Mapping Table**.

The command reads explicit source and target mesh object references from the active **Retarget Profile**'s **Auto Match Mesh Scope**. Blender selection can help populate that scope, but selection is not the execution input. The scope stores mesh membership only; point clouds, source weight fields, target seam clusters, and match results are recomputed from current visible mesh geometry every time Auto Match runs.

Automatic matching is WYSIWYG: the mesh shapes visible to the user are the shapes used for matching. Source and target mesh sets are expected to be approximately aligned in visible world space before Auto Match runs. A saved **Work Pose** is not a required auto-match input. If a Work Pose changes the visible source mesh shape, that visible result can influence matching in the same way as any other visible source mesh state.

The command does not match by source or target bone transforms. It uses target-side weighted mesh point clouds and a source-side **Source Weight Field** only. When the **Mapping Table** already has **Mapping Rows**, those rows are the source candidate whitelist: Auto Match samples only source vertex-group weights for those rows, clears their existing **Target Links**, and refills links from the new match result without deleting the Source Rows themselves. When the Mapping Table is empty, source bones become source candidates when visible source mesh geometry has matching weighted source mesh influence.

The implementation separates Blender-facing geometry sampling from matching math. The geometry sampling adapter reads evaluated Blender meshes, vertex-group weights, visible object state, and object transforms, then outputs a source weight field and target array-backed weighted point clouds. The matching core consumes those arrays, builds target seam clusters, runs **Visible Weight Projection Auto Match**, and returns an **Auto Match Assignment Plan** without accessing `bpy`, Blender objects, or `mathutils` objects.

Auto Match replaces current target assignments with the new assignment plan. If Source Rows already exist, rerunning Auto Match treats those rows as the explicit source candidate list and overwrites only their Target Links. If the table is empty, rerunning Auto Match creates Source Rows from matched source candidates. This keeps user-authored non-physical source lists stable while preventing stale Target Links from surviving into live solve.

The first matching algorithm is **Visible Weight Projection Auto Match**. Each target-side matching unit is optionally reduced with **Deterministic Point-Cloud Compression**, then each positive target point reads the nearest source point in **Auto Match Visible Space**. The source weights at those nearest source points are accumulated into source-candidate scores. The highest-scoring source wins that target-side matching unit, and the **Projection Winner Ratio** records how dominant that winning source was. The matcher does not independently recenter or rescale each candidate region, and it does not fall back to bone names, bone transforms, hierarchy, body-part semantics, or IK/FK semantics.

Target seam clustering happens before projection. When multiple target **Deform Channels** are connected by duplicate seam vertices with matching positions and matching weights, Auto Match treats that **Target Seam Cluster** as one target-side matching unit. If the cluster projects to a source candidate, every target channel in the cluster is assigned to the matched source Mapping Row.

First-version seam clustering is target-side only. Source geometry is not seam-merged because a source bone is the unit that becomes a Mapping Row. Existing Mapping Rows can further restrict which source bones participate in matching. Auto Match does not merge multiple source bones into one source candidate.

Auto Match may pause **Live Preview** before collecting target geometry. This prevents old mappings from contaminating the target-side visible geometry used for a new match. If Live Preview was enabled before the command, Bone Remap may restore it and solve once with the updated Mapping Table after the command finishes.

Auto Match does not run **Target Calibration**. Auto matching only changes Mapping Table data; Target Calibration is an optional separate target-side convenience command.

**Considered Options**

- Compare current visible source meshes with current visible target meshes.
- Require a saved Work Pose before automatic matching.
- Match from source or target bone positions, directions, or hierarchy.
- Match from weighted mesh geometry only.
- Store only centroid/radius summaries for weighted regions.
- Keep point-level coordinates and weights in weighted regions.
- Mix Blender sampling, target seam clustering, projection scoring, and mapping writes in one operator path.
- Split Blender-facing geometry sampling from Blender-independent matching math.
- Let the matching core read `bpy` or `mathutils` objects directly.
- Keep the matching core array-only after sampling.
- Let the matching core mutate the Mapping Table directly.
- Return an Auto Match Assignment Plan and apply it through Target Assignment Operation.
- Use existing Source Rows as a source candidate whitelist when present.
- Require source and target mesh sets to be approximately aligned in visible world space before matching.
- Normalize each candidate independently for translation and scale before matching.
- Use Visible Weight Projection Auto Match as the first matcher.
- Use source/target bidirectional point-cloud distance as the first matcher.
- Use centroid-only distance, ICP alignment, equal vertex count matching, bone names, or bone transforms.
- Use deterministic target point-cloud compression preserving high-weight samples and spatial coverage.
- Use random sampling, first-N truncation, or centroid-only summaries to reduce target regions.
- Validate matching through Blender-independent Auto Match Array Core tests first.
- Wire Blender UI first and rely on manual viewport testing for matching correctness.
- Add fallback scoring from names, bone transforms, hierarchy, or body-part semantics.
- Read only currently selected mesh objects at execution time.
- Read explicit source and target mesh sets from Auto Match Mesh Scope.
- Store point clouds or seam clusters in Auto Match Mesh Scope.
- Store mesh object membership only and recompute derived geometry each run.
- Build target seam clusters before projection.
- Match each target vertex group independently without seam clustering.
- Cluster target regions by nearby centroids or bone names.
- Cluster target regions only through duplicate seam vertices with matching positions and matching weights.
- Merge source regions before matching.
- Keep source candidates per source bone.
- Pause Live Preview before reading target geometry.
- Read target geometry while old live retarget writes are still applied.
- Run Target Calibration automatically after auto matching.
- Keep Target Calibration separate.
- Replace the Mapping Table before every auto-match run.
- Preserve existing Source Rows as the Auto Match source candidate list and overwrite only their Target Links.
- Preserve existing mappings that are not touched by matched auto-match results.

**Consequences**

- Auto Match is a mapping authoring helper, not a hidden retargeting solver.
- Users can shape the source and target models visually, then run one command to fill the Mapping Table.
- Auto Match remains WYSIWYG because derived geometry is recomputed from current visible meshes instead of cached from an earlier run.
- Users are responsible for approximately aligning the visible source and target mesh sets before running Auto Match.
- Visible-space position remains match evidence because target points read nearby source weight samples.
- If source and target meshes are not spatially aligned, Auto Match may produce poor or missing matches instead of hiding the problem with per-region normalization.
- Projection can compare target groups against source weights even when source and target vertex counts differ.
- Matching cost is controlled by deterministic target compression and nearest-source lookup rather than source/target all-pairs region scoring.
- Auto-match results remain reproducible for the same visible scene state because compression is deterministic.
- Work Pose becomes one possible way to change the visible source mesh before matching, not a required auto-match state.
- Fragmented target models are handled because seam-connected target regions can be matched as one combined target-side point cloud.
- Target seam clustering can inspect duplicate seam vertices and matching weights because point-level weighted geometry is still available.
- Blender API cost is isolated to the geometry sampling adapter, while the matching core can use array/vectorized processing.
- Target seam clustering, target compression, projection winner filtering, and assignment-plan generation can be unit-tested without requiring a Blender scene.
- Early failures in matching behavior are localized to the Auto Match Array Core instead of being mixed with Blender selection, UI, or evaluated mesh state.
- Manual mapping and automatic matching use the same row/link representation. Auto Match owns target-link replacement, while existing Source Rows can intentionally constrain source candidates.
- The matching core stays easier to test because its output is a temporary assignment plan, not Blender scene mutation.
- Auto-match results stay explainable because one projection rule owns the first-version match decision.
- Hard cases remain manually correctable in the Mapping Table instead of being hidden behind fallback heuristics.
- Incorrect automatic matches remain possible, so the Mapping Table stays user-reviewable and editable.
- Auto matching avoids bone-based guesses when target bones are generated, vertical, arbitrary, or only viewport conveniences.
- Existing manual mappings are user-reviewable, but rerunning Auto Match intentionally overwrites target links with the newly visible weighted-geometry result. Existing Source Rows stay available as the explicit source candidate list.
- Target Seam Clusters are temporary derived data; the saved result is the Mapping Table.
