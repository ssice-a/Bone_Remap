"""Regression checks for target hierarchy neutral retargeting.

Run with:
G:\blender5.0\blender.exe --background --factory-startup --python tests/blender/test_target_hierarchy_neutrality.py
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

import bpy

import bone_remap
from bone_remap import bake, solver, state, work_pose


EPSILON = 1.0e-5


def main() -> None:
    bone_remap.register()
    try:
        test_save_work_pose_leaves_source_visibly_in_saved_work_pose()
        test_save_work_pose_records_hidden_source_bones()
        test_solve_toggle_operator_is_single_source_of_live_solve_state()
        test_solve_toggle_writes_visible_target_result()
        test_live_solve_updates_after_source_pose_change()
        test_solve_toggle_rejects_profiles_that_write_no_targets()
        test_active_motion_action_selection_updates_source_action()
        test_add_weighted_source_rows_uses_bound_mesh_vertex_groups()
        test_auto_match_visible_meshes_uses_shared_weighted_geometry()
        test_auto_match_visible_meshes_replaces_stale_mapping_rows()
        test_mapping_row_activation_highlights_owned_target_bones()
        test_target_link_activation_highlights_one_target_bone()
        test_live_solve_writes_same_visible_target_matrices_for_flat_and_parented_targets()
        test_clear_live_preview_resets_parented_target_to_bind_matrices()
        test_bake_replays_parented_target_visible_matrices()
    finally:
        bone_remap.unregister()

    print("TARGET_HIERARCHY_NEUTRALITY_OK")


def test_save_work_pose_leaves_source_visibly_in_saved_work_pose() -> None:
    clear_scene()

    source = create_two_bone_armature("VisibleWorkPoseSource", source_names())
    target = create_two_bone_armature("VisibleWorkPoseTarget", target_names())
    create_profile("VisibleWorkPoseProfile", source, target)

    bpy.context.view_layer.objects.active = source
    source.select_set(True)
    bpy.ops.bone_remap.work_pose_enter()
    set_pose(source, parent_rotation_z=0.42, child_rotation_x=0.31, parent_scale=(1.2, 1.2, 1.2))
    expected = visible_pose_matrices(source, source_names())
    bpy.ops.bone_remap.work_pose_save()
    bpy.context.view_layer.update()

    assert_pose_matrices_close(expected, visible_pose_matrices(source, source_names()))


def test_save_work_pose_records_hidden_source_bones() -> None:
    clear_scene()

    source = create_two_bone_armature("HiddenWorkPoseSource", source_names())
    target = create_two_bone_armature("HiddenWorkPoseTarget", target_names())
    create_profile("HiddenWorkPoseProfile", source, target)
    source.data.bones["SourceChild"].hide = True

    bpy.context.view_layer.objects.active = source
    source.select_set(True)
    bpy.ops.bone_remap.work_pose_enter()
    bpy.ops.bone_remap.work_pose_save()

    profile = state.get_active_profile(bpy.context.scene)
    assert {item.bone_name for item in profile.work_pose_matrices} == set(source_names())


def test_solve_toggle_operator_is_single_source_of_live_solve_state() -> None:
    clear_scene()

    source = create_two_bone_armature("ToggleSource", source_names())
    target = create_two_bone_armature("ToggleTarget", target_names())
    profile = create_profile("ToggleProfile", source, target)

    assert not profile.live_preview_enabled
    bpy.ops.bone_remap.live_preview_toggle()
    assert profile.live_preview_enabled
    bpy.ops.bone_remap.live_preview_toggle()
    assert not profile.live_preview_enabled


def test_solve_toggle_writes_visible_target_result() -> None:
    clear_scene()

    source = create_two_bone_armature("ToggleSolveSource", source_names())
    target = create_two_bone_armature("ToggleSolveTarget", target_names())
    profile = create_profile("ToggleSolveProfile", source, target)
    set_pose(source, parent_rotation_z=0.38, child_rotation_x=0.52, parent_scale=(1.5, 1.5, 1.5))

    result = bpy.ops.bone_remap.live_preview_toggle()

    assert result == {"FINISHED"}
    assert profile.live_preview_enabled
    source_matrices = visible_pose_matrices(source, source_names())
    assert_pose_matrices_close(
        {
            "TargetRoot": source_matrices["SourceRoot"],
            "TargetChild": source_matrices["SourceChild"],
        },
        visible_pose_matrices(target, target_names()),
    )


def test_live_solve_updates_after_source_pose_change() -> None:
    clear_scene()

    source = create_two_bone_armature("LiveMoveSource", source_names())
    target = create_two_bone_armature("LiveMoveTarget", target_names())
    profile = create_profile("LiveMoveProfile", source, target)

    assert bpy.ops.bone_remap.live_preview_toggle() == {"FINISHED"}
    set_pose(source, parent_rotation_z=0.38, child_rotation_x=0.52, parent_scale=(1.5, 1.5, 1.5))
    bpy.context.view_layer.update()

    source_matrices = visible_pose_matrices(source, source_names())
    assert_pose_matrices_close(
        {
            "TargetRoot": source_matrices["SourceRoot"],
            "TargetChild": source_matrices["SourceChild"],
        },
        visible_pose_matrices(target, target_names()),
    )


def test_solve_toggle_rejects_profiles_that_write_no_targets() -> None:
    clear_scene()

    source = create_two_bone_armature("NoTargetSolveSource", source_names())
    target = create_two_bone_armature("NoTargetSolveTarget", target_names())
    profile = state.create_profile(bpy.context.scene, "NoTargetSolveProfile")
    profile.source_armature = source
    profile.target_armature = target
    save_rest_work_pose(profile, source)

    try:
        result = bpy.ops.bone_remap.live_preview_toggle()
    except RuntimeError:
        result = {"CANCELLED"}

    assert result == {"CANCELLED"}
    assert not profile.live_preview_enabled


def test_active_motion_action_selection_updates_source_action() -> None:
    clear_scene()

    source = create_two_bone_armature("MotionSource", source_names())
    target = create_two_bone_armature("MotionTarget", target_names())
    profile = create_profile("MotionProfile", source, target)
    action = bpy.data.actions.new("ChosenMotion")

    profile.active_motion_action = action

    assert source.animation_data is not None
    assert source.animation_data.action == action


def test_add_weighted_source_rows_uses_bound_mesh_vertex_groups() -> None:
    clear_scene()

    source = create_two_bone_armature("WeightedSource", source_names())
    target = create_two_bone_armature("WeightedTarget", target_names())
    profile = state.create_profile(bpy.context.scene, "WeightedRowsProfile")
    profile.source_armature = source
    profile.target_armature = target
    create_bound_weighted_mesh(source, "WeightedSourceMesh", {"SourceChild": [(0, 1.0)], "NotABone": [(1, 1.0)]})

    result = bpy.ops.bone_remap.mapping_add_weighted_source_rows()

    assert result == {"FINISHED"}
    assert [row.source_bone_name for row in profile.mapping_rows] == ["SourceChild"]


def test_auto_match_visible_meshes_uses_shared_weighted_geometry() -> None:
    clear_scene()

    source = create_two_bone_armature("AutoMapSource", source_names())
    target = create_two_bone_armature("AutoMapTarget", target_names())
    profile = state.create_profile(bpy.context.scene, "AutoMapProfile")
    profile.source_armature = source
    profile.target_armature = target
    save_rest_work_pose(profile, source)
    create_bound_weighted_mesh(
        source,
        "AutoMapSourceMesh",
        {"SourceRoot": [(0, 1.0), (1, 1.0)], "SourceChild": [(1, 1.0), (2, 1.0)]},
    )
    create_bound_weighted_mesh(
        target,
        "AutoMapTargetMesh",
        {"TargetRoot": [(0, 1.0), (1, 1.0)], "TargetChild": [(1, 1.0), (2, 1.0)]},
    )

    assert bpy.ops.bone_remap.auto_match_add_bound_meshes() == {"FINISHED"}
    result = bpy.ops.bone_remap.auto_match_visible_meshes()

    assert result == {"FINISHED"}
    mapping_by_source = {
        row.source_bone_name: [link.target_bone_name for link in row.target_links]
        for row in profile.mapping_rows
    }
    assert mapping_by_source == {
        "SourceRoot": ["TargetRoot"],
        "SourceChild": ["TargetChild"],
    }


def test_auto_match_visible_meshes_replaces_stale_mapping_rows() -> None:
    clear_scene()

    source = create_two_bone_armature("AutoMapReplaceSource", source_names())
    target = create_two_bone_armature("AutoMapReplaceTarget", target_names())
    profile = state.create_profile(bpy.context.scene, "AutoMapReplaceProfile")
    profile.source_armature = source
    profile.target_armature = target
    save_rest_work_pose(profile, source)
    add_mapping(profile, "0__old-target-armature", "TargetRoot")
    create_bound_weighted_mesh(
        source,
        "AutoMapReplaceSourceMesh",
        {"SourceRoot": [(0, 1.0), (1, 1.0)], "SourceChild": [(1, 1.0), (2, 1.0)]},
    )
    create_bound_weighted_mesh(
        target,
        "AutoMapReplaceTargetMesh",
        {"TargetRoot": [(0, 1.0), (1, 1.0)], "TargetChild": [(1, 1.0), (2, 1.0)]},
    )

    assert bpy.ops.bone_remap.auto_match_add_bound_meshes() == {"FINISHED"}
    result = bpy.ops.bone_remap.auto_match_visible_meshes()

    assert result == {"FINISHED"}
    mapping_by_source = {
        row.source_bone_name: [link.target_bone_name for link in row.target_links]
        for row in profile.mapping_rows
    }
    assert mapping_by_source == {
        "SourceRoot": ["TargetRoot"],
        "SourceChild": ["TargetChild"],
    }


def test_mapping_row_activation_highlights_owned_target_bones() -> None:
    clear_scene()

    source = create_two_bone_armature("HighlightSource", source_names())
    target = create_two_bone_armature("HighlightTarget", target_names())
    profile = create_profile("HighlightProfile", source, target)

    result = bpy.ops.bone_remap.mapping_activate_source_row(mapping_index=0)

    assert result == {"FINISHED"}
    assert bpy.context.object == target
    assert selected_pose_bone_names(target) == ["TargetRoot"]
    assert target.data.bones.active == target.data.bones["TargetRoot"]
    assert profile.active_mapping_row_index == 0


def test_target_link_activation_highlights_one_target_bone() -> None:
    clear_scene()

    source = create_two_bone_armature("TargetLinkHighlightSource", source_names())
    target = create_two_bone_armature("TargetLinkHighlightTarget", target_names())
    profile = create_profile("TargetLinkHighlightProfile", source, target)
    profile.active_mapping_row_index = 0
    first_row = profile.mapping_rows[0]
    link = first_row.target_links.add()
    link.target_bone_name = "TargetChild"

    result = bpy.ops.bone_remap.mapping_activate_target_link(target_link_index=1)

    assert result == {"FINISHED"}
    assert bpy.context.object == target
    assert selected_pose_bone_names(target) == ["TargetChild"]
    assert target.data.bones.active == target.data.bones["TargetChild"]
    assert first_row.active_target_link_index == 1


def test_live_solve_writes_same_visible_target_matrices_for_flat_and_parented_targets() -> None:
    clear_scene()

    flat_source = create_two_bone_armature("FlatSource", source_names())
    flat_target = create_two_bone_armature("FlatTarget", target_names(), parent_child=False)
    flat_profile = create_profile("FlatProfile", flat_source, flat_target)

    parented_source = create_two_bone_armature("ParentedSource", source_names())
    parented_target = create_two_bone_armature("ParentedTarget", target_names(), parent_child=True)
    parented_profile = create_profile("ParentedProfile", parented_source, parented_target)

    # Uniform scale keeps the result pose-channel-representable for both flat
    # and parented targets. Non-uniform parent scale plus child rotation can
    # create shear, which a flat Blender pose channel cannot store losslessly.
    set_pose(parented_source, parent_rotation_z=0.38, child_rotation_x=0.52, parent_scale=(1.5, 1.5, 1.5))
    set_pose(flat_source, parent_rotation_z=0.38, child_rotation_x=0.52, parent_scale=(1.5, 1.5, 1.5))

    solve_profile(flat_profile, flat_source, flat_target)
    solve_profile(parented_profile, parented_source, parented_target)

    assert_pose_matrices_close(
        visible_pose_matrices(flat_target, target_names()),
        visible_pose_matrices(parented_target, target_names()),
    )


def test_bake_replays_parented_target_visible_matrices() -> None:
    clear_scene()

    source = create_two_bone_armature("BakeSource", source_names())
    target = create_two_bone_armature("BakeTarget", target_names(), parent_child=True)
    profile = create_profile("BakeProfile", source, target)
    profile.bake_use_range_override = True
    profile.bake_frame_start = 1
    profile.bake_frame_end = 2

    action = bpy.data.actions.new("BakeSourceMotion")
    source.animation_data_create().action = action
    profile.active_motion_action = action
    key_source_pose(source, frame=1, parent_rotation_z=0.25, child_rotation_x=0.2, parent_scale=(1.2, 1.2, 1.2))
    key_source_pose(source, frame=2, parent_rotation_z=0.55, child_rotation_x=0.7, parent_scale=(1.4, 1.4, 1.4))
    work_pose.reset_source_pose_to_rest(bpy.context, target)

    expected_by_frame = {}
    for frame in (1, 2):
        bpy.context.scene.frame_set(frame)
        solve_profile(profile, source, target)
        expected_by_frame[frame] = visible_pose_matrices(target, target_names())

    written_keys, message = bake.bake_active_profile(bpy.context)
    assert written_keys > 0, message

    work_pose.reset_source_pose_to_rest(bpy.context, target)
    for frame in (1, 2):
        bpy.context.scene.frame_set(frame)
        bpy.context.view_layer.update()
        assert_pose_matrices_close(
            expected_by_frame[frame],
            visible_pose_matrices(target, target_names()),
        )


def test_clear_live_preview_resets_parented_target_to_bind_matrices() -> None:
    clear_scene()

    source = create_two_bone_armature("ClearSource", source_names())
    target = create_two_bone_armature("ClearTarget", target_names(), parent_child=True)
    profile = create_profile("ClearProfile", source, target)

    set_pose(source, parent_rotation_z=0.38, child_rotation_x=0.52, parent_scale=(1.5, 1.5, 1.5))
    solve_profile(profile, source, target)

    from bone_remap import live_preview

    reset_count, messages = live_preview.reset_target_channels_to_bind(
        bpy.context,
        target,
        list(target_names()),
    )
    errors = [message.text for message in messages if message.severity == "ERROR"]
    assert not errors, errors
    assert reset_count == 2
    assert_pose_matrices_close(
        {
            bone_name: target.data.bones[bone_name].matrix_local.copy()
            for bone_name in target_names()
        },
        visible_pose_matrices(target, target_names()),
    )


def clear_scene() -> None:
    bpy.ops.object.mode_set(mode="OBJECT") if bpy.context.object and bpy.context.object.mode != "OBJECT" else None
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()
    state.set_active_profile_index(bpy.context.scene, -1)


def source_names() -> tuple[str, str]:
    return ("SourceRoot", "SourceChild")


def target_names() -> tuple[str, str]:
    return ("TargetRoot", "TargetChild")


def create_profile(name: str, source, target):
    profile = state.create_profile(bpy.context.scene, name)
    profile.source_armature = source
    profile.target_armature = target
    save_rest_work_pose(profile, source)
    add_mapping(profile, "SourceRoot", "TargetRoot")
    add_mapping(profile, "SourceChild", "TargetChild")
    return profile


def create_two_bone_armature(name: str, bone_names: tuple[str, str], parent_child: bool = True):
    bpy.ops.object.armature_add()
    armature = bpy.context.object
    armature.name = name
    armature.data.name = f"{name}Data"

    bpy.ops.object.mode_set(mode="EDIT")
    edit_bones = armature.data.edit_bones
    root = edit_bones[0]
    root.name = bone_names[0]
    root.head = (0.0, 0.0, 0.0)
    root.tail = (0.0, 1.0, 0.0)

    child = edit_bones.new(bone_names[1])
    child.head = (0.0, 1.0, 0.0)
    child.tail = (0.0, 2.0, 0.0)
    if parent_child:
        child.parent = root
        child.use_connect = True

    bpy.ops.object.mode_set(mode="POSE")
    for pose_bone in armature.pose.bones:
        pose_bone.rotation_mode = "XYZ"
    bpy.ops.object.mode_set(mode="OBJECT")
    return armature


def create_bound_weighted_mesh(armature, name: str, weights_by_group: dict[str, list[tuple[int, float]]]):
    mesh_data = bpy.data.meshes.new(f"{name}Data")
    mesh_data.from_pydata(
        [(0.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 2.0, 0.0)],
        [],
        [],
    )
    mesh_data.update()
    mesh_obj = bpy.data.objects.new(name, mesh_data)
    bpy.context.collection.objects.link(mesh_obj)
    modifier = mesh_obj.modifiers.new("Armature", "ARMATURE")
    modifier.object = armature
    for group_name, weights in weights_by_group.items():
        group = mesh_obj.vertex_groups.new(name=group_name)
        for vertex_index, weight in weights:
            group.add([vertex_index], weight, "ADD")
    return mesh_obj


def save_rest_work_pose(profile, source) -> None:
    profile.work_pose_matrices.clear()
    for data_bone in source.data.bones:
        item = profile.work_pose_matrices.add()
        item.bone_name = data_bone.name
        item.matrix = work_pose.flatten_matrix(data_bone.matrix_local)
    profile.work_pose_saved = True


def add_mapping(profile, source_bone_name: str, target_bone_name: str) -> None:
    row = profile.mapping_rows.add()
    row.source_bone_name = source_bone_name
    link = row.target_links.add()
    link.target_bone_name = target_bone_name


def set_pose(source, parent_rotation_z: float, child_rotation_x: float, parent_scale=(1.0, 1.0, 1.0)) -> None:
    parent = source.pose.bones["SourceRoot"]
    child = source.pose.bones["SourceChild"]
    parent.rotation_euler = (0.0, 0.0, parent_rotation_z)
    parent.scale = parent_scale
    child.rotation_euler = (child_rotation_x, 0.0, 0.0)
    bpy.context.view_layer.update()


def key_source_pose(source, frame: int, parent_rotation_z: float, child_rotation_x: float, parent_scale=(1.0, 1.0, 1.0)) -> None:
    bpy.context.scene.frame_set(frame)
    set_pose(source, parent_rotation_z, child_rotation_x, parent_scale)
    for pose_bone in source.pose.bones:
        pose_bone.keyframe_insert(data_path="location", frame=frame)
        pose_bone.keyframe_insert(data_path="rotation_euler", frame=frame)
        pose_bone.keyframe_insert(data_path="scale", frame=frame)


def solve_profile(profile, source, target) -> None:
    result = solver.solve_profile_one_frame(bpy.context, profile, source, target)
    errors = [message.text for message in result.messages if message.severity == "ERROR"]
    assert not errors, errors
    assert result.written_targets == 2, result


def visible_pose_matrices(armature, bone_names: tuple[str, str]):
    evaluated = armature.evaluated_get(bpy.context.evaluated_depsgraph_get())
    return {
        bone_name: evaluated.pose.bones[bone_name].matrix.copy()
        for bone_name in bone_names
    }


def selected_pose_bone_names(armature) -> list[str]:
    return sorted(
        pose_bone.name
        for pose_bone in armature.pose.bones
        if pose_bone.select
    )


def assert_pose_matrices_close(expected, actual) -> None:
    for bone_name, expected_matrix in expected.items():
        actual_matrix = actual[bone_name]
        max_error = max(
            abs(expected_matrix[row][column] - actual_matrix[row][column])
            for row in range(4)
            for column in range(4)
        )
        assert max_error <= EPSILON, f"{bone_name} matrix error {max_error}"


if __name__ == "__main__":
    main()
