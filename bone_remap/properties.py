"""Blender property definitions for Bone Remap project state."""

import bpy
from bpy.props import (
    BoolProperty,
    CollectionProperty,
    EnumProperty,
    FloatVectorProperty,
    IntProperty,
    PointerProperty,
    StringProperty,
)
from bpy.types import Action, Object, PropertyGroup

from .registration import register_classes, unregister_classes


PROFILE_COLLECTION_ATTR = "brm_retarget_profiles"
ACTIVE_PROFILE_INDEX_ATTR = "brm_active_profile_index"


def poll_armature(_self, obj: Object | None) -> bool:
    return obj is not None and obj.type == "ARMATURE"


def poll_mesh(_self, obj: Object | None) -> bool:
    return obj is not None and obj.type == "MESH"


def sync_active_motion_action(self, context) -> None:
    source = self.source_armature
    if source is None or source.type != "ARMATURE":
        return

    source.animation_data_create().action = self.active_motion_action
    if context is not None:
        context.view_layer.update()


class BRM_WorkPoseBoneMatrix(PropertyGroup):
    """One saved Work Pose matrix for a source pose bone."""

    bone_name: StringProperty(name="Bone Name")
    matrix: FloatVectorProperty(
        name="Work Pose Matrix",
        description="Source pose bone matrix in source armature object space",
        size=16,
        default=(
            1.0, 0.0, 0.0, 0.0,
            0.0, 1.0, 0.0, 0.0,
            0.0, 0.0, 1.0, 0.0,
            0.0, 0.0, 0.0, 1.0,
        ),
    )


class BRM_InputCompensationTransform(PropertyGroup):
    """Sparse source solver input compensation captured from Work Pose edits."""

    bone_name: StringProperty(name="Bone Name")
    matrix: FloatVectorProperty(
        name="Input Compensation Matrix",
        description="Changed source solver input transform captured during Work Pose Save",
        size=16,
        default=(
            1.0, 0.0, 0.0, 0.0,
            0.0, 1.0, 0.0, 0.0,
            0.0, 0.0, 1.0, 0.0,
            0.0, 0.0, 0.0, 1.0,
        ),
    )


class BRM_ClassificationOverride(PropertyGroup):
    """User override for Work Pose input/output classification."""

    bone_name: StringProperty(name="Bone Name")
    classification: EnumProperty(
        name="Classification",
        items=(
            ("INPUT", "Input Compensation", "Replay before source rig evaluation"),
            ("OUTPUT", "Output Compensation", "Use Work Pose matrix as output-side retarget baseline"),
        ),
        default="OUTPUT",
    )


class BRM_ClassificationReportItem(PropertyGroup):
    """One Work Pose classification report row."""

    bone_name: StringProperty(name="Bone Name")
    classification: EnumProperty(
        name="Classification",
        items=(
            ("INPUT", "Input Compensation", ""),
            ("OUTPUT", "Output Compensation", ""),
            ("AMBIGUOUS_OUTPUT", "Ambiguous Output", ""),
        ),
        default="OUTPUT",
    )
    reason: StringProperty(name="Reason")


class BRM_TargetLink(PropertyGroup):
    """One target Deform Channel assigned to a source Mapping Row."""

    target_bone_name: StringProperty(name="Target Bone")


class BRM_TargetBindMatrix(PropertyGroup):
    """Stored target bind/reference matrix for a target Deform Channel."""

    target_bone_name: StringProperty(name="Target Bone")
    matrix: FloatVectorProperty(
        name="Target Bind Matrix",
        description="Target Deform Channel bind/reference matrix in target armature object space",
        size=16,
        default=(
            1.0, 0.0, 0.0, 0.0,
            0.0, 1.0, 0.0, 0.0,
            0.0, 0.0, 1.0, 0.0,
            0.0, 0.0, 0.0, 1.0,
        ),
    )


class BRM_LiveWrittenTarget(PropertyGroup):
    """One target channel last written by Live Preview."""

    target_bone_name: StringProperty(name="Target Bone")


class BRM_AutoMatchMeshReference(PropertyGroup):
    """One mesh object included in Auto Match Mesh Scope."""

    mesh: PointerProperty(
        name="Mesh",
        description="Mesh object used by Auto Match Visible Meshes",
        type=Object,
        poll=poll_mesh,
    )


class BRM_MappingRow(PropertyGroup):
    """Source-first mapping row that owns one or more target links."""

    source_bone_name: StringProperty(name="Source Bone")
    target_links: CollectionProperty(type=BRM_TargetLink)
    active_target_link_index: IntProperty(
        name="Active Target Link",
        default=-1,
    )


