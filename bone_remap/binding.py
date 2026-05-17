"""Target-side bone binding organization helpers."""

from __future__ import annotations

import bpy
from mathutils import Vector
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


def build_selected_physics_chain(context) -> tuple[int, int, str]:
    active_context = state.get_active_profile_context(context.scene)
    if active_context is None:
        return 0, 0, "Active Retarget Profile needs valid Source and Target Armatures."

    profile = active_context.profile
    target = active_context.target_armature
    from . import mapping

    selected_names = mapping.selected_bone_names(context, target)
    if len(selected_names) < 2:
        return 0, 0, "Select at least two target bones for one physics chain."

    root_name = _active_target_bone_name(context, target)
    if root_name is None or root_name not in selected_names:
        return 0, 0, "Set the active selected target bone as the chain head."

    place_from_weights = bool(profile.bone_binding_place_chain_from_weights)
    centers, missing = _chain_order_points(context, target, selected_names, place_from_weights)
    if missing:
        return 0, 0, f"Missing non-zero target weights for: {', '.join(missing[:5])}."

    ordered_names, order_message = _order_selected_chain(target, selected_names, root_name, centers)
    if not ordered_names:
        return 0, 0, order_message

    success, edit_message = _write_physics_chain_edit_bones(
        context,
        target,
        ordered_names,
        centers,
        place_from_weights=place_from_weights,
        connect_chain=bool(profile.bone_binding_connect_chain),
        correct_roll=bool(profile.bone_binding_correct_roll),
    )
    if not success:
        return 0, 0, edit_message

    target_bone_sets.mark_physics_targets(target, ordered_names)
    removed = _remove_target_links(profile, set(ordered_names))
    if removed:
        runtime_plan.invalidate_runtime_plan(profile)
    _cleanup_removed_target_links(context, profile, target, ordered_names)
    target_bone_sets.sync_profile_target_sets(profile)
    mapping.activate_armature_and_select_pose_bones(context, target, ordered_names)
    _refresh_view(context)
    return len(ordered_names), removed, f"Built physics chain with {len(ordered_names)} bones; removed {removed} mapping links."


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


def _active_target_bone_name(context, target: Object) -> str | None:
    if context.object == target and context.mode == "POSE":
        active_pose_bone = getattr(context, "active_pose_bone", None)
        if active_pose_bone is not None:
            return active_pose_bone.name

    active_data_bone = target.data.bones.active
    return active_data_bone.name if active_data_bone is not None else None


def _chain_order_points(context, target: Object, bone_names: list[str], use_weights: bool) -> tuple[dict[str, Vector], list[str]]:
    if not use_weights:
        return {
            bone_name: (target.data.bones[bone_name].head_local + target.data.bones[bone_name].tail_local) * 0.5
            for bone_name in bone_names
            if bone_name in target.data.bones
        }, []

    meshes = weighted_geometry.bound_meshes(context.scene, target)
    regions = weighted_geometry.weighted_regions(meshes, target)
    centers = {region.bone_name: region.centroid for region in regions}
    missing = [bone_name for bone_name in bone_names if bone_name not in centers]
    return {
        bone_name: centers[bone_name]
        for bone_name in bone_names
        if bone_name in centers
    }, missing


def _order_selected_chain(target: Object, selected_names: list[str], root_name: str, centers: dict[str, Vector]) -> tuple[list[str], str]:
    path_order = _order_by_existing_path(target, selected_names, root_name)
    if path_order:
        return path_order, "Existing parent path order."
    return _order_by_nearest_centers(selected_names, root_name, centers)


def _order_by_existing_path(target: Object, selected_names: list[str], root_name: str) -> list[str] | None:
    selected = set(selected_names)
    neighbors = {name: set() for name in selected_names}
    edge_count = 0
    for bone_name in selected_names:
        bone = target.data.bones.get(bone_name)
        parent = bone.parent if bone is not None else None
        if parent is None or parent.name not in selected:
            continue
        neighbors[bone_name].add(parent.name)
        neighbors[parent.name].add(bone_name)
        edge_count += 1

    if edge_count != len(selected_names) - 1:
        return None
    if any(len(names) > 2 for names in neighbors.values()):
        return None
    if len(neighbors[root_name]) != 1:
        return None

    ordered = [root_name]
    previous = None
    current = root_name
    while len(ordered) < len(selected_names):
        candidates = [name for name in neighbors[current] if name != previous]
        if len(candidates) != 1:
            return None
        previous, current = current, candidates[0]
        ordered.append(current)
    return ordered


