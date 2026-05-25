"""Deterministic demo data for the GUI shell."""

from __future__ import annotations

from dataclasses import dataclass

from gst_device_explorer.core.models import (
    CameraControl,
    CameraControlChoice,
    CameraControlSet,
    CandidateRanking,
    CandidateRecommendation,
    Capability,
    CompositeDevice,
    Device,
    DeviceProfile,
    DeviceRef,
    GroupValidation,
    GroupValidationDiagnostics,
    GroupValidationEndpointCounts,
    GroupingEvidence,
    ProfileCandidateSummary,
)
from gst_device_explorer.gui.builders import (
    build_detail_pane_for_audio_input,
    build_detail_pane_for_audio_output,
    build_detail_pane_for_group,
    build_detail_pane_for_video,
    build_media_explorer_snapshot,
    build_unknown_detail_pane,
)
from gst_device_explorer.gui.model import DetailPaneModel, MediaExplorerSnapshot, SidebarNode

DEMO_GENERATED_AT = "2026-05-24T12:00:00-07:00"


@dataclass(frozen=True)
class DemoGuiSnapshot:
    """Deterministic snapshot plus per-node detail panes for the Qt shell."""

    snapshot: MediaExplorerSnapshot
    detail_panes: dict[str, DetailPaneModel]


def build_demo_gui_snapshot() -> DemoGuiSnapshot:
    """Build a deterministic GUI snapshot without probing live hardware."""

    video_devices = [_demo_camera(), _standalone_camera()]
    audio_inputs = [_demo_audio_input()]
    audio_outputs = [_demo_audio_output()]
    group = _demo_group()
    validation = _demo_group_validation()
    controls = {
        "/dev/video0": _demo_control_set("/dev/video0"),
        "/dev/video2": _demo_control_set("/dev/video2", inactive=True),
    }
    profiles = [
        _profile(
            device_kind="video",
            device="/dev/video0",
            display_name="Reachy-Style Camera",
            available_candidate_id="generic-v4l2-yuyv-videoconvert-autovideosink",
        ),
        _profile(
            device_kind="audio-input",
            device="hw:2,0",
            display_name="Reachy-Style Microphone",
            available_candidate_id="generic-alsa-audio-input-level-fakesink",
        ),
        _profile(
            device_kind="audio-output",
            device="hw:2,0",
            display_name="Reachy-Style Speaker",
            available_candidate_id="generic-alsa-audio-output-sine-alsasink",
        ),
        DeviceProfile(
            device_kind="video",
            device="/dev/video2",
            display_name="Standalone Camera",
            candidate_summary={
                "available": [],
                "unavailable": [
                    ProfileCandidateSummary(
                        candidate_id="generic-v4l2-yuyv-videoconvert-autovideosink",
                        status="unavailable",
                        reason="autovideosink is missing in this synthetic demo",
                        missing_elements=["autovideosink"],
                    )
                ],
            },
        ),
    ]
    recommendations = [
        _ranking("video", "/dev/video0", "generic-v4l2-yuyv-videoconvert-autovideosink"),
        _ranking("audio-input", "hw:2,0", "generic-alsa-audio-input-level-fakesink"),
        _ranking("audio-output", "hw:2,0", "generic-alsa-audio-output-sine-alsasink"),
        CandidateRanking(
            kind="candidate_ranking",
            endpoint_kind="video",
            endpoint="/dev/video2",
            recommended_candidate_id=None,
            ranked_candidates=[
                CandidateRecommendation(
                    candidate_id="generic-v4l2-yuyv-videoconvert-autovideosink",
                    rank=1,
                    selected_profile="generic-linux-video-preview",
                    available=False,
                    score=10,
                    reasons=["Device exists but the display sink is unavailable."],
                    missing_elements=["autovideosink"],
                )
            ],
        ),
    ]

    snapshot = build_media_explorer_snapshot(
        video_devices=video_devices,
        audio_inputs=audio_inputs,
        audio_outputs=audio_outputs,
        groups=[group],
        profiles=profiles,
        validations=[validation],
        recommendations=recommendations,
        selected_id="group:demo-usb-device",
        generated_at=DEMO_GENERATED_AT,
    )
    detail_panes = _build_demo_detail_panes(
        snapshot=snapshot,
        group=group,
        validation=validation,
        video_devices=video_devices,
        audio_inputs=audio_inputs,
        audio_outputs=audio_outputs,
        profiles=profiles,
        recommendations=recommendations,
        controls=controls,
    )
    return DemoGuiSnapshot(snapshot=snapshot, detail_panes=detail_panes)


