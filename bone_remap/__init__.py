"""Bone Remap add-on package."""

if "properties" in locals():
    import importlib
    import sys

    for _module_name in (
        "registration",
        "action_fcurves",
        "action_slots",
        "state",
        "work_pose_layer",
        "pose_matrices",
        "weighted_geometry",
        "auto_match_core",
        "properties",
        "operators",
        "work_pose",
        "runtime_plan",
        "mapping",
        "solver",
        "live_preview",
        "motion_edit",
        "bake",
        "presets",
        "auto_map",
        "target_calibration",
        "binding",
        "ui",
    ):
        _module = sys.modules.get(f"{__name__}.{_module_name}") or locals().get(_module_name)
        if _module is not None:
            importlib.reload(_module)

from . import properties, operators, work_pose, runtime_plan, mapping, solver, live_preview, motion_edit, bake, presets, auto_map, target_calibration, binding, ui

_MODULES = (
    properties,
    operators,
    work_pose,
    mapping,
    solver,
    live_preview,
    motion_edit,
    bake,
    presets,
    auto_map,
    target_calibration,
    binding,
    ui,
)


def register():
    for module in _MODULES:
        module.register()


def unregister():
    for module in reversed(_MODULES):
        module.unregister()
    runtime_plan.clear_runtime_plan_cache()
