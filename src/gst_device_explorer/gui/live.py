"""Live GUI snapshot builders.

This module adapts existing safe discovery/profile/grouping functions into the
toolkit-neutral GUI model. It does not run GUI actions, execute pipelines,
capture media, or start subprocesses beyond the existing read-only probe paths.
"""

from __future__ import annotations

from dataclasses import dataclass, replace

from gst_device_explorer.core.grouping import build_composite_devices
from gst_device_explorer.core.grouping_metadata import build_groupable_devices
from gst_device_explorer.core.models import (
    CandidateRanking,
    CompositeDevice,
    Device,
    DeviceProfile,
)
import gst_device_explorer.core.audio_diagnostics as audio_diagnostics
import gst_device_explorer.core.audio_pipelines as audio_pipelines
import gst_device_explorer.core.pipelines as video_pipelines
import gst_device_explorer.core.profiles as profile_builders
import gst_device_explorer.core.ranking as ranking
import gst_device_explorer.core.validation as validation
import gst_device_explorer.core.video_diagnostics as video_diagnostics
from gst_device_explorer.gui.builders import (
    build_detail_pane_for_audio_input,
    build_detail_pane_for_audio_output,
    build_detail_pane_for_group,
    build_detail_pane_for_video,
    build_media_explorer_snapshot,
    build_sidebar_model,
)
from gst_device_explorer.gui.model import (
    DetailPaneModel,
    DetailSection,
    GuiAction,
    MediaExplorerSnapshot,
    SidebarNode,
)
import gst_device_explorer.probes.alsa as alsa_probe
import gst_device_explorer.probes.gst as gst_probe
import gst_device_explorer.probes.v4l2 as v4l2_probe


@dataclass(frozen=True)
class GuiSnapshotBundle:
    """Renderable GUI snapshot plus detail panes keyed by sidebar node id."""

    snapshot: MediaExplorerSnapshot
    detail_panes: dict[str, DetailPaneModel]


def build_live_media_explorer_snapshot(selected_id: str | None = None) -> MediaExplorerSnapshot:
    """Build a live GUI snapshot from existing safe probe/discovery paths."""

    return build_live_gui_snapshot(selected_id=selected_id).snapshot


def build_live_gui_snapshot(selected_id: str | None = None) -> GuiSnapshotBundle:
    """Build a live GUI snapshot bundle from currently discovered devices."""

    video_devices = v4l2_probe.discover_v4l2_video_devices()
    audio_inputs = alsa_probe.discover_alsa_audio_inputs()
    audio_outputs = alsa_probe.discover_alsa_audio_outputs()
    devices = [*video_devices, *audio_inputs, *audio_outputs]
    groups = build_composite_devices(build_groupable_devices(devices))
    environment = gst_probe.inspect_gstreamer_environment()

    video_capabilities = {
        _device_target(device): v4l2_probe.discover_v4l2_capabilities(_device_target(device))
        for device in video_devices
    }
    video_devices = [
        replace(device, capabilities=list(video_capabilities[_device_target(device)]))
        for device in video_devices
    ]
    profiles: list[DeviceProfile] = []
    recommendations: list[CandidateRanking] = []

    for device in video_devices:
        target = _device_target(device)
        capabilities = video_capabilities[target]
        profile = profile_builders.build_video_profile(
            device,
            capabilities,
            environment,
            groups,
        )
        if profile is not None:
            profiles.append(profile)
        candidates = video_pipelines.build_video_preview_candidates(
            device,
            capabilities,
            environment,
        )
        diagnostics = video_diagnostics.build_video_preview_diagnostics(
            device,
            capabilities,
            environment,
        )
        recommendations.append(ranking.rank_candidates(candidates, diagnostics, "video", target))

    for device in audio_inputs:
        target = _device_target(device)
        profile = profile_builders.build_audio_input_profile(device, environment, groups)
        if profile is not None:
            profiles.append(profile)
        candidates = audio_pipelines.build_audio_input_test_candidates(device, environment)
        diagnostics = audio_diagnostics.build_audio_input_test_diagnostics(device, environment)
        recommendations.append(
            ranking.rank_candidates(candidates, diagnostics, "audio-input", target)
        )

    for device in audio_outputs:
        target = _device_target(device)
        profile = profile_builders.build_audio_output_profile(device, environment, groups)
        if profile is not None:
            profiles.append(profile)
        candidates = audio_pipelines.build_audio_output_test_candidates(device, environment)
        diagnostics = audio_diagnostics.build_audio_output_test_diagnostics(device, environment)
        recommendations.append(
            ranking.rank_candidates(candidates, diagnostics, "audio-output", target)
        )

    validations = [
        item
        for item in (
            validation.build_group_validation(group, profiles)
            for group in groups
        )
        if item is not None
    ]
    selected = _select_existing_or_default(
        selected_id=selected_id,
        video_devices=video_devices,
        audio_inputs=audio_inputs,
        audio_outputs=audio_outputs,
        groups=groups,
    )
    if not devices and not groups:
        return build_empty_gui_snapshot()

    snapshot = build_media_explorer_snapshot(
        video_devices=video_devices,
        audio_inputs=audio_inputs,
        audio_outputs=audio_outputs,
        groups=groups,
        profiles=profiles,
        validations=validations,
        recommendations=recommendations,
        selected_id=selected,
    )
    detail_panes = build_detail_pane_map(
        snapshot=snapshot,
        video_devices=video_devices,
        audio_inputs=audio_inputs,
        audio_outputs=audio_outputs,
        groups=groups,
        profiles=profiles,
        validations=validations,
        recommendations=recommendations,
    )
    return GuiSnapshotBundle(snapshot=snapshot, detail_panes=detail_panes)