def _order_by_nearest_centers(selected_names: list[str], root_name: str, centers: dict[str, Vector]) -> tuple[list[str], str]:
    missing = [name for name in selected_names if name not in centers]
    if missing:
        return [], f"Missing chain order point for: {', '.join(missing[:5])}."

    ordered = [root_name]
    remaining = set(selected_names)
    remaining.remove(root_name)
    current = root_name
    while remaining:
        next_name = min(remaining, key=lambda name: (centers[name] - centers[current]).length)
        if (centers[next_name] - centers[current]).length <= weighted_geometry.WEIGHT_EPSILON:
            return [], "Selected chain centers are too close to order safely."
        ordered.append(next_name)
        remaining.remove(next_name)
        current = next_name
    return ordered, "Nearest-center order."


def _write_physics_chain_edit_bones(
    context,
    target: Object,
    ordered_names: list[str],
    centers: dict[str, Vector],
    *,
    place_from_weights: bool,
    connect_chain: bool,
    correct_roll: bool,
) -> tuple[bool, str]:
    if context.object is not None and context.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")

    for selected_object in context.selected_objects:
        selected_object.select_set(False)
    target.select_set(True)
    context.view_layer.objects.active = target
    bpy.ops.object.mode_set(mode="EDIT")

    edit_bones = target.data.edit_bones
    selected = set(ordered_names)
    root = edit_bones.get(ordered_names[0])
    if root is None:
        bpy.ops.object.mode_set(mode="POSE")
        return False, "Chain head edit bone no longer exists."

    joints = None
    if place_from_weights:
        root_head_override = Vector(root.head) if root.parent is not None and root.parent.name not in selected and root.use_connect else None
        joints, joint_error = _chain_joints([centers[name] for name in ordered_names], root_head_override=root_head_override)
        if joint_error is not None:
            bpy.ops.object.mode_set(mode="POSE")
            return False, joint_error

    if root.parent is not None and root.parent.name in selected:
        root.use_connect = False
        root.parent = None

    for index, bone_name in enumerate(ordered_names):
        edit_bone = edit_bones.get(bone_name)
        if edit_bone is None:
            bpy.ops.object.mode_set(mode="POSE")
            return False, f"Missing edit bone: {bone_name}."
        if index > 0:
            edit_bone.use_connect = False
        if place_from_weights:
            edit_bone.head = joints[index]
            edit_bone.tail = joints[index + 1]

    for index, bone_name in enumerate(ordered_names[1:], start=1):
        edit_bone = edit_bones[bone_name]
        parent = edit_bones[ordered_names[index - 1]]
        if connect_chain and not place_from_weights:
            offset = Vector(parent.tail) - Vector(edit_bone.head)
            edit_bone.head = Vector(edit_bone.head) + offset
            edit_bone.tail = Vector(edit_bone.tail) + offset
        edit_bone.parent = parent
        if connect_chain:
            edit_bone.head = parent.tail
        edit_bone.use_connect = connect_chain

    if correct_roll:
        for bone_name in ordered_names:
            _align_bone_roll(edit_bones[bone_name])

    bpy.ops.object.mode_set(mode="POSE")
    return True, "Physics chain edit bones updated."


def _chain_joints(centers: list[Vector], root_head_override: Vector | None = None) -> tuple[list[Vector] | None, str | None]:
    if len(centers) < 2:
        return None, "Need at least two chain centers."

    joints = [centers[0] - (centers[1] - centers[0]) * 0.5]
    for index in range(1, len(centers)):
        joints.append((centers[index - 1] + centers[index]) * 0.5)
    joints.append(centers[-1] + (centers[-1] - centers[-2]) * 0.5)

    if root_head_override is not None:
        joints[0] = root_head_override

    for index in range(len(joints) - 1):
        if (joints[index + 1] - joints[index]).length <= weighted_geometry.WEIGHT_EPSILON:
            return None, "Computed chain joints are too close to place safely."
    return joints, None


def _align_bone_roll(edit_bone) -> None:
    direction = Vector(edit_bone.tail) - Vector(edit_bone.head)
    if direction.length <= weighted_geometry.WEIGHT_EPSILON:
        return
    axis = direction.normalized()
    reference = Vector((0.0, 0.0, 1.0))
    if abs(axis.dot(reference)) > 0.95:
        reference = Vector((1.0, 0.0, 0.0))
    edit_bone.align_roll(reference)


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


class BRM_OT_build_selected_physics_chain(Operator):
    bl_idname = "bone_remap.build_selected_physics_chain"
    bl_label = "Build Selected Physics Chain"
    bl_description = "Build one selected target physics chain from the active selected bone as the chain head"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        built, _removed, message = build_selected_physics_chain(context)
        if built == 0:
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
    BRM_OT_build_selected_physics_chain,
    BRM_OT_mark_selected_target_chain_as_physics,
    BRM_OT_unmark_selected_target_chain_as_physics,
    BRM_OT_select_physics_targets,
)


def register():
    register_classes(_CLASSES)


def unregister():
    unregister_classes(_CLASSES)
