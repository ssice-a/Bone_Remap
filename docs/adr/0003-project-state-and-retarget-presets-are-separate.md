# Project State and Retarget Presets Are Separate

Bone Remap stores the current working retarget setup with the active Blender project by default. Reusable presets are explicit import/export records, not the only place where retarget state lives.

Core commands run from the active Retarget Profile, not from transient Blender selection. The profile explicitly owns the source armature, target armature, mapping table, Work Pose, motion clip list, and the explicit Auto Match Mesh Scope used by automatic mapping. Optional Target Calibration may leave target-side metadata or reports for inspection, but that metadata is not a required state for core retargeting commands. Selection can help users fill or edit profile data, including adding selected meshes to the Auto Match Mesh Scope, but it does not decide which objects Work Pose, auto mapping, live retargeting, or bake operate on at execution time.

Switching the active Retarget Profile changes which profile future core commands and Live Preview updates use. It does not automatically clear or reset the previous profile's target armature; users clear live preview pose explicitly when they want that cleanup.

For automatic mapping, a mesh belongs to the Source Mesh Set or Target Mesh Set when the user has added it to the active profile's Auto Match Mesh Scope. Bound Mesh Discovery can suggest meshes with Armature modifiers targeting the source or target armature, but the saved Auto Match Mesh Scope is the execution input. Usable vertex-group weight data requires an exact vertex-group-name to bone-name match on the relevant armature and at least one vertex weight greater than `1e-6`. Bone Remap does not infer mesh membership from parenting or object names during automatic mapping execution.

If a mesh has multiple Armature modifiers, Bound Mesh Discovery may suggest it for a profile armature when any Armature modifier targets that armature. A mesh that is present in both the source and target mesh sets is treated as a profile configuration error.

An empty Auto Match Mesh Scope does not invalidate the whole Retarget Profile. Commands that require weighted geometry must fail with a clear profile/setup error instead of guessing from selection, parenting, names, or bone transforms.

**Considered Options**

- Store all retarget data only in external preset files.
- Store all retarget data only inside the Blender project.
- Split current working state from explicit reusable presets.
- Let core commands infer source and target objects from current Blender selection.
- Make the active Retarget Profile the runtime context for core commands.
- Automatically clear the previous profile's live target pose when switching profiles.
- Leave profile switching as a context change only and make live preview cleanup explicit.
- Store explicit source and target mesh lists in the Retarget Profile as Auto Match Mesh Scope.
- Derive source and target mesh sets from armature binding relationships at execution time.
- Infer mesh membership from object parenting or names.
- Require an Armature modifier binding with usable vertex-group weights.
- Fuzzy-match, repair, or guess vertex-group names during mesh discovery.
- Require exact vertex-group-name to bone-name matches for first-version mesh discovery.
- Expose a configurable weight epsilon in the first UI.
- Use a fixed first-version weight epsilon of `1e-6`.
- Reject meshes with multiple Armature modifiers.
- Accept meshes with multiple Armature modifiers when one targets the relevant profile armature.
- Allow the same mesh to belong to both source and target mesh sets.
- Treat source/target mesh-set overlap as a configuration error.
- Treat missing discovered meshes as making the whole Retarget Profile invalid.
- Let mesh-dependent commands fail clearly while other profile commands can continue.
- Include Motion Actions in exported retarget presets.
- Keep Motion Actions outside retarget presets by default.
- Identify preset bones with custom stable IDs.
- Identify preset bones by Blender bone name.
- Silently drop preset mappings whose bone names do not exist.
- Fuzzy-match missing bone names during preset import.
- Partially import resolvable preset data and report missing bone names.
- Merge imported Mapping Table entries into the current Mapping Table.
- Replace the current Mapping Table with the imported Mapping Table.

**Consequences**

- Users can resume the current retargeting work without exporting a preset first.
- Presets stay intentional: they are created when the user wants to reuse mapping, Work Pose, or a full Retarget Profile outside the current project.
- Presets describe retargeting setup, not which concrete animation clip is being played.
- Motion Actions remain animation assets and are not included in Retarget Presets by default.
- Work Pose and Work Pose Layer are Retarget Profile data and can be reused across Motion Actions.
- Presets identify source and target bones by Blender bone name for the first design.
- Bone Remap does not require writing custom stable IDs onto bones for the first preset design.
- Preset import may partially resolve bone-name references.
- Missing bone-name references are reported to the user and do not participate in live retargeting until resolved.
- Bone Remap does not fuzzy-match missing bone names during preset import by default.
- Preset import replaces the current Mapping Table instead of merging with it.
- Preset import runs removed-target cleanup for previously mapped target channels that leave the Mapping Table after replacement.
- Old mappings are not kept as fallback mappings when imported references are missing.
- The live retargeting workflow reads current project state, not an external preset file directly.
- Importing a preset updates or creates project state; exporting a preset copies selected project state into a reusable record.
- This separates "what I am editing now" from "what I want to reuse later."
- Core command behavior is reproducible because it reads explicit profile object references instead of current selection.
- Switching profiles is non-destructive to visible target poses; cleanup is controlled by explicit Clear Live Preview.
- Current selection remains useful for convenience actions, but not for deciding the source/target object set used by core retargeting behavior.
- Users set the source armature and target armature, then explicitly define the Auto Match Mesh Scope when they want automatic mapping.
- Mesh membership is visible profile state for Auto Map instead of hidden scene discovery.
- Bound Mesh Discovery remains useful as a convenience for filling the Auto Match Mesh Scope without making current selection the execution input.
- Multiple Armature modifiers are tolerated when they still point clearly to the profile armature.
- Source and target mesh scope membership remains disjoint; overlap must be corrected before auto mapping can rely on the profile.
- Workflows that do not need weighted geometry can still use the profile when mesh discovery is empty.
- Workflows that need weighted geometry do not silently fall back to weaker object or bone heuristics.
- Unmatched vertex groups are ignored instead of making the whole mesh invalid.
- Mesh discovery remains deterministic because it does not use fuzzy naming or prefix/suffix guessing.
