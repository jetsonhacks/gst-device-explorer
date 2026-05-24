"""Command handlers for gst-device-explorer CLI."""

from __future__ import annotations

import datetime
import io
import json
from contextlib import redirect_stdout
from pathlib import Path

from gst_device_explorer import __version__
from gst_device_explorer.core.models import (
    CandidateRanking,
    CompositeDevice,
    Device,
    DeviceRef,
    DeviceProfile,
    GroupValidation,
    PipelineCandidate,
    PipelineDiagnostic,
    SystemReport,
)
from gst_device_explorer.core.schema import JSON_SCHEMA_VERSION, wrap_json
from gst_device_explorer.core.support import (
    SupportBundleFile,
    SupportBundleManifest,
    validate_bundle_output_path,
)
from gst_device_explorer.core.tui import (
    TuiReviewModel,
    build_tui_review_model,
    render_overview_lines,
)
import gst_device_explorer.core.audio_diagnostics as audio_diagnostics
import gst_device_explorer.core.audio_pipelines as audio_pipelines
import gst_device_explorer.core.capture as capture
import gst_device_explorer.core.config as config
import gst_device_explorer.core.discovery as discovery
import gst_device_explorer.core.execution as execution
import gst_device_explorer.core.pipelines as pipelines
import gst_device_explorer.core.presets as presets
import gst_device_explorer.core.profiles as profiles
import gst_device_explorer.core.ranking as ranking
import gst_device_explorer.core.report as core_report
import gst_device_explorer.core.schema as schema_mod
import gst_device_explorer.core.suggestions as suggestions_mod
import gst_device_explorer.core.validation as validation
import gst_device_explorer.core.video_diagnostics as video_diagnostics
import gst_device_explorer.probes.alsa as alsa_probe
import gst_device_explorer.probes.gst as gst_probe
import gst_device_explorer.probes.v4l2 as v4l2_probe
from gst_device_explorer.cli.renderer import (
    print_capture_completed,
    print_capture_plan,
    print_execution_plan,
    print_support_bundle_written,
    print_system_report,
)
from gst_device_explorer.cli.serializers import (
    config_validation_result_to_json_dict,
    schema_document_summary_to_json_dict,
    suggested_command_to_json_dict,
    support_bundle_manifest_to_json_dict,
    system_report_to_json_dict,
    to_json_data,
)


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


def build_video_capture_candidates(
    device_path: str,
    duration_seconds: float,
    output_path: str,
) -> list[PipelineCandidate]:
    device = Device(
        id=device_path,
        kind="video_input",
        name=device_path,
        metadata={"backend": "v4l2", "path": device_path},
    )
    capabilities = v4l2_probe.discover_v4l2_capabilities(device_path)
    environment = gst_probe.inspect_gstreamer_environment()
    return capture.build_video_capture_candidates(
        device,
        capabilities,
        environment,
        duration_seconds,
        capture.validate_capture_output_path(output_path),
    )


def build_audio_input_capture_candidates(
    alsa_device: str,
    duration_seconds: float,
    output_path: str,
) -> list[PipelineCandidate]:
    device = _find_alsa_device(
        alsa_probe.discover_alsa_audio_inputs(), alsa_device, kind="audio_input"
    )
    if device is None:
        return []
    environment = gst_probe.inspect_gstreamer_environment()
    return capture.build_audio_input_capture_candidates(
        device,
        environment,
        duration_seconds,
        capture.validate_capture_output_path(output_path),
    )


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


def run_capture_candidate(
    candidates: list[PipelineCandidate],
    endpoint: str,
    duration_seconds: float,
    output_path: str,
    inspect_commands: list[str],
    selection: str | None,
    dry_run: bool,
) -> int:
    if not candidates:
        print(f"No capture candidates were generated for {endpoint}.")
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
    print_capture_plan(
        plan,
        endpoint=endpoint,
        duration_seconds=duration_seconds,
        output_path=output_path,
        dry_run=dry_run,
    )

    if dry_run:
        return 0

    try:
        exit_code = execution.run_execution_plan(
            plan,
            timeout_seconds=duration_seconds + 5.0,
        )
    except execution.ExecutionStartError as error:
        print(f"Error: could not start capture pipeline: {error}")
        return 1

    if exit_code == 0:
        print_capture_completed()
    return exit_code


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