def _build_demo_detail_panes(
    *,
    snapshot: MediaExplorerSnapshot,
    group: CompositeDevice,
    validation: GroupValidation,
    video_devices: list[Device],
    audio_inputs: list[Device],
    audio_outputs: list[Device],
    profiles: list[DeviceProfile],
    recommendations: list[CandidateRanking],
    controls: dict[str, CameraControlSet],
) -> dict[str, DetailPaneModel]:
    by_profile = {(profile.device_kind, profile.device): profile for profile in profiles}
    by_ranking = {(ranking.endpoint_kind, ranking.endpoint): ranking for ranking in recommendations}
    result: dict[str, DetailPaneModel] = {
        "root:devices": build_unknown_detail_pane("root:devices"),
        "section:composite-groups": build_unknown_detail_pane("section:composite-groups"),
        "section:cameras": build_unknown_detail_pane("section:cameras"),
        "section:audio-inputs": build_unknown_detail_pane("section:audio-inputs"),
        "section:audio-outputs": build_unknown_detail_pane("section:audio-outputs"),
        "group:demo-usb-device": build_detail_pane_for_group(group, validation=validation),
    }
    for device in video_devices:
        pane = build_detail_pane_for_video(
            device,
            profile=by_profile.get(("video", _device_target(device))),
            recommendation=by_ranking.get(("video", _device_target(device))),
            control_set=controls.get(_device_target(device)),
        )
        result[pane.selected_id] = pane
    for device in audio_inputs:
        pane = build_detail_pane_for_audio_input(
            device,
            profile=by_profile.get(("audio-input", device.id)),
            recommendation=by_ranking.get(("audio-input", device.id)),
        )
        result[pane.selected_id] = pane
    for device in audio_outputs:
        pane = build_detail_pane_for_audio_output(
            device,
            profile=by_profile.get(("audio-output", device.id)),
            recommendation=by_ranking.get(("audio-output", device.id)),
        )
        result[pane.selected_id] = pane

    endpoint_aliases = _endpoint_aliases(snapshot.sidebar_roots)
    for alias, target_id in endpoint_aliases.items():
        if target_id in result:
            result[alias] = result[target_id]
    return result


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


def _demo_camera() -> Device:
    return Device(
        id="/dev/video0",
        kind="video_input",
        name="Reachy-Style Camera",
        capabilities=[
            Capability(
                name="video_format",
                values={
                    "media_type": "video",
                    "pixel_format": "MJPG",
                    "description": "Motion-JPEG, compressed",
                    "width": 640,
                    "height": 480,
                    "fps": [30.0, 15.0],
                    "device_path": "/dev/video0",
                },
                source="demo",
            ),
            Capability(
                name="video_format",
                values={
                    "media_type": "video",
                    "pixel_format": "YUYV",
                    "description": "YUYV 4:2:2",
                    "width": 1280,
                    "height": 720,
                    "fps": [30.0],
                    "device_path": "/dev/video0",
                },
                source="demo",
            ),
        ],
        metadata={"path": "/dev/video0", "driver": "uvcvideo", "bus": "usb-1-4.1"},
    )


def _standalone_camera() -> Device:
    return Device(
        id="/dev/video2",
        kind="video_input",
        name="Standalone Camera",
        capabilities=[
            Capability(
                name="video_format",
                values={
                    "media_type": "video",
                    "pixel_format": "MJPG",
                    "description": "Motion-JPEG, compressed",
                    "width": 1920,
                    "height": 1080,
                    "fps": [30.0],
                    "device_path": "/dev/video2",
                },
                source="demo",
            )
        ],
        metadata={"path": "/dev/video2", "driver": "uvcvideo", "bus": "usb-2-1"},
    )


