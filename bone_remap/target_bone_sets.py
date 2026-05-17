"""Target Bone Set storage on Blender Bone Collections."""

from __future__ import annotations

from bpy.types import Object

from . import runtime_plan


BONE_COLLECTION_PREFIX = "BRM Mesh: "
BASE_BONE_COLLECTION_NAME = "BRM Base Bones"
MAPPED_TARGET_COLLECTION_NAME = "BRM Mapped Targets"
PHYSICS_TARGET_COLLECTION_NAME = "BRM Physics Targets"
MAPPED_TARGET_PALETTE = "THEME04"
PHYSICS_TARGET_PALETTE = "CUSTOM"
PHYSICS_TARGET_COLORS = {
    "normal": (0.55, 0.36, 0.02),
    "select": (0.78, 0.50, 0.04),
    "active": (0.95, 0.68, 0.12),
}
_COLOR_TAG_PROP = "_brm_color_tag"
_PREVIOUS_COLOR_PROP = "_brm_previous_color_palette"
_PREVIOUS_CUSTOM_NORMAL_PROP = "_brm_previous_custom_normal"
_PREVIOUS_CUSTOM_SELECT_PROP = "_brm_previous_custom_select"
_PREVIOUS_CUSTOM_ACTIVE_PROP = "_brm_previous_custom_active"


def replace_mesh_target_sets(target_armature: Object, assignments_by_mesh: dict[str, list[str]]) -> int:
    _clear_managed_mesh_collections(target_armature)
    assigned = 0
    for mesh_name, bone_names in sorted(assignments_by_mesh.items()):
        collection = _get_or_create_bone_collection(target_armature, _collection_name(mesh_name))
        for bone_name in bone_names:
            bone = target_armature.data.bones.get(bone_name)
            if bone is None:
                continue
            _assign_to_managed_collection(target_armature, collection, bone)
            assigned += 1
    return assigned


def mark_physics_targets(target_armature: Object | None, target_bone_names: list[str] | tuple[str, ...] | set[str]) -> int:
    if target_armature is None or target_armature.type != "ARMATURE":
        return 0

    physics_collection = _get_or_create_bone_collection(target_armature, PHYSICS_TARGET_COLLECTION_NAME)
    marked = 0
    for target_name in target_bone_names:
        bone = target_armature.data.bones.get(target_name)
        if bone is None:
            continue
        _assign_to_managed_collection(target_armature, physics_collection, bone)
        marked += 1
    return marked


def unmark_physics_targets(target_armature: Object | None, target_bone_names: list[str] | tuple[str, ...] | set[str]) -> int:
    if target_armature is None or target_armature.type != "ARMATURE":
        return 0
    collection = target_armature.data.collections.get(PHYSICS_TARGET_COLLECTION_NAME)
    if collection is None:
        return 0

    removed = 0
    for target_bone_name in target_bone_names:
        bone = target_armature.data.bones.get(target_bone_name)
        if bone is None:
            continue
        if any(candidate.name == PHYSICS_TARGET_COLLECTION_NAME for candidate in bone.collections):
            collection.unassign(bone)
            removed += 1
    return removed


def physics_target_names(target_armature: Object | None) -> set[str]:
    return _collection_bone_names(target_armature, PHYSICS_TARGET_COLLECTION_NAME)


def auto_match_excluded_target_names(target_armature: Object | None) -> set[str]:
    return physics_target_names(target_armature)


def mesh_target_set_count(target_armature: Object | None) -> int:
    if target_armature is None or target_armature.type != "ARMATURE":
        return 0
    return sum(1 for collection in target_armature.data.collections if collection.name.startswith(BONE_COLLECTION_PREFIX))


def mapped_target_names(profile) -> set[str]:
    target = profile.target_armature
    physics_names = physics_target_names(target)
    return {
        target_name
        for target_name in runtime_plan.mapped_target_names(profile)
        if target_name not in physics_names
    }


def sync_profile_target_sets(profile) -> None:
    target = profile.target_armature
    if target is None or target.type != "ARMATURE":
        return

    mapped_collection = _get_or_create_bone_collection(target, MAPPED_TARGET_COLLECTION_NAME)
    for bone in tuple(mapped_collection.bones):
        mapped_collection.unassign(bone)

    for target_name in mapped_target_names(profile):
        bone = target.data.bones.get(target_name)
        if bone is not None:
            _assign_to_managed_collection(target, mapped_collection, bone)

    _sync_target_colors(target, profile.bone_binding_highlight_enabled)


def _clear_managed_mesh_collections(armature: Object) -> None:
    for collection in armature.data.collections:
        if not collection.name.startswith(BONE_COLLECTION_PREFIX):
            continue
        for bone in tuple(collection.bones):
            collection.unassign(bone)


def _get_or_create_bone_collection(armature: Object, name: str):
    existing = armature.data.collections.get(name)
    collection = existing if existing is not None else armature.data.collections.new(name)
    if _is_brm_managed_collection(name):
        _make_collection_non_visibility_driving(collection)
    return collection


