"""Target-side bone binding organization helpers."""

from __future__ import annotations

import bpy
from bpy.types import Object, Operator

from . import state, weighted_geometry
from .registration import register_classes, unregister_classes


BONE_COLLECTION_PREFIX = "BRM Mesh: "


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

    _clear_managed_mesh_collections(target)
    assigned = 0
    for mesh_name, bone_names in sorted(assignments_by_mesh.items()):
        collection = _get_or_create_bone_collection(target, _collection_name(mesh_name))
        for bone_name in bone_names:
            bone = target.data.bones.get(bone_name)
            if bone is None:
                continue
            collection.assign(bone)
            assigned += 1

    return len(assignments_by_mesh), assigned, f"Grouped {assigned} target bones into {len(assignments_by_mesh)} mesh collections."


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


def _clear_managed_mesh_collections(armature: Object) -> None:
    for collection in armature.data.collections:
        if not collection.name.startswith(BONE_COLLECTION_PREFIX):
            continue
        for bone in tuple(collection.bones):
            collection.unassign(bone)


def _get_or_create_bone_collection(armature: Object, name: str):
    existing = armature.data.collections.get(name)
    if existing is not None:
        return existing
    return armature.data.collections.new(name)


def _collection_name(mesh_name: str) -> str:
    return f"{BONE_COLLECTION_PREFIX}{mesh_name}"


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


_CLASSES = (
    BRM_OT_group_target_bones_by_mesh,
)


def register():
    register_classes(_CLASSES)


def unregister():
    unregister_classes(_CLASSES)