def refresh_gui_snapshot(
    builder=build_live_gui_snapshot,
    *,
    previous_selected_id: str | None = None,
) -> GuiSnapshotBundle:
    """Refresh a GUI snapshot, returning an error model instead of raising."""

    try:
        return builder(selected_id=previous_selected_id)
    except Exception as error:
        return build_error_gui_snapshot(
            "Unable to refresh media devices.",
            details=str(error),
            selected_id=previous_selected_id,
        )


def build_detail_pane_map(
    *,
    snapshot: MediaExplorerSnapshot,
    video_devices: list[Device],
    audio_inputs: list[Device],
    audio_outputs: list[Device],
    groups: list[CompositeDevice],
    profiles: list[DeviceProfile],
    validations,
    recommendations: list[CandidateRanking],
) -> dict[str, DetailPaneModel]:
    """Build detail panes for all stable sidebar node ids in a snapshot."""

    profiles_by_key = {(profile.device_kind, profile.device): profile for profile in profiles}
    rankings_by_key = {
        (ranking_item.endpoint_kind, ranking_item.endpoint): ranking_item
        for ranking_item in recommendations
    }
    validations_by_group = {item.group_id: item for item in validations}
    result: dict[str, DetailPaneModel] = {
        snapshot.detail_pane.selected_id: snapshot.detail_pane,
        "root:devices": build_overview_detail_pane(snapshot),
        "section:composite-groups": build_section_detail_pane("Composite Groups", groups),
        "section:cameras": build_section_detail_pane("Cameras", video_devices),
        "section:audio-inputs": build_section_detail_pane("Audio Inputs", audio_inputs),
        "section:audio-outputs": build_section_detail_pane("Audio Outputs", audio_outputs),
    }

    for group in groups:
        result[f"group:{group.id}"] = build_detail_pane_for_group(
            group,
            validation=validations_by_group.get(group.id),
        )
    for device in video_devices:
        target = _device_target(device)
        pane = build_detail_pane_for_video(
            device,
            profile=profiles_by_key.get(("video", target)),
            recommendation=rankings_by_key.get(("video", target)),
        )
        result[pane.selected_id] = pane
    for device in audio_inputs:
        target = _device_target(device)
        pane = build_detail_pane_for_audio_input(
            device,
            profile=profiles_by_key.get(("audio-input", target)),
            recommendation=rankings_by_key.get(("audio-input", target)),
        )
        result[pane.selected_id] = pane
    for device in audio_outputs:
        target = _device_target(device)
        pane = build_detail_pane_for_audio_output(
            device,
            profile=profiles_by_key.get(("audio-output", target)),
            recommendation=rankings_by_key.get(("audio-output", target)),
        )
        result[pane.selected_id] = pane

    for alias, target_id in _endpoint_aliases(snapshot.sidebar_roots).items():
        if target_id in result:
            result[alias] = result[target_id]
    return result


def build_loading_detail_pane() -> DetailPaneModel:
    """Build a transient loading detail pane."""

    return DetailPaneModel(
        selected_id="refresh:loading",
        title="Refreshing Devices",
        kind="loading",
        status="loading",
        summary=("Refreshing cameras, audio endpoints, and composite groups.",),
        sections=(
            DetailSection(
                title="Refresh",
                items=("This read-only refresh uses existing safe discovery paths.",),
            ),
        ),
        actions=(),
    )


def build_error_detail_pane(
    message: str,
    *,
    details: str | None = None,
    selected_id: str | None = None,
) -> DetailPaneModel:
    """Build an error detail pane without exposing stack traces as primary UI."""

    sections = [
        DetailSection(
            title="Suggested Next Step",
            items=("Check that required system tools are installed, then try Refresh again.",),
        )
    ]
    if details:
        sections.append(DetailSection(title="Details", items=(details,)))
    return DetailPaneModel(
        selected_id=selected_id or "refresh:error",
        title=message,
        kind="error",
        status="error",
        summary=("Live discovery did not complete.",),
        sections=tuple(sections),
        actions=(_refresh_action(),),
    )


def build_empty_snapshot() -> MediaExplorerSnapshot:
    """Build a useful empty live snapshot."""

    return MediaExplorerSnapshot(
        sidebar_roots=build_sidebar_model(),
        selected_node_id="selection:empty",
        detail_pane=build_empty_detail_pane(),
        status="empty",
        summary=("No media devices discovered.",),
    )


