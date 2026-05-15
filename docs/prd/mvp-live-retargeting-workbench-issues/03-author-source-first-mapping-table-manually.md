# Author Source-First Mapping Table Manually

Label: `ready-for-agent`

## What to build

Build the manual **Mapping Authoring Workbench** around source-first mapping. Users can create source **Mapping Rows**, select target **Deform Channels**, choose a **Destination Source Row**, and assign selected targets as **Target Links**.

This slice should be demoable by creating one source row, adding multiple target links under it, moving a target link to another source row, and seeing owner/health information update.

## Acceptance criteria

- [ ] Users can create Mapping Rows from source bones.
- [ ] Users can assign selected target Deform Channels to a Destination Source Row.
- [ ] A Mapping Row can own multiple Target Links.
- [ ] A Deform Channel can have at most one Target Assignment.
- [ ] Assigning an already-owned target to a different row moves ownership using latest-assignment-wins semantics.
- [ ] Moving a target between rows does not clear its target pose.
- [ ] Active target owner can be revealed without automatically changing the Destination Source Row.
- [ ] Mapping Health Report shows unmapped rows, invalid references, and duplicate assignment problems.

## Blocked by

- Create Active Retarget Profile Shell
