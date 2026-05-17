"""Blender 5 Action Slot helpers."""

from __future__ import annotations


def slot_identity(action_slot) -> tuple[str, str]:
    if action_slot is None:
        return "", ""
    return (
        str(getattr(action_slot, "identifier", "") or ""),
        str(getattr(action_slot, "name_display", getattr(action_slot, "name", "")) or ""),
    )


def pick_matching_action_slot(action_slots, preferred_slot=None):
    slots = tuple(action_slots) if action_slots is not None else ()
    if not slots:
        return None

    preferred_identifier, preferred_name = slot_identity(preferred_slot)
    if preferred_identifier or preferred_name:
        for action_slot in slots:
            action_slot_identifier, action_slot_name = slot_identity(action_slot)
            if preferred_identifier and action_slot_identifier == preferred_identifier:
                return action_slot
            if preferred_name and action_slot_name == preferred_name:
                return action_slot

    return slots[0]


def sync_action_slot(target, preferred_slot=None, force: bool = False):
    if target is None or not hasattr(target, "action_slot"):
        return None

    suitable_slots = getattr(target, "action_suitable_slots", None)
    action_slot = pick_matching_action_slot(suitable_slots, preferred_slot)
    if action_slot is None:
        action = getattr(target, "action", None)
        action_slots = getattr(action, "slots", None) if action is not None else None
        action_slot = pick_matching_action_slot(suitable_slots, getattr(action_slots, "active", None))
    if action_slot is None:
        return None

    try:
        target.action_slot = action_slot
    except Exception:
        return None
    return action_slot


def clear_action_slot(target) -> None:
    if target is None or not hasattr(target, "action_slot"):
        return
    try:
        target.action_slot = None
    except Exception:
        pass