def build_empty_gui_snapshot() -> GuiSnapshotBundle:
    """Build a renderable empty live snapshot bundle."""

    snapshot = build_empty_snapshot()
    return GuiSnapshotBundle(
        snapshot=snapshot,
        detail_panes={
            snapshot.detail_pane.selected_id: snapshot.detail_pane,
            "root:devices": snapshot.detail_pane,
        },
    )


def build_error_gui_snapshot(
    message: str,
    *,
    details: str | None = None,
    selected_id: str | None = None,
) -> GuiSnapshotBundle:
    """Build a renderable error snapshot bundle."""

    detail = build_error_detail_pane(message, details=details, selected_id=selected_id)
    snapshot = MediaExplorerSnapshot(
        sidebar_roots=build_sidebar_model(),
        selected_node_id=detail.selected_id,
        detail_pane=detail,
        status="error",
        summary=(message,),
    )
    return GuiSnapshotBundle(snapshot=snapshot, detail_panes={detail.selected_id: detail})


def build_overview_detail_pane(snapshot: MediaExplorerSnapshot) -> DetailPaneModel:
    """Build an overview pane for the root sidebar node."""

    return DetailPaneModel(
        selected_id="root:devices",
        title="Discovered Media Devices",
        kind="overview",
        status=snapshot.status,
        summary=snapshot.summary,
        sections=(
            DetailSection(
                title="Refresh",
                items=("Use Refresh after connecting or removing media devices.",),
            ),
        ),
        actions=(_refresh_action(),),
    )


def build_section_detail_pane(title: str, items: list[object]) -> DetailPaneModel:
    """Build a simple detail pane for sidebar section nodes."""

    return DetailPaneModel(
        selected_id=f"section:{title.lower().replace(' ', '-')}",
        title=title,
        kind="section",
        status="available" if items else "empty",
        summary=(f"{len(items)} item(s)",),
        sections=(
            DetailSection(
                title="Selection",
                items=("Select a child item to inspect endpoint details.",),
            ),
        ),
        actions=(_refresh_action(),),
    )


def build_empty_detail_pane() -> DetailPaneModel:
    """Build an empty live-discovery detail pane."""

    return DetailPaneModel(
        selected_id="selection:empty",
        title="No Media Devices Discovered",
        kind="empty",
        status="empty",
        summary=("Use Refresh after connecting a camera, microphone, or speaker.",),
        sections=(
            DetailSection(
                title="Discovery",
                items=("No cameras, audio inputs, audio outputs, or composite groups were found.",),
            ),
        ),
        actions=(_refresh_action(),),
    )


def _refresh_action() -> GuiAction:
    return GuiAction(
        id="refresh:devices",
        label="Refresh",
        kind="refresh",
        enabled=True,
        safety="inspection",
        disabled_reason=None,
    )


def _select_existing_or_default(
    *,
    selected_id: str | None,
    video_devices: list[Device],
    audio_inputs: list[Device],
    audio_outputs: list[Device],
    groups: list[CompositeDevice],
) -> str | None:
    ids = _available_selection_ids(video_devices, audio_inputs, audio_outputs, groups)
    if selected_id in ids:
        return selected_id
    if groups:
        return f"group:{groups[0].id}"
    if video_devices:
        return f"video:{_device_target(video_devices[0])}"
    if audio_inputs:
        return f"audio_input:{_device_target(audio_inputs[0])}"
    if audio_outputs:
        return f"audio_output:{_device_target(audio_outputs[0])}"
    return None


def _available_selection_ids(
    video_devices: list[Device],
    audio_inputs: list[Device],
    audio_outputs: list[Device],
    groups: list[CompositeDevice],
) -> set[str]:
    ids = {f"group:{group.id}" for group in groups}
    ids.update(f"video:{_device_target(device)}" for device in video_devices)
    ids.update(f"audio_input:{_device_target(device)}" for device in audio_inputs)
    ids.update(f"audio_output:{_device_target(device)}" for device in audio_outputs)
    for group in groups:
        for member in group.members:
            if member.role in {"camera", "video", "video_input"}:
                ids.add(f"group:{group.id}:video:{member.path or member.device_id}")
            elif member.role in {"audio-input", "audio_input"}:
                ids.add(f"group:{group.id}:audio_input:{member.device_id}")
            elif member.role in {"audio-output", "audio_output"}:
                ids.add(f"group:{group.id}:audio_output:{member.device_id}")
    return ids


def _endpoint_aliases(nodes: tuple[SidebarNode, ...]) -> dict[str, str]:
    aliases: dict[str, str] = {}
    for node in nodes:
        if node.target_kind == "video" and node.target is not None:
            aliases[node.id] = f"video:{node.target}"
        elif node.target_kind == "audio-input" and node.target is not None:
            aliases[node.id] = f"audio_input:{node.target}"
        elif node.target_kind == "audio-output" and node.target is not None:
            aliases[node.id] = f"audio_output:{node.target}"
        aliases.update(_endpoint_aliases(node.children))
    return aliases


def _device_target(device: Device) -> str:
    value = device.metadata.get("path") if device.kind == "video_input" else None
    if isinstance(value, str) and value:
        return value
    value = device.metadata.get("alsa_device")
    if isinstance(value, str) and value:
        return value
    return device.id
