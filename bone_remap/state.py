"""State helpers for the Active Retarget Profile."""

from __future__ import annotations

from dataclasses import dataclass

from .properties import ACTIVE_PROFILE_INDEX_ATTR, PROFILE_COLLECTION_ATTR


@dataclass(frozen=True)
class ValidationMessage:
    severity: str
    text: str


@dataclass(frozen=True)
class ActiveProfileContext:
    profile: object
    source_armature: object
    target_armature: object


def get_profiles(scene):
    return getattr(scene, PROFILE_COLLECTION_ATTR)


def get_active_profile_index(scene) -> int:
    return getattr(scene, ACTIVE_PROFILE_INDEX_ATTR)


def set_active_profile_index(scene, index: int) -> None:
    profiles = get_profiles(scene)
    if not profiles:
        setattr(scene, ACTIVE_PROFILE_INDEX_ATTR, -1)
        return

    clamped = max(0, min(index, len(profiles) - 1))
    setattr(scene, ACTIVE_PROFILE_INDEX_ATTR, clamped)


def get_active_profile(scene):
    profiles = get_profiles(scene)
    index = get_active_profile_index(scene)
    if 0 <= index < len(profiles):
        return profiles[index]
    return None


def create_profile(scene, name: str | None = None):
    profiles = get_profiles(scene)
    profile = profiles.add()
    profile.name = name or _next_profile_name(profiles)
    set_active_profile_index(scene, len(profiles) - 1)
    return profile


def remove_active_profile(scene) -> bool:
    profiles = get_profiles(scene)
    index = get_active_profile_index(scene)
    if not (0 <= index < len(profiles)):
        return False

    profiles.remove(index)
    if profiles:
        set_active_profile_index(scene, min(index, len(profiles) - 1))
    else:
        set_active_profile_index(scene, -1)
    return True


def validate_profile(profile) -> list[ValidationMessage]:
    messages: list[ValidationMessage] = []
    if profile is None:
        return [ValidationMessage("ERROR", "No Active Retarget Profile.")]

    source = profile.source_armature
    target = profile.target_armature

    if source is None:
        messages.append(ValidationMessage("ERROR", "Source Armature is not assigned."))
    elif source.type != "ARMATURE":
        messages.append(ValidationMessage("ERROR", "Source Armature reference is not an armature."))

    if target is None:
        messages.append(ValidationMessage("ERROR", "Target Armature is not assigned."))
    elif target.type != "ARMATURE":
        messages.append(ValidationMessage("ERROR", "Target Armature reference is not an armature."))

    if source is not None and target is not None and source == target:
        messages.append(ValidationMessage("ERROR", "Source Armature and Target Armature must be different objects."))

    if not messages:
        messages.append(ValidationMessage("INFO", "Active Retarget Profile is valid."))

    return messages


def validate_active_profile(scene) -> list[ValidationMessage]:
    return validate_profile(get_active_profile(scene))


def get_active_profile_context(scene) -> ActiveProfileContext | None:
    profile = get_active_profile(scene)
    if profile is None:
        return None

    messages = validate_profile(profile)
    if any(message.severity == "ERROR" for message in messages):
        return None

    return ActiveProfileContext(
        profile=profile,
        source_armature=profile.source_armature,
        target_armature=profile.target_armature,
    )


def _next_profile_name(profiles) -> str:
    base_name = "Retarget Profile"
    existing = {profile.name for profile in profiles}
    if base_name not in existing:
        return base_name

    suffix = 2
    while True:
        candidate = f"{base_name} {suffix}"
        if candidate not in existing:
            return candidate
        suffix += 1
