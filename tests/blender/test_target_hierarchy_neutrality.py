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
from mathutils import Matrix

import bone_remap
from bone_remap import auto_map, bake, mapping, solver, state, work_pose


EPSILON = 1.0e-5


def main() -> None:
    bone_remap.register()
    try:
        test_save_work_pose_leaves_source_visibly_in_saved_work_pose()
        test_save_work_pose_records_hidden_source_bones()
        test_solve_toggle_operator_is_single_source_of_live_solve_state()
        test_solve_toggle_writes_visible_target_result()
        test_live_solve_updates_after_source_pose_change()
        test_depsgraph_live_preview_skips_playback()
        test_depsgraph_live_preview_does_not_dirty_runtime_plan()
        test_live_apply_without_view_update_uses_notifying_pose_writes()
        test_partial_solve_only_writes_affected_target_scope()
        test_partial_solve_rewrites_descendant_target_scope()
        test_live_preview_ignores_target_only_updates()
        test_solve_toggle_rejects_profiles_that_write_no_targets()
        test_active_motion_action_selection_updates_source_action()
        test_source_actions_list_add_select_and_remove()
        test_source_action_selection_solves_live_preview_immediately()
        test_live_preview_rebinds_selected_source_action_when_animation_data_action_is_cleared()
        test_source_action_selection_preserves_imported_action_slot_under_work_pose_layer()
        test_playback_frame_handler_solves_live_preview()
        test_add_weighted_source_rows_uses_bound_mesh_vertex_groups()
        test_auto_match_visible_meshes_uses_shared_weighted_geometry()
        test_auto_match_visible_meshes_replaces_stale_mapping_rows()
        test_auto_match_pauses_live_preview_without_clearing_visible_target_pose()
        test_target_selection_syncs_active_source_row()
        test_assign_selected_targets_to_active_source_preserves_target_selection_after_source_row_click()
        test_mapping_row_activation_sets_active_source_without_stealing_target_selection()
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


def test_depsgraph_live_preview_skips_playback() -> None:
    clear_scene()

    source = create_two_bone_armature("PlaybackGateSource", source_names())
    target = create_two_bone_armature("PlaybackGateTarget", target_names())
    profile = create_profile("PlaybackGateProfile", source, target)
    profile.live_preview_enabled = True

    from bone_remap import live_preview

    solve_calls = []
    original_is_animation_playing = live_preview._is_animation_playing
    original_relevant = live_preview._depsgraph_update_relevant
    original_changed = live_preview._source_bone_names_changed
    original_solve_now = live_preview.solve_now

    def counted_solve_now(*args, **kwargs):
        solve_calls.append(kwargs.get("reason", "unknown"))
        return None

    live_preview._is_animation_playing = lambda context: True
    live_preview._depsgraph_update_relevant = lambda scene, depsgraph: True
    live_preview._source_bone_names_changed = lambda active_context, depsgraph: ("SourceRoot",)
    live_preview.solve_now = counted_solve_now
    try:
        live_preview._depsgraph_update_post(bpy.context.scene, bpy.context.evaluated_depsgraph_get())
    finally:
        live_preview._is_animation_playing = original_is_animation_playing
        live_preview._depsgraph_update_relevant = original_relevant
        live_preview._source_bone_names_changed = original_changed
        live_preview.solve_now = original_solve_now

    assert solve_calls == []


def test_depsgraph_live_preview_does_not_dirty_runtime_plan() -> None:
    clear_scene()

    source = create_two_bone_armature("PlanDirtySource", source_names())
    target = create_two_bone_armature("PlanDirtyTarget", target_names())
    profile = create_profile("PlanDirtyProfile", source, target)
    profile.live_preview_enabled = True

    from bone_remap import live_preview, runtime_plan

    invalidations = []
    original_is_animation_playing = live_preview._is_animation_playing
    original_relevant = live_preview._depsgraph_update_relevant
    original_changed = live_preview._source_bone_names_changed
    original_invalidate = runtime_plan.invalidate_runtime_plan

    live_preview._is_animation_playing = lambda context: False
    live_preview._depsgraph_update_relevant = lambda scene, depsgraph: True
    live_preview._source_bone_names_changed = lambda active_context, depsgraph: ()
    runtime_plan.invalidate_runtime_plan = lambda dirty_profile: invalidations.append(dirty_profile.name)
    try:
        live_preview._depsgraph_update_post(bpy.context.scene, bpy.context.evaluated_depsgraph_get())
    finally:
        live_preview._is_animation_playing = original_is_animation_playing
        live_preview._depsgraph_update_relevant = original_relevant
        live_preview._source_bone_names_changed = original_changed
        runtime_plan.invalidate_runtime_plan = original_invalidate

    assert invalidations == []


