"""Command handlers for gst-device-explorer CLI."""

from __future__ import annotations

from gst_device_explorer import __version__
from gst_device_explorer.core.models import (
    CompositeDevice,
    Device,
    DeviceProfile,
    PipelineCandidate,
    PipelineDiagnostic,
    SystemReport,
)
import gst_device_explorer.core.audio_diagnostics as audio_diagnostics
import gst_device_explorer.core.audio_pipelines as audio_pipelines
import gst_device_explorer.core.discovery as discovery
import gst_device_explorer.core.execution as execution
import gst_device_explorer.core.pipelines as pipelines
import gst_device_explorer.core.profiles as profiles
import gst_device_explorer.core.report as core_report
import gst_device_explorer.core.video_diagnostics as video_diagnostics
import gst_device_explorer.probes.alsa as alsa_probe
import gst_device_explorer.probes.gst as gst_probe
import gst_device_explorer.probes.v4l2 as v4l2_probe
from gst_device_explorer.cli.renderer import print_execution_plan


def build_video_preview_candidates(device_path: str) -> list[PipelineCandidate]:
    device = Device(
        id=device_path,
        kind="video_input",
        name=device_path,
        metadata={"backend": "v4l2", "path": device_path},
    )
    capabilities = v4l2_probe.discover_v4l2_capabilities(device_path)
    environment = gst_probe.inspect_gstreamer_environment()
    return pipelines.build_video_preview_candidates(device, capabilities, environment)


def build_video_preview_diagnostics(device_path: str) -> list[PipelineDiagnostic]:
    device = Device(
        id=device_path,
        kind="video_input",
        name=device_path,
        metadata={"backend": "v4l2", "path": device_path},
    )
    capabilities = v4l2_probe.discover_v4l2_capabilities(device_path)
    environment = gst_probe.inspect_gstreamer_environment()
    return video_diagnostics.build_video_preview_diagnostics(
        device, capabilities, environment
    )


def build_video_profile(device_path: str) -> DeviceProfile | None:
    device = Device(
        id=device_path,
        kind="video_input",
        name=device_path,
        metadata={"backend": "v4l2", "path": device_path},
    )
    capabilities = v4l2_probe.discover_v4l2_capabilities(device_path)
    environment = gst_probe.inspect_gstreamer_environment()
    groups = _discover_profile_groups()
    return profiles.build_video_profile(device, capabilities, environment, groups)


def build_audio_input_test_candidates(alsa_device: str) -> list[PipelineCandidate]:
    device = _find_alsa_device(
        alsa_probe.discover_alsa_audio_inputs(), alsa_device, kind="audio_input"
    )
    if device is None:
        return []
    environment = gst_probe.inspect_gstreamer_environment()
    return audio_pipelines.build_audio_input_test_candidates(device, environment)


def build_audio_input_test_diagnostics(alsa_device: str) -> list[PipelineDiagnostic]:
    device = _find_alsa_device(
        alsa_probe.discover_alsa_audio_inputs(), alsa_device, kind="audio_input"
    )
    if device is None:
        return []
    environment = gst_probe.inspect_gstreamer_environment()
    return audio_diagnostics.build_audio_input_test_diagnostics(device, environment)


def build_audio_input_profile(alsa_device: str) -> DeviceProfile | None:
    device = _find_alsa_device(
        alsa_probe.discover_alsa_audio_inputs(), alsa_device, kind="audio_input"
    )
    if device is None:
        return None
    environment = gst_probe.inspect_gstreamer_environment()
    groups = _discover_profile_groups()
    return profiles.build_audio_input_profile(device, environment, groups)


def build_audio_output_test_candidates(alsa_device: str) -> list[PipelineCandidate]:
    device = _find_alsa_device(
        alsa_probe.discover_alsa_audio_outputs(), alsa_device, kind="audio_output"
    )
    if device is None:
        return []
    environment = gst_probe.inspect_gstreamer_environment()
    return audio_pipelines.build_audio_output_test_candidates(device, environment)


def build_audio_output_test_diagnostics(
    alsa_device: str,
) -> list[PipelineDiagnostic]:
    device = _find_alsa_device(
        alsa_probe.discover_alsa_audio_outputs(), alsa_device, kind="audio_output"
    )
    if device is None:
        return []
    environment = gst_probe.inspect_gstreamer_environment()
    return audio_diagnostics.build_audio_output_test_diagnostics(device, environment)


def build_audio_output_profile(alsa_device: str) -> DeviceProfile | None:
    device = _find_alsa_device(
        alsa_probe.discover_alsa_audio_outputs(), alsa_device, kind="audio_output"
    )
    if device is None:
        return None
    environment = gst_probe.inspect_gstreamer_environment()
    groups = _discover_profile_groups()
    return profiles.build_audio_output_profile(device, environment, groups)


def run_selected_candidate(
    candidates: list[PipelineCandidate],
    device_label: str,
    inspect_commands: list[str],
    selection: str | None,
    dry_run: bool,
) -> int:
    if not candidates:
        print(f"No pipeline candidates were generated for {device_label}.")
        print()
        print("Try:")
        for command in inspect_commands:
            print(f"  {command}")
        print("  gst-device-explorer env")
        return 1

    try:
        candidate = execution.select_pipeline_candidate(candidates, selection=selection)
    except execution.CandidateSelectionError as error:
        print(f"Error: {error}")
        return 1

    plan = execution.create_execution_plan(candidate)
    print_execution_plan(plan, dry_run=dry_run)

    if dry_run:
        return 0

    try:
        return execution.run_execution_plan(plan)
    except execution.ExecutionStartError as error:
        print(f"Error: could not start pipeline: {error}")
        return 1


def _find_alsa_device(
    devices: list[Device],
    alsa_device: str,
    kind: str,
) -> Device | None:
    return next(
        (
            device
            for device in devices
            if device.kind == kind
            and (
                device.id == alsa_device
                or device.metadata.get("alsa_device") == alsa_device
            )
        ),
        None,
    )


def build_system_report() -> SystemReport:
    """Build a system report from all probes and builders."""

    video_devices = v4l2_probe.discover_v4l2_video_devices()
    audio_input_devices = alsa_probe.discover_alsa_audio_inputs()
    audio_output_devices = alsa_probe.discover_alsa_audio_outputs()
    environment = gst_probe.inspect_gstreamer_environment()
    groups = discovery.discover_composite_devices()

    video_capabilities = {
        device.id: v4l2_probe.discover_v4l2_capabilities(device.id)
        for device in video_devices
    }

    return core_report.build_system_report(
        video_devices=video_devices,
        audio_input_devices=audio_input_devices,
        audio_output_devices=audio_output_devices,
        groups=groups,
        environment=environment,
        video_capabilities=video_capabilities,
        tool_version=__version__,
    )


def _discover_profile_groups() -> list[CompositeDevice]:
    return discovery.discover_composite_devices()