def build_video_recommendation(device_path: str) -> CandidateRanking:
    """Build a ranked recommendation for a V4L2 video endpoint."""
    device = Device(
        id=device_path,
        kind="video_input",
        name=device_path,
        metadata={"backend": "v4l2", "path": device_path},
    )
    capabilities = v4l2_probe.discover_v4l2_capabilities(device_path)
    environment = gst_probe.inspect_gstreamer_environment()
    candidates = pipelines.build_video_preview_candidates(device, capabilities, environment)
    diagnostics = video_diagnostics.build_video_preview_diagnostics(
        device, capabilities, environment
    )
    return ranking.rank_candidates(candidates, diagnostics, "video", device_path)


def build_audio_input_recommendation(alsa_device: str) -> CandidateRanking:
    """Build a ranked recommendation for an ALSA audio input endpoint."""
    device = _find_alsa_device(
        alsa_probe.discover_alsa_audio_inputs(), alsa_device, kind="audio_input"
    )
    if device is None:
        return ranking.empty_ranking("audio-input", alsa_device)
    environment = gst_probe.inspect_gstreamer_environment()
    candidates = audio_pipelines.build_audio_input_test_candidates(device, environment)
    diagnostics = audio_diagnostics.build_audio_input_test_diagnostics(device, environment)
    return ranking.rank_candidates(candidates, diagnostics, "audio-input", alsa_device)


def build_audio_output_recommendation(alsa_device: str) -> CandidateRanking:
    """Build a ranked recommendation for an ALSA audio output endpoint."""
    device = _find_alsa_device(
        alsa_probe.discover_alsa_audio_outputs(), alsa_device, kind="audio_output"
    )
    if device is None:
        return ranking.empty_ranking("audio-output", alsa_device)
    environment = gst_probe.inspect_gstreamer_environment()
    candidates = audio_pipelines.build_audio_output_test_candidates(device, environment)
    diagnostics = audio_diagnostics.build_audio_output_test_diagnostics(device, environment)
    return ranking.rank_candidates(candidates, diagnostics, "audio-output", alsa_device)


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


def build_group_validation(group_id: str) -> GroupValidation | None:
    """Build a validation summary for one discovered composite group."""

    groups = discovery.discover_composite_devices()
    group = _find_group(groups, group_id)
    if group is None:
        return None

    environment = gst_probe.inspect_gstreamer_environment()
    video_devices = v4l2_probe.discover_v4l2_video_devices()
    audio_input_devices = alsa_probe.discover_alsa_audio_inputs()
    audio_output_devices = alsa_probe.discover_alsa_audio_outputs()

    endpoint_profiles: list[DeviceProfile] = []
    for member in group.members:
        if member.role == "camera":
            device = _find_video_device(video_devices, member)
            if device is None:
                continue
            capabilities = v4l2_probe.discover_v4l2_capabilities(device.id)
            profile = profiles.build_video_profile(
                device,
                capabilities,
                environment,
                groups,
            )
        elif member.role == "audio-input":
            device = _find_device(audio_input_devices, member)
            profile = (
                profiles.build_audio_input_profile(device, environment, groups)
                if device is not None
                else None
            )
        elif member.role == "audio-output":
            device = _find_device(audio_output_devices, member)
            profile = (
                profiles.build_audio_output_profile(device, environment, groups)
                if device is not None
                else None
            )
        else:
            profile = None

        if profile is not None:
            endpoint_profiles.append(profile)

    return validation.build_group_validation(group, endpoint_profiles)


def _discover_profile_groups() -> list[CompositeDevice]:
    return discovery.discover_composite_devices()


def _find_group(groups: list[CompositeDevice], group_id: str) -> CompositeDevice | None:
    return next((group for group in groups if group.id == group_id), None)