def test_live_apply_without_view_update_uses_notifying_pose_writes() -> None:
    clear_scene()

    target = create_two_bone_armature("NoBatchLiveTarget", target_names())
    matrix_by_bone = {
        "TargetRoot": Matrix.Rotation(0.25, 4, "Z"),
        "TargetChild": Matrix.Rotation(0.15, 4, "X"),
    }

    from bone_remap import pose_matrices

    original_min_bones = pose_matrices._BATCH_WRITE_MIN_BONES
    original_min_coverage = pose_matrices._BATCH_WRITE_MIN_COVERAGE
    pose_matrices._BATCH_WRITE_MIN_BONES = 1
    pose_matrices._BATCH_WRITE_MIN_COVERAGE = 0.0
    timings = {}
    try:
        written = pose_matrices.apply_pose_matrix_map(
            bpy.context,
            target,
            matrix_by_bone,
            update_view_layer=False,
            timings=timings,
        )
    finally:
        pose_matrices._BATCH_WRITE_MIN_BONES = original_min_bones
        pose_matrices._BATCH_WRITE_MIN_COVERAGE = original_min_coverage

    assert written == 2
    assert "apply_batch_write" not in timings


def test_partial_solve_only_writes_affected_target_scope() -> None:
    clear_scene()

    source = create_two_bone_armature("PartialSource", source_names())
    target = create_two_bone_armature("PartialTarget", target_names())
    profile = create_profile("PartialProfile", source, target)
    set_pose(source, parent_rotation_z=0.27, child_rotation_x=0.0, parent_scale=(1.3, 1.3, 1.3))
    solver.solve_profile_one_frame(bpy.context, profile, source, target)
    set_pose(source, parent_rotation_z=0.27, child_rotation_x=0.41, parent_scale=(1.3, 1.3, 1.3))

    written_target_maps = []

    from bone_remap import solver as solver_module, pose_matrices

    original_apply = pose_matrices.apply_pose_matrix_map

    def counted_apply(context, armature, pose_matrix_map, update_view_layer=True, timings=None, ordered_bone_names=None):
        written_target_maps.append(tuple(pose_matrix_map.keys()))
        return original_apply(
            context,
            armature,
            pose_matrix_map,
            update_view_layer=update_view_layer,
            timings=timings,
            ordered_bone_names=ordered_bone_names,
        )

    pose_matrices.apply_pose_matrix_map = counted_apply
    try:
        result = solver_module.solve_profile_one_frame(
            bpy.context,
            profile,
            source,
            target,
            source_bone_names={"SourceChild"},
        )
    finally:
        pose_matrices.apply_pose_matrix_map = original_apply

    assert result.written_targets == 1
    assert written_target_maps[-1] == ("TargetChild",)
    assert_pose_matrices_close(
        {
            "TargetChild": visible_pose_matrices(source, source_names())["SourceChild"],
        },
        visible_pose_matrices(target, target_names()),
    )


