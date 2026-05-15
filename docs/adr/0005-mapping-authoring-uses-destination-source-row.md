# Mapping Authoring Uses A Destination Source Row

Bone Remap's mapping authoring workflow uses a source-first structure: users create source Mapping Rows, select target Deform Channels, choose one Destination Source Row, and assign the selected targets to that row. This keeps one-to-many mapping explicit without forcing users to switch between source and target armatures for every correction.

**Considered Options**

- Use a flat source-target pair table.
- Use target-first mapping where selecting a target drives the whole UI.
- Use two primary lists: source rows and target links under the destination source row.
- Automatically switch destination when the active target already has an owner.
- Show the active target owner for inspection, but require explicit user action to use it as the destination.
- Split add, move, and unchanged target cases into separate commands.
- Use one assignment command that adds unmapped targets, moves previously owned targets, and leaves existing targets unchanged.

**Consequences**

- Mapping authoring remains source-first and supports one source row owning many target links.
- The source rows list shows each source row and its target count.
- The target links list shows the targets under the current Destination Source Row.
- Users can choose a Destination Source Row from the source rows list without switching the active Blender armature.
- Target-side viewport selection defines the Selected Target Set.
- The active target's current owner is shown for inspection.
- The active target owner does not automatically replace the Destination Source Row.
- Users can explicitly use the active target owner as the Destination Source Row when they want to group selected targets under that owner.
- The primary assignment command is "assign selected targets to destination".
- The assignment command adds unmapped targets, moves targets from other source rows, and leaves targets already under the destination unchanged.
- Moving a target from one source row to another is not treated as deletion; the next live solve overwrites that target with the new owner row's result.
- Deleting or unassigning a target so it leaves the Mapping Table resets that target channel to bind/rest if it may have received live preview writes.
- Mapping Health Report remains diagnostic and does not prove semantic correctness.