class BRM_RetargetProfile(PropertyGroup):
    """Project-stored retarget setup for one source/target armature pair."""

    source_armature: PointerProperty(
        name="Source Armature",
        description="Source Armature whose evaluated pose drives retargeting",
        type=Object,
        poll=poll_armature,
    )
    target_armature: PointerProperty(
        name="Target Armature",
        description="Target Armature whose Deform Channels receive retargeted pose",
        type=Object,
        poll=poll_armature,
    )
    work_pose_saved: BoolProperty(
        name="Work Pose Saved",
        description="Whether this profile has saved Work Pose matrices",
        default=False,
    )
    work_pose_action: PointerProperty(
        name="Work Pose Action",
        description="Generated source-side action used as the Work Pose Layer",
        type=Action,
    )
    work_pose_editing: BoolProperty(
        name="Work Pose Edit Mode",
        description="Whether this profile is currently editing Work Pose",
        default=False,
        options={"SKIP_SAVE"},
    )
    work_pose_matrices: CollectionProperty(type=BRM_WorkPoseBoneMatrix)
    input_compensations: CollectionProperty(type=BRM_InputCompensationTransform)
    classification_overrides: CollectionProperty(type=BRM_ClassificationOverride)
    classification_report: CollectionProperty(type=BRM_ClassificationReportItem)
    auto_match_source_meshes: CollectionProperty(type=BRM_AutoMatchMeshReference)
    auto_match_target_meshes: CollectionProperty(type=BRM_AutoMatchMeshReference)
    mapping_rows: CollectionProperty(type=BRM_MappingRow)
    active_mapping_row_index: IntProperty(
        name="Destination Source Row",
        description="Mapping Row that receives selected target assignments",
        default=-1,
    )
    revealed_target_bone_name: StringProperty(
        name="Revealed Target",
        description="Last target Deform Channel inspected for ownership",
    )
    revealed_owner_source_bone_name: StringProperty(
        name="Revealed Owner",
        description="Source Mapping Row that owns the last revealed target",
    )
    live_preview_enabled: BoolProperty(
        name="Live Preview Enabled",
        description="Automatically solve the active profile when timeline, source pose, Work Pose, or Mapping Table changes",
        default=False,
    )
    live_preview_perf_logging: BoolProperty(
        name="Log Solve Performance",
        description="Print Live Preview solve timing details to the Blender console",
        default=False,
    )
    runtime_plan_revision: IntProperty(
        name="Runtime Plan Revision",
        description="Internal revision used to invalidate cached retarget runtime plans",
        default=0,
        options={"SKIP_SAVE"},
    )
    live_preview_last_written_targets: CollectionProperty(type=BRM_LiveWrittenTarget)
    live_preview_last_result: StringProperty(
        name="Live Preview Last Result",
        description="Last Live Preview status message",
    )
    active_motion_action: PointerProperty(
        name="Active Motion Action",
        description="Source-side Motion Action used by Motion Edit Mode and Bake defaults",
        type=Action,
        update=sync_active_motion_action,
    )
    motion_editing: BoolProperty(
        name="Motion Edit Mode",
        description="Whether this profile is currently editing source motion",
        default=False,
        options={"SKIP_SAVE"},
    )
    bake_use_range_override: BoolProperty(
        name="Use Bake Range Override",
        description="Use explicit bake start/end instead of the active Motion Action range",
        default=False,
    )
    bake_frame_start: IntProperty(name="Bake Start", default=1)
    bake_frame_end: IntProperty(name="Bake End", default=250)
    bake_overwrite_existing: BoolProperty(
        name="Overwrite Existing Target Action",
        description="Bake into the current target action and clear keys inside bake scope/range",
        default=False,
    )
    bake_last_result: StringProperty(name="Bake Last Result")
    target_bind_matrices: CollectionProperty(type=BRM_TargetBindMatrix)


_CLASSES = (
    BRM_WorkPoseBoneMatrix,
    BRM_InputCompensationTransform,
    BRM_ClassificationOverride,
    BRM_ClassificationReportItem,
    BRM_TargetLink,
    BRM_TargetBindMatrix,
    BRM_LiveWrittenTarget,
    BRM_AutoMatchMeshReference,
    BRM_MappingRow,
    BRM_RetargetProfile,
)


def register():
    register_classes(_CLASSES)

    setattr(
        bpy.types.Scene,
        PROFILE_COLLECTION_ATTR,
        CollectionProperty(type=BRM_RetargetProfile),
    )
    setattr(
        bpy.types.Scene,
        ACTIVE_PROFILE_INDEX_ATTR,
        IntProperty(
            name="Active Retarget Profile",
            description="Index of the active Retarget Profile used by Bone Remap commands",
            default=-1,
        ),
    )


def unregister():
    if hasattr(bpy.types.Scene, ACTIVE_PROFILE_INDEX_ATTR):
        delattr(bpy.types.Scene, ACTIVE_PROFILE_INDEX_ATTR)
    if hasattr(bpy.types.Scene, PROFILE_COLLECTION_ATTR):
        delattr(bpy.types.Scene, PROFILE_COLLECTION_ATTR)

    unregister_classes(_CLASSES)