def test_partial_solve_rewrites_descendant_target_scope() -> None:
    clear_scene()

    source = create_two_bone_armature("ClosureSource", source_names())
    target = create_two_bone_armature("ClosureTarget", target_names(), parent_child=True)
    profile = create_profile("ClosureProfile", source, target)
    set_pose(source, parent_rotation_z=0.63, child_rotation_x=0.18, parent_scale=(1.2, 1.2, 1.2))

    from bone_remap import solver as solver_module, pose_matrices

    original_apply = pose_matrices.apply_pose_matrix_map
    written_target_maps = []

    def counted_apply(context, armature, pose_matrix_map, update_view_layer=True, timings=None, ordered_bone_names=None):
        written_target_maps.append(tuple(pose_matrix_map.keys()))
        return original_apply(
            context,
            armature,
            pose_matrix_map,
            update_view_layer=update_view_layer,
            timings=timings,
            ordered_bone_names=ordered_bone_names,
        )

    pose_matrices.apply_pose_matrix_map = counted_apply
    try:
        result = solver_module.solve_profile_one_frame(
            bpy.context,
            profile,
            source,
            target,
            source_bone_names={"SourceRoot"},
        )
    finally:
        pose_matrices.apply_pose_matrix_map = original_apply

    assert result.written_targets == 2
    assert set(written_target_maps[-1]) == {"TargetRoot", "TargetChild"}
    source_matrices = visible_pose_matrices(source, source_names())
    assert_pose_matrices_close(
        {
            "TargetRoot": source_matrices["SourceRoot"],
            "TargetChild": source_matrices["SourceChild"],
        },
        visible_pose_matrices(target, target_names()),
    )


def test_live_preview_ignores_target_only_updates() -> None:
    clear_scene()

    source = create_two_bone_armature("TargetOnlySource", source_names())
    target = create_two_bone_armature("TargetOnlyTarget", target_names())
    profile = create_profile("TargetOnlyProfile", source, target)

    from bone_remap import live_preview

    assert bpy.ops.bone_remap.live_preview_toggle() == {"FINISHED"}
    solve_calls = []
    original_solve_now = live_preview.solve_now

    def counted_solve_now(*args, **kwargs):
        solve_calls.append(1)
        return original_solve_now(*args, **kwargs)

    live_preview.solve_now = counted_solve_now
    try:
        target.pose.bones["TargetRoot"].location.x += 0.25
        bpy.context.view_layer.update()
    finally:
        live_preview.solve_now = original_solve_now

    assert solve_calls == []


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


def test_source_actions_list_add_select_and_remove() -> None:
    clear_scene()

    source = create_two_bone_armature("SourceActionsSource", source_names())
    target = create_two_bone_armature("SourceActionsTarget", target_names())
    profile = create_profile("SourceActionsProfile", source, target)
    action_a = bpy.data.actions.new("SourceActionA")
    action_b = bpy.data.actions.new("SourceActionB")

    source.animation_data_create().action = action_a
    assert bpy.ops.bone_remap.motion_action_add_current() == {"FINISHED"}
    assert len(source.brm_source_actions) == 1
    assert source.brm_source_actions[0].action == action_a
    assert source.brm_active_source_action_index == 0
    assert profile.active_motion_action == action_a

    assert bpy.ops.bone_remap.motion_action_add_current() == {"FINISHED"}
    assert len(source.brm_source_actions) == 1

    source.animation_data.action = action_b
    assert bpy.ops.bone_remap.motion_action_add_current() == {"FINISHED"}
    assert len(source.brm_source_actions) == 2
    assert source.brm_active_source_action_index == 1
    assert profile.active_motion_action == action_b

    source.brm_active_source_action_index = 0
    assert profile.active_motion_action == action_a
    assert source.animation_data.action == action_a

    assert bpy.ops.bone_remap.motion_action_remove() == {"FINISHED"}
    assert len(source.brm_source_actions) == 1
    assert source.brm_source_actions[0].action == action_b
    assert source.brm_active_source_action_index == 0
    assert profile.active_motion_action == action_b

    assert bpy.ops.bone_remap.motion_action_remove() == {"FINISHED"}
    assert len(source.brm_source_actions) == 0
    assert source.brm_active_source_action_index == -1
    assert profile.active_motion_action is None
    assert source.animation_data.action is None


