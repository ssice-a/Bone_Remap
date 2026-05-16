"""Blender class registration helpers for reload-friendly add-on modules."""

from __future__ import annotations

import bpy


def register_classes(classes) -> None:
    for cls in classes:
        _unregister_stale_class(cls)
        if not _is_registered_class(cls):
            bpy.utils.register_class(cls)


def unregister_classes(classes) -> None:
    for cls in reversed(classes):
        if _is_registered_class(cls):
            bpy.utils.unregister_class(cls)
            continue
        _unregister_stale_class(cls)


def _unregister_stale_class(cls) -> None:
    registered = getattr(bpy.types, cls.__name__, None)
    if registered is None or registered is cls or not _is_registered_class(registered):
        return
    bpy.utils.unregister_class(registered)


def _is_registered_class(cls) -> bool:
    return bool(getattr(cls, "is_registered", False))
