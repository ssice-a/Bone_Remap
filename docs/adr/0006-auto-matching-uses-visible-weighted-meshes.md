# Auto Matching Uses Visible Weighted Meshes

Bone Remap's first automatic matching workflow compares the currently visible source mesh point clouds against the currently visible target mesh point clouds, then writes matched source-to-target relationships into the Mapping Table.

The command reads explicit source and target mesh object references from the active Retarget Profile's Auto Match Mesh Scope. Blender selection can help populate that scope, but selection is not the execution input. The scope stores mesh membership only; point clouds, weighted regions, seam clusters, and match results are recomputed from current visible mesh geometry every time Auto Match runs.

Automatic matching is WYSIWYG: the mesh shapes visible to the user are the shapes used for matching. Source and target mesh sets are expected to be approximately aligned in visible world space before Auto Match runs. A saved Work Pose is not a required auto-match input. If a Work Pose changes the visible source mesh shape, that visible result can influence matching in the same way as any other visible source mesh state.

The command does not match by source or target bone transforms. It uses weighted mesh point clouds only. Source bones become source candidates when visible source mesh geometry has matching weighted source vertex groups. Target Deform Channels become target regions when visible target mesh geometry has matching weighted target vertex groups. Weighted regions retain point-level coordinates and weights; centroids, bounds, radii, and other summaries are derived values rather than the only region data.

The implementation separates Blender-facing geometry sampling from matching math. The geometry sampling adapter reads evaluated Blender meshes, vertex-group weights, visible object state, and object transforms, then outputs array-backed weighted point clouds. The matching core consumes those arrays, builds target seam clusters, scores point-cloud matches, and returns an Auto Match Assignment Plan without accessing `bpy`, Blender objects, or `mathutils` objects.

Auto Match replaces the current Mapping Table with the new assignment plan. Rerunning the command is an overwrite operation rather than an explicit merge, which prevents stale source rows from an older source/target pairing from surviving into live solve.

The first matching algorithm uses a single Visible-Space Weighted Point-Cloud Score. Source and target weighted point clouds are compared in shared visible world space, with visible-space position kept as match evidence. Its concrete first-version distance is Bidirectional Weighted Nearest-Point Distance: compute weighted nearest-point distance from target to source and from source to target, then combine the two directions into one symmetric score. The score ranks source candidates; Auto Match does not leave a target-side matching unit unmapped only because the best score crosses a global hard cutoff. Nearest-point lookup uses a visible-space spatial hash instead of brute-force all-pairs distance checks. The matcher does not independently recenter or rescale each candidate region before scoring, and it does not fall back to bone names, bone transforms, hierarchy, body-part semantics, or IK/FK semantics.

Large weighted regions are reduced with Deterministic Point-Cloud Compression before scoring. Compression is stable for the same visible input, preserves high-weight samples, and preserves visible-space coverage through grid representatives. It is not random sampling, first-N truncation, or centroid-only summarization.

The first implementation validates Auto Match through the Blender-independent Auto Match Array Core before wiring Blender UI. Pure tests cover target seam clustering, deterministic point-cloud compression, visible-space spatial hash lookup, bidirectional weighted nearest-point scoring, and assignment-plan generation. Blender-facing tests then verify geometry sampling and operator integration.

Target seam clustering happens before point-cloud matching. When multiple target Deform Channels are connected by duplicate seam vertices with matching positions and matching weights, Auto Match treats that Target Seam Cluster as one target-side matching unit. If the cluster matches a source candidate, every target channel in the cluster is assigned to the matched source Mapping Row.

First-version seam clustering is target-side only. Source regions remain per-source-bone candidates because a source bone is the unit that becomes a Mapping Row. Auto Match does not merge multiple source bones into one source candidate.

Auto Match may pause Live Preview and clear Bone Remap's previous Live Matrix Write results before collecting target geometry. This prevents old mappings from contaminating the target-side visible geometry used for a new match. If Live Preview was enabled before the command, Bone Remap may restore it and solve once with the updated Mapping Table after the command finishes.

Auto Match does not run Target Calibration. Auto matching only changes Mapping Table data; Target Calibration is an optional separate target-side convenience command.

**Considered Options**

