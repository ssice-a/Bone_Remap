"""Target-side bone binding organization helpers."""

from __future__ import annotations

import bpy
from bpy.types import Object, Operator

from . import runtime_plan, state, target_bone_sets, weighted_geometry
from .registration import register_classes, unregister_classes


def group_target_bones_by_bound_mesh(context) -> tuple[int, int, str]:
    active_context = state.get_active_profile_context(context.scene)
    if active_context is None:
        return 0, 0, "Active Retarget Profile needs valid Source and Target Armatures."

    target = active_context.target_armature
    target_meshes = weighted_geometry.bound_meshes(context.scene, target)
    if not target_meshes:
        return 0, 0, "No target meshes bound to Target Armature."

    assignments_by_mesh = {
        mesh_obj.name: _weighted_bone_names_for_mesh(mesh_obj, target)
        for mesh_obj in target_meshes
    }
    assignments_by_mesh = {
        mesh_name: bone_names
        for mesh_name, bone_names in assignments_by_mesh.items()
        if bone_names
    }
    if not assignments_by_mesh:
        return 0, 0, "No target mesh has same-name non-zero vertex group weights."

    assigned = target_bone_sets.replace_mesh_target_sets(target, assignments_by_mesh)

    return len(assignments_by_mesh), assigned, f"Grouped {assigned} target bones into {len(assignments_by_mesh)} mesh collections."


def mark_selected_target_chain_as_physics(context) -> tuple[int, int, int, str]:
    active_context = state.get_active_profile_context(context.scene)
    if active_context is None:
        return 0, 0, 0, "Active Retarget Profile needs valid Source and Target Armatures."

    profile = active_context.profile
    target = active_context.target_armature
    target_names = _selected_target_chain_names(context, target)
    if not target_names:
        return 0, 0, 0, "Select one or more target bones first."

    marked = target_bone_sets.mark_physics_targets(target, target_names)

    removed = _remove_target_links(profile, set(target_names))
    if removed:
        runtime_plan.invalidate_runtime_plan(profile)

    _cleanup_removed_target_links(context, profile, target, target_names)
    target_bone_sets.sync_profile_target_sets(profile)
    _refresh_view(context)
    return marked, removed, len(target_names), f"Marked {marked} target bones as physics; removed {removed} mapping links."


def unmark_selected_target_chain_as_physics(context) -> tuple[int, int, str]:
    active_context = state.get_active_profile_context(context.scene)
    if active_context is None:
        return 0, 0, "Active Retarget Profile needs valid Source and Target Armatures."

    profile = active_context.profile
    target = active_context.target_armature
    target_names = _selected_target_chain_names(context, target)
    if not target_names:
        return 0, 0, "Select one or more target bones first."

    if not target_bone_sets.physics_target_names(target):
        return 0, len(target_names), "No physics target collection exists."

    unmarked = target_bone_sets.unmark_physics_targets(target, target_names)

    target_bone_sets.sync_profile_target_sets(profile)
    _refresh_view(context)
    return unmarked, len(target_names), f"Unmarked {unmarked} physics target bones."


def select_physics_targets(context) -> tuple[int, str]:
    active_context = state.get_active_profile_context(context.scene)
    if active_context is None:
        return 0, "Active Retarget Profile needs valid Source and Target Armatures."

    target = active_context.target_armature
    names = sorted(target_bone_sets.physics_target_names(target))
    if not names:
        return 0, "No physics target bones are marked."

    from . import mapping

    selected = mapping.activate_armature_and_select_pose_bones(context, target, names)
    return selected, f"Selected {selected} physics target bones."


def _weighted_bone_names_for_mesh(mesh_obj: Object, armature: Object) -> list[str]:
    bone_names = {bone.name for bone in armature.data.bones}
    weighted_group_indexes = set()
    for vertex in mesh_obj.data.vertices:
        for group_ref in vertex.groups:
            if group_ref.weight > weighted_geometry.WEIGHT_EPSILON:
                weighted_group_indexes.add(int(group_ref.group))

    names = []
    for vertex_group in mesh_obj.vertex_groups:
        if vertex_group.index not in weighted_group_indexes:
            continue
        if vertex_group.name in bone_names:
            names.append(vertex_group.name)
    return names