def test_source_action_selection_solves_live_preview_immediately() -> None:
    clear_scene()

    source = create_two_bone_armature("ActionSwitchSource", source_names())
    target = create_two_bone_armature("ActionSwitchTarget", target_names())
    profile = create_profile("ActionSwitchProfile", source, target)
    action_a = bpy.data.actions.new("ActionSwitchA")
    action_b = bpy.data.actions.new("ActionSwitchB")

    source.animation_data_create().action = action_a
    key_source_pose(source, frame=2, parent_rotation_z=0.15, child_rotation_x=0.0)
    assert bpy.ops.bone_remap.motion_action_add_current() == {"FINISHED"}

    source.animation_data.action = action_b
    key_source_pose(source, frame=2, parent_rotation_z=0.75, child_rotation_x=0.0)
    assert bpy.ops.bone_remap.motion_action_add_current() == {"FINISHED"}

    profile.live_preview_enabled = True
    bpy.context.scene.frame_set(2)

    source.brm_active_source_action_index = 0
    target_a_z = target.pose.bones["TargetRoot"].rotation_euler.z

    source.brm_active_source_action_index = 1
    target_b_z = target.pose.bones["TargetRoot"].rotation_euler.z

    assert abs(target_a_z - 0.15) < 0.01
    assert abs(target_b_z - 0.75) < 0.01


def test_live_preview_rebinds_selected_source_action_when_animation_data_action_is_cleared() -> None:
    clear_scene()

    source = create_two_bone_armature("ActionRebindSource", source_names())
    target = create_two_bone_armature("ActionRebindTarget", target_names())
    profile = create_profile("ActionRebindProfile", source, target)
    action = bpy.data.actions.new("ActionRebindMotion")

    source.animation_data_create().action = action
    key_source_pose(source, frame=2, parent_rotation_z=0.65, child_rotation_x=0.0)
    assert bpy.ops.bone_remap.motion_action_add_current() == {"FINISHED"}

    source.animation_data.action = None
    profile.live_preview_enabled = True
    bpy.context.scene.frame_set(2)
    bpy.context.view_layer.update()

    assert source.animation_data.action == action
    assert abs(target.pose.bones["TargetRoot"].rotation_euler.z - 0.65) < 0.01


def test_source_action_selection_preserves_imported_action_slot_under_work_pose_layer() -> None:
    clear_scene()

    donor = create_two_bone_armature("ImportedActionRig", source_names())
    bpy.context.view_layer.objects.active = donor
    bpy.ops.object.mode_set(mode="POSE")
    key_source_pose(donor, frame=1, parent_rotation_z=0.0, child_rotation_x=0.0)
    key_source_pose(donor, frame=2, parent_rotation_z=0.6, child_rotation_x=0.4)
    imported_action = donor.animation_data.action
    assert imported_action is not None
    assert len(imported_action.slots) == 1

    bpy.ops.object.mode_set(mode="OBJECT")
    source = create_two_bone_armature("SlotSource", source_names())
    target = create_two_bone_armature("SlotTarget", target_names())
    profile = create_profile("SlotProfile", source, target)
    profile.live_preview_enabled = True

    source.animation_data_create().action = imported_action
    assert bpy.ops.bone_remap.motion_action_add_current() == {"FINISHED"}

    animation_data = source.animation_data
    assert animation_data is not None
    assert animation_data.action == imported_action
    assert animation_data.action_slot is not None

    bpy.context.scene.frame_set(2)
    bpy.context.view_layer.update()
    result = solver.solve_active_profile_one_frame(bpy.context)
    assert result.written_targets == 2
    assert abs(target.pose.bones["TargetRoot"].rotation_euler.z) > 0.1


def test_playback_frame_handler_solves_live_preview() -> None:
    clear_scene()

    source = create_two_bone_armature("PlaybackLiveSource", source_names())
    target = create_two_bone_armature("PlaybackLiveTarget", target_names())
    profile = create_profile("PlaybackLiveProfile", source, target)
    action = bpy.data.actions.new("PlaybackLiveMotion")
    source.animation_data_create().action = action
    profile.active_motion_action = action
    key_source_pose(source, frame=1, parent_rotation_z=0.1, child_rotation_x=0.0)
    key_source_pose(source, frame=2, parent_rotation_z=0.4, child_rotation_x=0.3)
    profile.live_preview_enabled = True

    from bone_remap import live_preview, solver as solver_module

    solve_calls = []
    original_is_animation_playing = live_preview._is_animation_playing
    original_solve_profile_one_frame = solver_module.solve_profile_one_frame

    def counted_solve_profile_one_frame(*args, **kwargs):
        solve_calls.append(1)
        return original_solve_profile_one_frame(*args, **kwargs)

    live_preview._is_animation_playing = lambda context: True
    solver_module.solve_profile_one_frame = counted_solve_profile_one_frame
    try:
        live_preview._frame_change_post(bpy.context.scene, bpy.context.evaluated_depsgraph_get())
    finally:
        live_preview._is_animation_playing = original_is_animation_playing
        solver_module.solve_profile_one_frame = original_solve_profile_one_frame

    assert solve_calls == [1]


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


