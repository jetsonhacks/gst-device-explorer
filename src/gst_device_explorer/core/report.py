"""System report builder."""

from __future__ import annotations

from gst_device_explorer.core.models import (
    Capability,
    CompositeDevice,
    Device,
    DeviceProfile,
    EnvironmentFact,
    ReportDevices,
    ReportDiagnostics,
    ReportProfiles,
    SystemReport,
)
import gst_device_explorer.core.profiles as profiles_mod


def build_system_report(
    video_devices: list[Device],
    audio_input_devices: list[Device],
    audio_output_devices: list[Device],
    groups: list[CompositeDevice],
    environment: list[EnvironmentFact],
    video_capabilities: dict[str, list[Capability]],
    tool_version: str,
) -> SystemReport:
    """Build a system report from already-gathered discovery facts."""

    video_profiles = _build_video_profiles(
        video_devices, video_capabilities, environment, groups
    )
    audio_input_profiles = _build_audio_input_profiles(
        audio_input_devices, environment, groups
    )
    audio_output_profiles = _build_audio_output_profiles(
        audio_output_devices, environment, groups
    )

    all_profiles = video_profiles + audio_input_profiles + audio_output_profiles
    missing_elements = _aggregate_missing_elements(all_profiles)
    suggested_next_commands = _aggregate_suggested_commands(all_profiles)

    return SystemReport(
        kind="system_report",
        tool_version=tool_version,
        environment=environment,
        devices=ReportDevices(
            video=video_devices,
            audio_inputs=audio_input_devices,
            audio_outputs=audio_output_devices,
        ),
        groups=groups,
        profiles=ReportProfiles(
            video=video_profiles,
            audio_inputs=audio_input_profiles,
            audio_outputs=audio_output_profiles,
        ),
        diagnostics=ReportDiagnostics(
            missing_elements=missing_elements,
        ),
        suggested_next_commands=suggested_next_commands,
    )


def _build_video_profiles(
    devices: list[Device],
    video_capabilities: dict[str, list[Capability]],
    environment: list[EnvironmentFact],
    groups: list[CompositeDevice],
) -> list[DeviceProfile]:
    result: list[DeviceProfile] = []
    for device in devices:
        caps = video_capabilities.get(device.id, [])
        profile = profiles_mod.build_video_profile(device, caps, environment, groups)
        if profile is not None:
            result.append(profile)
    return result


def _build_audio_input_profiles(
    devices: list[Device],
    environment: list[EnvironmentFact],
    groups: list[CompositeDevice],
) -> list[DeviceProfile]:
    result: list[DeviceProfile] = []
    for device in devices:
        profile = profiles_mod.build_audio_input_profile(device, environment, groups)
        if profile is not None:
            result.append(profile)
    return result


def _build_audio_output_profiles(
    devices: list[Device],
    environment: list[EnvironmentFact],
    groups: list[CompositeDevice],
) -> list[DeviceProfile]:
    result: list[DeviceProfile] = []
    for device in devices:
        profile = profiles_mod.build_audio_output_profile(device, environment, groups)
        if profile is not None:
            result.append(profile)
    return result


def _aggregate_missing_elements(device_profiles: list[DeviceProfile]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for profile in device_profiles:
        for candidate in profile.candidate_summary.get("unavailable", []):
            for element in candidate.missing_elements:
                if element not in seen:
                    seen.add(element)
                    result.append(element)
    return result


def _aggregate_suggested_commands(device_profiles: list[DeviceProfile]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for profile in device_profiles:
        for command in profile.suggested_next_commands:
            if command not in seen:
                seen.add(command)
                result.append(command)
    return result