def _selected_target_chain_names(context, target: Object) -> list[str]:
    from . import mapping

    selected = mapping.selected_bone_names(context, target)
    if not selected:
        return []

    names: list[str] = []
    seen: set[str] = set()
    for bone_name in selected:
        bone = target.data.bones.get(bone_name)
        if bone is None:
            continue
        for chain_bone in _bone_with_descendants(bone):
            if chain_bone.name in seen:
                continue
            seen.add(chain_bone.name)
            names.append(chain_bone.name)
    return names


def _bone_with_descendants(bone) -> list:
    bones = [bone]
    for child in bone.children:
        bones.extend(_bone_with_descendants(child))
    return bones


def _remove_target_links(profile, target_names: set[str]) -> int:
    removed = 0
    for row in profile.mapping_rows:
        for index in range(len(row.target_links) - 1, -1, -1):
            if row.target_links[index].target_bone_name in target_names:
                row.target_links.remove(index)
                removed += 1
        if not row.target_links:
            row.active_target_link_index = -1
        elif row.active_target_link_index < 0:
            row.active_target_link_index = 0
        else:
            row.active_target_link_index = min(row.active_target_link_index, len(row.target_links) - 1)
    return removed


def _cleanup_removed_target_links(context, profile, target: Object, target_names: list[str]) -> None:
    from . import live_preview

    live_preview.cleanup_removed_target_links(context, profile, target, target_names)
    live_preview.solve_if_enabled(context, reason="target_physics_marked")


def _refresh_view(context) -> None:
    context.view_layer.update()
    screen = getattr(context, "screen", None)
    if screen is None:
        return
    for area in screen.areas:
        if area.type in {"VIEW_3D", "PROPERTIES"}:
            area.tag_redraw()


class BRM_OT_group_target_bones_by_mesh(Operator):
    bl_idname = "bone_remap.group_target_bones_by_mesh"
    bl_label = "Group Target Bones By Mesh"
    bl_description = "Create/update target bone collections from bound target meshes and their non-zero vertex groups"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        mesh_count, assigned_count, message = group_target_bones_by_bound_mesh(context)
        if mesh_count == 0 or assigned_count == 0:
            self.report({"WARNING"}, message)
            return {"CANCELLED"}

        self.report({"INFO"}, message)
        return {"FINISHED"}


class BRM_OT_mark_selected_target_chain_as_physics(Operator):
    bl_idname = "bone_remap.mark_selected_target_chain_as_physics"
    bl_label = "Mark Selected Chain As Physics"
    bl_description = "Add selected target bones and descendants to Physics Targets and remove them from the Mapping Table"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        marked, _removed, _chain_count, message = mark_selected_target_chain_as_physics(context)
        if marked == 0:
            self.report({"WARNING"}, message)
            return {"CANCELLED"}

        self.report({"INFO"}, message)
        return {"FINISHED"}


class BRM_OT_unmark_selected_target_chain_as_physics(Operator):
    bl_idname = "bone_remap.unmark_selected_target_chain_as_physics"
    bl_label = "Unmark Selected Physics"
    bl_description = "Remove selected target bones and descendants from Physics Targets"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        unmarked, _chain_count, message = unmark_selected_target_chain_as_physics(context)
        if unmarked == 0:
            self.report({"WARNING"}, message)
            return {"CANCELLED"}

        self.report({"INFO"}, message)
        return {"FINISHED"}


class BRM_OT_select_physics_targets(Operator):
    bl_idname = "bone_remap.select_physics_targets"
    bl_label = "Select Physics Targets"
    bl_description = "Select every target bone currently marked as a physics target"
    bl_options = {"REGISTER"}

    def execute(self, context):
        selected, message = select_physics_targets(context)
        if selected == 0:
            self.report({"WARNING"}, message)
            return {"CANCELLED"}

        self.report({"INFO"}, message)
        return {"FINISHED"}


_CLASSES = (
    BRM_OT_group_target_bones_by_mesh,
    BRM_OT_mark_selected_target_chain_as_physics,
    BRM_OT_unmark_selected_target_chain_as_physics,
    BRM_OT_select_physics_targets,
)


def register():
    register_classes(_CLASSES)


def unregister():
    unregister_classes(_CLASSES)
