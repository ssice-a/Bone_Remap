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


def remove_action_fcurve(owner, fcurve) -> None:
    owner.remove(fcurve)


def clear_action_fcurves(action) -> None:
    for owner, fcurve in list(iter_action_fcurve_owners(action)):
        remove_action_fcurve(owner, fcurve)