def _assign_to_managed_collection(armature: Object, collection, bone) -> None:
    if _is_brm_managed_collection(collection.name):
        _ensure_base_visibility_collection(armature, bone)
    collection.assign(bone)


def _ensure_base_visibility_collection(armature: Object, bone) -> None:
    if any(not _is_brm_managed_collection(collection.name) for collection in bone.collections):
        return

    collection = armature.data.collections.get(BASE_BONE_COLLECTION_NAME)
    if collection is None:
        collection = armature.data.collections.new(BASE_BONE_COLLECTION_NAME)
    collection.assign(bone)


def _collection_name(mesh_name: str) -> str:
    return f"{BONE_COLLECTION_PREFIX}{mesh_name}"


def _is_brm_managed_collection(name: str) -> bool:
    return name in {MAPPED_TARGET_COLLECTION_NAME, PHYSICS_TARGET_COLLECTION_NAME} or name.startswith(BONE_COLLECTION_PREFIX)


def _make_collection_non_visibility_driving(collection) -> None:
    try:
        collection.is_visible = False
    except (AttributeError, TypeError):
        pass


def _sync_target_colors(target: Object, highlight_enabled: bool) -> None:
    mapped_names = _collection_bone_names(target, MAPPED_TARGET_COLLECTION_NAME)
    physics_names = _collection_bone_names(target, PHYSICS_TARGET_COLLECTION_NAME)
    if not highlight_enabled:
        _restore_brm_colors(target)
        return

    highlighted_names = mapped_names | physics_names
    for pose_bone in target.pose.bones:
        if pose_bone.name in physics_names:
            _set_brm_color(pose_bone, PHYSICS_TARGET_PALETTE, "PHYSICS", PHYSICS_TARGET_COLORS)
        elif pose_bone.name in mapped_names:
            _set_brm_color(pose_bone, MAPPED_TARGET_PALETTE, "MAPPED")
        elif pose_bone.name not in highlighted_names and pose_bone.get(_COLOR_TAG_PROP):
            _restore_bone_color(pose_bone)


def _collection_bone_names(target: Object | None, collection_name: str) -> set[str]:
    if target is None or target.type != "ARMATURE":
        return set()
    collection = target.data.collections.get(collection_name)
    if collection is None:
        return set()
    return {bone.name for bone in collection.bones}


def _set_brm_color(pose_bone, palette: str, tag: str, custom_colors: dict[str, tuple[float, float, float]] | None = None) -> None:
    if not pose_bone.get(_COLOR_TAG_PROP):
        pose_bone[_PREVIOUS_COLOR_PROP] = pose_bone.color.palette
        if pose_bone.color.palette == "CUSTOM":
            pose_bone[_PREVIOUS_CUSTOM_NORMAL_PROP] = tuple(pose_bone.color.custom.normal)
            pose_bone[_PREVIOUS_CUSTOM_SELECT_PROP] = tuple(pose_bone.color.custom.select)
            pose_bone[_PREVIOUS_CUSTOM_ACTIVE_PROP] = tuple(pose_bone.color.custom.active)
    pose_bone.color.palette = palette
    if custom_colors is not None:
        pose_bone.color.custom.normal = custom_colors["normal"]
        pose_bone.color.custom.select = custom_colors["select"]
        pose_bone.color.custom.active = custom_colors["active"]
    pose_bone[_COLOR_TAG_PROP] = tag


def _restore_brm_colors(target: Object) -> None:
    for pose_bone in target.pose.bones:
        if pose_bone.get(_COLOR_TAG_PROP):
            _restore_bone_color(pose_bone)


def _restore_bone_color(pose_bone) -> None:
    previous = pose_bone.get(_PREVIOUS_COLOR_PROP, "DEFAULT")
    try:
        pose_bone.color.palette = previous
    except TypeError:
        pose_bone.color.palette = "DEFAULT"
    if previous == "CUSTOM":
        _restore_custom_color_channel(pose_bone, "normal", _PREVIOUS_CUSTOM_NORMAL_PROP)
        _restore_custom_color_channel(pose_bone, "select", _PREVIOUS_CUSTOM_SELECT_PROP)
        _restore_custom_color_channel(pose_bone, "active", _PREVIOUS_CUSTOM_ACTIVE_PROP)
    if _COLOR_TAG_PROP in pose_bone:
        del pose_bone[_COLOR_TAG_PROP]
    if _PREVIOUS_COLOR_PROP in pose_bone:
        del pose_bone[_PREVIOUS_COLOR_PROP]
    for prop_name in (_PREVIOUS_CUSTOM_NORMAL_PROP, _PREVIOUS_CUSTOM_SELECT_PROP, _PREVIOUS_CUSTOM_ACTIVE_PROP):
        if prop_name in pose_bone:
            del pose_bone[prop_name]


def _restore_custom_color_channel(pose_bone, channel_name: str, prop_name: str) -> None:
    if prop_name not in pose_bone:
        return
    setattr(pose_bone.color.custom, channel_name, tuple(pose_bone[prop_name]))
