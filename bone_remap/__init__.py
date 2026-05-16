"""Bone Remap add-on package."""

from . import properties, operators, work_pose, runtime_plan, mapping, solver, live_preview, motion_edit, bake, presets, auto_map, target_calibration, ui

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
    ui,
)


def register():
    for module in _MODULES:
        module.register()


def unregister():
    for module in reversed(_MODULES):
        module.unregister()
    runtime_plan.clear_runtime_plan_cache()
