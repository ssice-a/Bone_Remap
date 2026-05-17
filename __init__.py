"""Blender add-on entrypoint for Bone Remap."""

bl_info = {
    "name": "Bone Remap",
    "author": "ssice-a",
    "version": (0, 1, 0),
    "blender": (4, 3, 0),
    "location": "View3D > Sidebar > Bone Remap",
    "description": "Realtime bone retargeting workbench for source and target armatures.",
    "category": "Animation",
}

if "bone_remap" in locals():
    import importlib

    importlib.reload(bone_remap)
else:
    from . import bone_remap


def register():
    bone_remap.register()


def unregister():
    bone_remap.unregister()
