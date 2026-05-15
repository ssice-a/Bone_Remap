# Import and Export Retarget Presets

Label: `ready-for-agent`

## What to build

Add **Retarget Preset** import/export for reusable retarget setup. Presets identify bones by Blender bone name, do not include Motion Actions by default, and apply imported Mapping Tables by replacement rather than merge.

This slice should be demoable by exporting a preset from one project state, importing it into another compatible source/target pair, seeing missing references reported, and confirming old mappings are not kept as fallback.

## Acceptance criteria

- [ ] Presets can export reusable Retarget Profile data such as Mapping Table and Work Pose.
- [ ] Presets do not include Motion Action data by default.
- [ ] Presets use Bone Name References for source and target bones.
- [ ] Preset Import reports Missing Bone References instead of guessing replacements.
- [ ] Preset Import replaces the current Mapping Table rather than merging.
- [ ] Old mappings are not kept as fallback mappings when imported references are missing.
- [ ] Preset Import runs Removed Target Link Cleanup for previously mapped target channels that leave the Mapping Table after replacement.

## Blocked by

- Author Source-First Mapping Table Manually
- Clear Live Preview and Removed Target Link Cleanup
