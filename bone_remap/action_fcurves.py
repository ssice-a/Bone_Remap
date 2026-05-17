"""Action F-Curve helpers for legacy and Blender 5 layered actions."""

from __future__ import annotations


def iter_action_fcurve_owners(action):
    legacy_fcurves = getattr(action, "fcurves", None)
    if legacy_fcurves is not None:
        for fcurve in list(legacy_fcurves):
            yield legacy_fcurves, fcurve
        return

    for layer in getattr(action, "layers", ()):
        for strip in getattr(layer, "strips", ()):
            for channelbag in getattr(strip, "channelbags", ()):
                fcurves = getattr(channelbag, "fcurves", None)
                if fcurves is None:
                    continue
                for fcurve in list(fcurves):
                    yield fcurves, fcurve


def iter_action_fcurves(action):
    for _owner, fcurve in iter_action_fcurve_owners(action):
        yield fcurve


def ensure_action_fcurve_for_datablock(action, datablock, data_path: str, index: int):
    ensure_for_datablock = getattr(action, "fcurve_ensure_for_datablock", None)
    if ensure_for_datablock is not None:
        return ensure_for_datablock(datablock, data_path, index=index)

    fcurves = getattr(action, "fcurves", None)
    if fcurves is None:
        raise RuntimeError("Action does not expose F-Curve creation API.")

    fcurve = fcurves.find(data_path, index=index)
    if fcurve is not None:
        return fcurve
    return fcurves.new(data_path=data_path, index=index)


def remove_action_fcurve(owner, fcurve) -> None:
    owner.remove(fcurve)


def clear_action_fcurves(action) -> None:
    for owner, fcurve in list(iter_action_fcurve_owners(action)):
        remove_action_fcurve(owner, fcurve)