def test_auto_match_pauses_live_preview_without_clearing_visible_target_pose() -> None:
    clear_scene()

    source = create_two_bone_armature("AutoMapPauseSource", source_names())
    target = create_two_bone_armature("AutoMapPauseTarget", target_names())
    profile = create_profile("AutoMapPauseProfile", source, target)
    profile.live_preview_enabled = True
    written = profile.live_preview_last_written_targets.add()
    written.target_bone_name = "TargetRoot"

    from bone_remap import live_preview

    clear_calls = []
    original_clear = live_preview.clear_live_preview
    live_preview.clear_live_preview = lambda *args, **kwargs: clear_calls.append((args, kwargs)) or (0, [])
    try:
        was_enabled = auto_map._pause_live_preview_for_target_sampling(profile)
    finally:
        live_preview.clear_live_preview = original_clear

    assert was_enabled is True
    assert profile.live_preview_enabled is False
    assert clear_calls == []


def test_target_selection_syncs_active_source_row() -> None:
    clear_scene()

    source = create_two_bone_armature("TargetSelectionSource", source_names())
    target = create_two_bone_armature("TargetSelectionTarget", target_names())
    profile = create_profile("TargetSelectionProfile", source, target)

    mapping.activate_armature_and_select_pose_bones(bpy.context, target, ["TargetChild"])
    mapping.sync_mapping_from_selection(bpy.context)

    assert profile.active_mapping_row_index == 1
    assert profile.mapping_rows[1].source_bone_name == "SourceChild"
    assert profile.mapping_rows[1].active_target_link_index == 0


def test_assign_selected_targets_to_active_source_preserves_target_selection_after_source_row_click() -> None:
    clear_scene()

    source = create_two_bone_armature("MoveTargetSource", source_names())
    target = create_two_bone_armature("MoveTargetTarget", target_names())
    profile = create_profile("MoveTargetProfile", source, target)

    mapping.activate_armature_and_select_pose_bones(bpy.context, target, ["TargetChild"])
    mapping.sync_mapping_from_selection(bpy.context)
    assert profile.active_mapping_row_index == 1

    assert bpy.ops.bone_remap.mapping_activate_source_row(mapping_index=0) == {"FINISHED"}
    mapping.sync_mapping_from_selection(bpy.context)
    assert profile.active_mapping_row_index == 0
    assert selected_pose_bone_names(target) == ["TargetChild"]

    assert bpy.ops.bone_remap.mapping_assign_selected_targets() == {"FINISHED"}
    owner_index, owner = mapping.find_owner_row(profile, "TargetChild")

    assert owner_index == 0
    assert owner.source_bone_name == "SourceRoot"
    assert [link.target_bone_name for link in profile.mapping_rows[0].target_links] == ["TargetRoot", "TargetChild"]
    assert [link.target_bone_name for link in profile.mapping_rows[1].target_links] == []


def test_mapping_row_activation_sets_active_source_without_stealing_target_selection() -> None:
    clear_scene()

    source = create_two_bone_armature("HighlightSource", source_names())
    target = create_two_bone_armature("HighlightTarget", target_names())
    profile = create_profile("HighlightProfile", source, target)
    mapping.activate_armature_and_select_pose_bones(bpy.context, target, ["TargetChild"])

    result = bpy.ops.bone_remap.mapping_activate_source_row(mapping_index=0)

    assert result == {"FINISHED"}
    assert bpy.context.object == target
    assert selected_pose_bone_names(target) == ["TargetChild"]
    assert target.data.bones.active == target.data.bones["TargetChild"]
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