def _demo_audio_input() -> Device:
    return Device(
        id="hw:2,0",
        kind="audio_input",
        name="Reachy-Style Microphone",
        metadata={"card": "2", "device": "0", "alsa_device": "hw:2,0"},
    )


def _demo_audio_output() -> Device:
    return Device(
        id="hw:2,0",
        kind="audio_output",
        name="Reachy-Style Speaker",
        metadata={"card": "2", "device": "0", "alsa_device": "hw:2,0"},
    )


def _demo_group() -> CompositeDevice:
    return CompositeDevice(
        id="demo-usb-device",
        name="Demo Composite USB Device",
        kind="unknown",
        confidence=0.9,
        members=[
            DeviceRef(role="camera", device_id="/dev/video0", path="/dev/video0", subsystem="v4l2"),
            DeviceRef(role="audio-input", device_id="hw:2,0", path=None, subsystem="alsa"),
            DeviceRef(role="audio-output", device_id="hw:2,0", path=None, subsystem="alsa"),
        ],
        evidence=[
            GroupingEvidence(
                source="demo-usb-topology",
                description="camera, microphone, and speaker share a synthetic USB parent",
                strength=0.9,
            )
        ],
    )


def _demo_group_validation() -> GroupValidation:
    return GroupValidation(
        kind="group_validation",
        group_id="demo-usb-device",
        group_label="Demo Composite USB Device",
        grouping_method="demo-usb-topology",
        status="limited",
        endpoint_counts=GroupValidationEndpointCounts(video=1, audio_inputs=1, audio_outputs=1),
        diagnostics=GroupValidationDiagnostics(missing_elements=["autovideosink"]),
        warnings=["Standalone camera preview is disabled in this demo."],
    )


def _demo_control_set(device_path: str, *, inactive: bool = False) -> CameraControlSet:
    flags = ("inactive",) if inactive else ()
    return CameraControlSet(
        device_path=device_path,
        source="demo",
        controls=(
            CameraControl(
                name="brightness",
                label="Brightness",
                control_type="int",
                control_id="0x00980900",
                device_path=device_path,
                minimum="0",
                maximum="255",
                step="1",
                default_value="128",
                current_value="140",
                flags=flags,
            ),
            CameraControl(
                name="exposure_auto",
                label="Exposure Auto",
                control_type="menu",
                control_id="0x009a0901",
                device_path=device_path,
                minimum="0",
                maximum="3",
                default_value="3",
                current_value="1",
                choices=(
                    CameraControlChoice(value="1", label="Manual Mode"),
                    CameraControlChoice(value="3", label="Aperture Priority Mode"),
                ),
                flags=flags,
            ),
            CameraControl(
                name="led1_mode",
                label="Led1 Mode",
                control_type="bool",
                control_id="0x0a046d05",
                device_path=device_path,
                default_value="0",
                current_value="1",
            ),
        ),
    )


def _profile(
    *,
    device_kind: str,
    device: str,
    display_name: str,
    available_candidate_id: str,
) -> DeviceProfile:
    return DeviceProfile(
        device_kind=device_kind,
        device=device,
        display_name=display_name,
        candidate_summary={
            "available": [
                ProfileCandidateSummary(
                    candidate_id=available_candidate_id,
                    status="available",
                    reason="required elements are available in the synthetic demo",
                )
            ],
            "unavailable": [],
        },
    )


def _ranking(endpoint_kind: str, endpoint: str, candidate_id: str) -> CandidateRanking:
    return CandidateRanking(
        kind="candidate_ranking",
        endpoint_kind=endpoint_kind,
        endpoint=endpoint,
        recommended_candidate_id=candidate_id,
        ranked_candidates=[
            CandidateRecommendation(
                candidate_id=candidate_id,
                rank=1,
                selected_profile="demo-profile",
                available=True,
                score=100,
                reasons=["Recommended first in the deterministic demo snapshot."],
            )
        ],
    )


def _device_target(device: Device) -> str:
    value = device.metadata.get("path") if device.kind == "video_input" else None
    if isinstance(value, str) and value:
        return value
    return device.id