- Compare current visible source meshes with current visible target meshes.
- Require a saved Work Pose before automatic matching.
- Match from source or target bone positions, directions, or hierarchy.
- Match from weighted mesh point clouds only.
- Store only centroid/radius summaries for weighted regions.
- Keep point-level coordinates and weights in weighted regions.
- Mix Blender sampling, target seam clustering, point-cloud scoring, and mapping writes in one operator path.
- Split Blender-facing geometry sampling from Blender-independent matching math.
- Let the matching core read `bpy` or `mathutils` objects directly.
- Keep the matching core array-only after sampling.
- Let the matching core mutate the Mapping Table directly.
- Return an Auto Match Assignment Plan and apply it through Target Assignment Operation.
- Require source and target mesh sets to be approximately aligned in visible world space before matching.
- Normalize each candidate independently for translation and scale before scoring.
- Use one deterministic visible-space weighted point-cloud score for the first matcher.
- Use bidirectional weighted nearest-point distance as the first concrete point-cloud score.
- Use centroid-only distance, one-way nearest-point distance, ICP alignment, or equal vertex count matching.
- Use visible-space spatial hash lookup for nearest-point queries.
- Compute full all-pairs distance matrices for every source/target region pair.
- Use deterministic point-cloud compression preserving high-weight samples and spatial coverage.
- Use random sampling, first-N truncation, or centroid-only summaries to reduce region size.
- Validate matching through Blender-independent Auto Match Array Core tests first.
- Wire Blender UI first and rely on manual viewport testing for matching correctness.
- Add fallback scoring from names, bone transforms, hierarchy, or body-part semantics.
- Read only currently selected mesh objects at execution time.
- Read explicit source and target mesh sets from Auto Match Mesh Scope.
- Store point clouds or seam clusters in Auto Match Mesh Scope.
- Store mesh object membership only and recompute derived geometry each run.
- Build target seam clusters before point-cloud matching.
- Match each target vertex group independently without seam clustering.
- Cluster target regions by nearby centroids or bone names.
- Cluster target regions only through duplicate seam vertices with matching positions and matching weights.
- Merge source regions before matching.
- Keep source regions per source bone.
- Pause Live Preview and clear prior Live Matrix Write results before reading target geometry.
- Read target geometry while old live retarget writes are still applied.
- Run Target Calibration automatically after auto matching.
- Keep Target Calibration separate.
- Replace the Mapping Table before every auto-match run.
- Preserve existing mappings that are not touched by matched auto-match results.

**Consequences**

- Auto Match is a mapping authoring helper, not a hidden retargeting solver.
- Users can shape the source and target models visually, then run one command to fill the Mapping Table.
- Auto Match remains WYSIWYG because derived geometry is recomputed from current visible meshes instead of cached from an earlier run.
- Users are responsible for approximately aligning the visible source and target mesh sets before running Auto Match.
- Similar local shapes are easier to distinguish because visible-space position remains part of the scoring evidence.
- If source and target meshes are not spatially aligned, Auto Match may produce poor matches instead of hiding the problem with per-region normalization.
- The score can compare regions with different vertex counts because nearest-point distance does not require one-to-one vertex correspondence.
- The bidirectional score avoids a one-way small-region containment match being treated as a complete region match.
- Matching cost is controlled by deterministic compression and spatial hashing instead of by random sampling or full all-pairs comparison.
- Auto-match results remain reproducible for the same visible scene state because compression is deterministic.
- High-weight influence peaks and spatial coverage remain available after compression, which is more useful for mapping than uniform random truncation.
- Work Pose becomes one possible way to change the visible source mesh before matching, not a required auto-match state.
- Fragmented target models are handled because seam-connected target regions can be matched as one combined target-side point cloud.
- Target seam clustering can inspect duplicate seam vertices and matching weights because point-level weighted geometry is still available.
- Blender API cost is isolated to the geometry sampling adapter, while the matching core can use array/vectorized operations.
- Point-cloud matching and target seam clustering can be unit-tested without requiring a Blender scene.
- Early failures in matching behavior are localized to the Auto Match Array Core instead of being mixed with Blender selection, UI, or evaluated mesh state.
- Blender UI integration can stay thin because the tested core already owns seam clustering, compression, scoring, and assignment planning.
- Manual mapping and automatic matching use the same row/link representation, but Auto Match owns its command as a full replacement of the current automatic result.
- The matching core stays easier to test because its output is a temporary assignment plan, not Blender scene mutation.
- Auto-match results stay explainable because one scoring rule owns the first-version match decision.
- Hard cases remain manually correctable in the Mapping Table instead of being hidden behind fallback heuristics.
- Incorrect automatic matches remain possible, so the Mapping Table stays user-reviewable and editable.
- Auto matching avoids bone-based guesses when target bones are generated, vertical, arbitrary, or only viewport conveniences.
- Existing manual mappings are user-reviewable, but rerunning Auto Match intentionally overwrites the table with the newly visible weighted-geometry result.
- Target Seam Clusters are temporary derived data; the saved result is the Mapping Table.