def _find_video_device(devices: list[Device], member: DeviceRef) -> Device | None:
    return next(
        (
            device
            for device in devices
            if device.kind == "video_input"
            and (
                device.id == member.device_id
                or device.id == member.path
                or device.metadata.get("path") == member.path
            )
        ),
        None,
    )


def _find_device(devices: list[Device], member: DeviceRef) -> Device | None:
    return next(
        (
            device
            for device in devices
            if device.id == member.device_id
            or device.id == member.path
            or device.metadata.get("alsa_device") == member.path
            or device.metadata.get("alsa_device") == member.device_id
        ),
        None,
    )


def run_support_bundle(output_path_str: str) -> int:
    """Create a support bundle directory at the given output path."""
    output_path = Path(output_path_str)

    try:
        validate_bundle_output_path(output_path)
    except FileExistsError as error:
        print(f"Error: {error}")
        return 1
    except ValueError as error:
        print(f"Error: {error}")
        return 1

    written_files: list[SupportBundleFile] = []
    bundle_warnings: list[str] = []

    report = build_system_report()
    config_result = config.effective_config()
    config_paths = config.config_search_paths()
    schema_documents = schema_mod.list_schema_documents()
    suggestions = suggestions_mod.list_generic_suggestions()
    groupable_devices = discovery.discover_groupable_devices()

    try:
        output_path.mkdir(parents=False)
    except OSError as error:
        print(f"Error: Could not create bundle directory: {error}")
        return 1

    report_dir = output_path / "report"
    report_dir.mkdir()

    _write_bundle_json(
        report_dir / "system-report.json",
        wrap_json("system_report", system_report_to_json_dict(report)),
        written_files,
        bundle_warnings,
        rel_path="report/system-report.json",
        kind="json",
        description="Full system report.",
        required=True,
    )

    try:
        buf = io.StringIO()
        with redirect_stdout(buf):
            print_system_report(report, as_json=False)
        (report_dir / "system-report.txt").write_text(buf.getvalue())
        written_files.append(SupportBundleFile(
            path="report/system-report.txt",
            kind="text",
            description="System report text summary.",
            required=False,
        ))
    except OSError as error:
        bundle_warnings.append(f"Could not write report/system-report.txt: {error}")

    inventory_dir = output_path / "inventory"
    inventory_dir.mkdir()

    all_devices = (
        list(report.devices.video)
        + list(report.devices.audio_inputs)
        + list(report.devices.audio_outputs)
    )
    _write_bundle_json(
        inventory_dir / "environment.json",
        wrap_json("environment", to_json_data(report.environment)),
        written_files,
        bundle_warnings,
        rel_path="inventory/environment.json",
        kind="json",
        description="GStreamer environment facts.",
        required=False,
    )
    _write_bundle_json(
        inventory_dir / "devices.json",
        wrap_json("devices", to_json_data(all_devices)),
        written_files,
        bundle_warnings,
        rel_path="inventory/devices.json",
        kind="json",
        description="All discovered devices.",
        required=False,
    )
    _write_bundle_json(
        inventory_dir / "audio-inputs.json",
        wrap_json("audio_inputs", to_json_data(list(report.devices.audio_inputs))),
        written_files,
        bundle_warnings,
        rel_path="inventory/audio-inputs.json",
        kind="json",
        description="Discovered ALSA audio input devices.",
        required=False,
    )
    _write_bundle_json(
        inventory_dir / "audio-outputs.json",
        wrap_json("audio_outputs", to_json_data(list(report.devices.audio_outputs))),
        written_files,
        bundle_warnings,
        rel_path="inventory/audio-outputs.json",
        kind="json",
        description="Discovered ALSA audio output devices.",
        required=False,
    )
    _write_bundle_json(
        inventory_dir / "groups.json",
        wrap_json("composite_groups", to_json_data(list(report.groups))),
        written_files,
        bundle_warnings,
        rel_path="inventory/groups.json",
        kind="json",
        description="Discovered composite device groups.",
        required=False,
    )
    _write_bundle_json(
        inventory_dir / "grouping-metadata.json",
        wrap_json("grouping_metadata", to_json_data(groupable_devices)),
        written_files,
        bundle_warnings,
        rel_path="inventory/grouping-metadata.json",
        kind="json",
        description="Raw grouping metadata records.",
        required=False,
    )

    config_dir = output_path / "config"
    config_dir.mkdir()

    config_paths_data = {
        "applied": False,
        "paths": [str(p) for p in config_paths],
        "required": False,
    }
    _write_bundle_json(
        config_dir / "config-path.json",
        wrap_json("config_path", config_paths_data),
        written_files,
        bundle_warnings,
        rel_path="config/config-path.json",
        kind="json",
        description="Configuration search paths.",
        required=False,
    )
    _write_bundle_json(
        config_dir / "config-show.json",
        wrap_json("config_show", config_validation_result_to_json_dict(config_result)),
        written_files,
        bundle_warnings,
        rel_path="config/config-show.json",
        kind="json",
        description="Effective configuration.",
        required=False,
    )
    _write_bundle_json(
        config_dir / "config-validate.json",
        wrap_json("config_validate", config_validation_result_to_json_dict(config_result)),
        written_files,
        bundle_warnings,
        rel_path="config/config-validate.json",
        kind="json",
        description="Configuration validation result.",
        required=False,
    )

    schemas_dir = output_path / "schemas"
    schemas_dir.mkdir()

    _write_bundle_json(
        schemas_dir / "schema-list.json",
        wrap_json(
            "schema_list",
            {"schemas": [schema_document_summary_to_json_dict(d) for d in schema_documents]},
        ),
        written_files,
        bundle_warnings,
        rel_path="schemas/schema-list.json",
        kind="json",
        description="Known schema document list.",
        required=False,
    )

    suggestions_dir = output_path / "suggestions"
    suggestions_dir.mkdir()

    _write_bundle_json(
        suggestions_dir / "suggestions-list.json",
        wrap_json(
            "suggestion_catalog",
            {"suggested_commands": [suggested_command_to_json_dict(s) for s in suggestions]},
        ),
        written_files,
        bundle_warnings,
        rel_path="suggestions/suggestions-list.json",
        kind="json",
        description="Generic suggested command catalog.",
        required=False,
    )

    tui_dir = output_path / "tui"
    tui_dir.mkdir()

    try:
        tui_model = build_tui_review_model(
            report=report,
            presets=presets.list_presets(),
            config=config_result,
            schema_documents=schema_documents,
        )
        snapshot = "\n".join(render_overview_lines(tui_model)) + "\n"
        (tui_dir / "snapshot.txt").write_text(snapshot)
        written_files.append(SupportBundleFile(
            path="tui/snapshot.txt",
            kind="text",
            description="TUI overview snapshot.",
            required=False,
        ))
    except OSError as error:
        bundle_warnings.append(f"Could not write tui/snapshot.txt: {error}")

    created_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
    manifest = SupportBundleManifest(
        schema_version=JSON_SCHEMA_VERSION,
        tool_version=__version__,
        kind="support_bundle_manifest",
        created_at=created_at,
        bundle_format="directory",
        files=tuple(written_files),
        warnings=tuple(bundle_warnings),
        notes=(
            "This bundle contains read-only inspection data. "
            "No pipelines were executed and no media was captured.",
        ),
    )

    try:
        manifest_payload = wrap_json(
            "support_bundle_manifest",
            support_bundle_manifest_to_json_dict(manifest),
        )
        (output_path / "manifest.json").write_text(
            json.dumps(manifest_payload, indent=2, sort_keys=True)
        )
    except OSError as error:
        print(f"Error: Could not write manifest: {error}")
        return 1

    print_support_bundle_written(output_path_str, written_files)
    return 0


def _write_bundle_json(
    file_path: Path,
    data: dict,
    written_files: list[SupportBundleFile],
    warnings: list[str],
    rel_path: str,
    kind: str,
    description: str,
    required: bool,
) -> None:
    try:
        file_path.write_text(json.dumps(data, indent=2, sort_keys=True))
        written_files.append(SupportBundleFile(
            path=rel_path,
            kind=kind,
            description=description,
            required=required,
        ))
    except OSError as error:
        warnings.append(f"Could not write {rel_path}: {error}")
