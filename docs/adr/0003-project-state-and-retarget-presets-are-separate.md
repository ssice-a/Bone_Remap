# Project State and Retarget Presets Are Separate

Bone Remap stores the current working retarget setup with the active Blender project by default. Reusable presets are explicit import/export records, not the only place where retarget state lives.

**Considered Options**

- Store all retarget data only in external preset files.
- Store all retarget data only inside the Blender project.
- Split current working state from explicit reusable presets.
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
- Old mappings are not kept as fallback mappings when imported references are missing.
- The live retargeting workflow reads current project state, not an external preset file directly.
- Importing a preset updates or creates project state; exporting a preset copies selected project state into a reusable record.
- This separates "what I am editing now" from "what I want to reuse later."
