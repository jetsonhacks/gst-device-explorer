from dataclasses import FrozenInstanceError
from pathlib import Path
import subprocess
import sys


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pytest

from gst_device_explorer.core.models import (
    CandidateRanking,
    CandidateRecommendation,
    Capability,
    CompositeDevice,
    Device,
    DeviceProfile,
    DeviceRef,
    GroupValidation,
    GroupValidationEndpointCounts,
    GroupingEvidence,
    ProfileCandidateSummary,
)
from gst_device_explorer.core.suggestions import SuggestedCommand
from gst_device_explorer.gui import (
    DetailPaneModel,
    DetailSection,
    GuiAction,
    SidebarNode,
    build_detail_pane_for_audio_input,
    build_detail_pane_for_audio_output,
    build_detail_pane_for_group,
    build_detail_pane_for_video,
    build_media_explorer_snapshot,
    build_sidebar_model,
    build_unknown_detail_pane,
)


def test_gui_dataclasses_are_frozen_and_normalize_sequences() -> None:
    node = SidebarNode(
        id="root:devices",
        label="Devices",
        kind="root",
        status="available",
        children=[SidebarNode(id="section:cameras", label="Cameras", kind="section", status="empty")],
    )
    pane = DetailPaneModel(
        selected_id="video:/dev/video0",
        title="Camera",
        kind="video",
        status="available",
        summary=["ready"],
        sections=[DetailSection(title="Capabilities", items=["YUY2"])],
        actions=[
            GuiAction(
                id="dry-run:video:/dev/video0",
                label="Dry Run",
                kind="dry_run",
                enabled=True,
                safety="dry_run",
            )
        ],
    )

    assert isinstance(node.children, tuple)
    assert isinstance(pane.summary, tuple)
    assert isinstance(pane.sections, tuple)
    assert isinstance(pane.actions, tuple)
    with pytest.raises(FrozenInstanceError):
        node.label = "Changed"  # type: ignore[misc]


def test_sidebar_nodes_represent_nested_groups_and_endpoints() -> None:
    roots = build_sidebar_model(
        video_devices=[_video_device()],
        audio_inputs=[_audio_input_device()],
        audio_outputs=[_audio_output_device()],
        groups=[_group()],
    )

    root = roots[0]
    group_section = root.children[0]
    group = group_section.children[0]

    assert root.id == "root:devices"
    assert group.kind == "group"
    assert group.id == "group:usb-device-1-2-3"
    assert [child.kind for child in group.children] == [
        "audio_input",
        "audio_output",
        "video",
    ]
    assert [child.target for child in group.children] == ["hw:2,0", "hw:2,0", "/dev/video0"]


def test_sidebar_nests_child_groups_under_physical_parent_group() -> None:
    roots = build_sidebar_model(
        video_devices=[_video_device(), _second_video_device()],
        audio_inputs=[_audio_input_device()],
        audio_outputs=[_audio_output_device()],
        groups=[_reachy_audio_group(), _reachy_camera_group(), _reachy_parent_group()],
    )

    group_section = roots[0].children[0]
    parent = group_section.children[0]

    assert [group.label for group in group_section.children] == ["Reachy Mini"]
    assert parent.id == "group:usb-family-1-4"
    assert [child.label for child in parent.children] == [
        "Reachy Mini Audio",
        "Reachy Mini Camera",
    ]
    assert [child.id for child in parent.children] == [
        "group:audio-device-alsa-card-0",
        "group:usb-device-1-4-1-4",
    ]
    assert [
        [endpoint.target for endpoint in child.children]
        for child in parent.children
    ] == [
        ["hw:2,0", "hw:2,0"],
        ["/dev/video0", "/dev/video1"],
    ]


def test_sidebar_node_ids_are_stable_and_deterministic() -> None:
    first = build_sidebar_model(
        video_devices=[_video_device()],
        audio_inputs=[_audio_input_device()],
        audio_outputs=[_audio_output_device()],
        groups=[_group()],
    )
    second = build_sidebar_model(
        audio_outputs=[_audio_output_device()],
        groups=[_group()],
        video_devices=[_video_device()],
        audio_inputs=[_audio_input_device()],
    )

    assert _flatten_ids(first) == _flatten_ids(second)
    assert "video:/dev/video0" in _flatten_ids(first)
    assert "audio_input:hw:2,0" in _flatten_ids(first)
    assert "audio_output:hw:2,0" in _flatten_ids(first)


def test_group_detail_pane_preserves_status_and_validation_actions() -> None:
    validation = GroupValidation(
        kind="group_validation",
        group_id="usb-device-1-2-3",
        group_label="USB Device Group",
        grouping_method="usb-topology",
        status="limited",
        endpoint_counts=GroupValidationEndpointCounts(video=1, audio_inputs=1, audio_outputs=1),
    )

    pane = build_detail_pane_for_group(_group(), validation=validation)

    assert pane.kind == "group"
    assert pane.status == "limited"
    sections = {section.title: section for section in pane.sections}
    assert "Group Summary" in sections
    assert "Endpoints" in sections
    assert "Direct Endpoints" in sections
    assert "Grouping Evidence" in sections
    assert "Reproduce with CLI" in sections
    assert any(action.kind == "validate_group" for action in pane.actions)
    validate_action = next(action for action in pane.actions if action.kind == "validate_group")
    assert validate_action.suggested_command is not None
    assert validate_action.suggested_command.target == "usb-device-1-2-3"


def test_video_detail_pane_represents_capabilities_and_safe_actions() -> None:
    pane = build_detail_pane_for_video(
        _video_device(),
        profile=_video_profile(),
        recommendation=_ranking(endpoint_kind="video", endpoint="/dev/video0"),
    )

    assert pane.selected_id == "video:/dev/video0"
    assert pane.kind == "video"
    assert pane.status == "available"
    assert _section_items(pane, "Capabilities") == ("format: fps=30, height=720, pixel_format=YUY2, width=1280",)
    assert _action(pane, "dry_run").suggested_command is not None
    assert _action(pane, "dry_run").suggested_command.safety == "dry_run"
    assert _action(pane, "preview").safety == "safe_execution"


def test_audio_input_detail_pane_includes_disabled_capture_reason() -> None:
    pane = build_detail_pane_for_audio_input(
        _audio_input_device(),
        profile=_audio_profile("audio-input", "hw:2,0"),
        recommendation=_ranking(endpoint_kind="audio-input", endpoint="hw:2,0"),
    )

    assert pane.kind == "audio_input"
    assert _action(pane, "test_audio_input").enabled is True
    capture = _action(pane, "capture")
    assert capture.enabled is False
    assert capture.disabled_reason == "Choose an explicit output path before capture."


def test_audio_output_detail_pane_references_suggested_command() -> None:
    pane = build_detail_pane_for_audio_output(
        _audio_output_device(),
        profile=_audio_profile("audio-output", "hw:2,0"),
        recommendation=_ranking(endpoint_kind="audio-output", endpoint="hw:2,0"),
    )

    action = _action(pane, "dry_run")
    assert pane.kind == "audio_output"
    assert isinstance(action.suggested_command, SuggestedCommand)
    assert action.suggested_command.target_kind == "audio-output"
    assert action.suggested_command.target == "hw:2,0"


def test_unknown_selection_produces_safe_fallback_detail_pane() -> None:
    pane = build_unknown_detail_pane("video:/missing")

    assert pane.kind == "unknown"
    assert pane.status == "unavailable"
    assert [action.kind for action in pane.actions] == ["refresh", "export_report"]


def test_empty_system_state_produces_useful_empty_snapshot() -> None:
    snapshot = build_media_explorer_snapshot()

    assert snapshot.sidebar_roots[0].status == "empty"
    assert snapshot.detail_pane.kind == "unknown"
    assert snapshot.detail_pane.status == "empty"
    assert snapshot.summary == ("0 camera(s), 0 audio input(s), 0 audio output(s), 0 group(s)",)


def test_snapshot_selects_matching_detail_pane() -> None:
    snapshot = build_media_explorer_snapshot(
        video_devices=[_video_device()],
        profiles=[_video_profile()],
        recommendations=[_ranking(endpoint_kind="video", endpoint="/dev/video0")],
        selected_id="video:/dev/video0",
    )

    assert snapshot.selected_node_id == "video:/dev/video0"
    assert snapshot.detail_pane.kind == "video"
    assert snapshot.detail_pane.title == "Synthetic Camera"


def test_builders_do_not_execute_pipelines_or_capture(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail_popen(*args: object, **kwargs: object) -> None:
        raise AssertionError("GUI model builders must not spawn subprocesses")

    monkeypatch.setattr(subprocess, "Popen", fail_popen)

    snapshot = build_media_explorer_snapshot(
        video_devices=[_video_device()],
        audio_inputs=[_audio_input_device()],
        audio_outputs=[_audio_output_device()],
        groups=[_group()],
        profiles=[_video_profile()],
        recommendations=[_ranking(endpoint_kind="video", endpoint="/dev/video0")],
        selected_id="video:/dev/video0",
    )

    assert snapshot.detail_pane.kind == "video"


def _video_device() -> Device:
    return Device(
        id="/dev/video0",
        kind="video_input",
        name="Synthetic Camera",
        capabilities=[
            Capability(
                name="format",
                values={"pixel_format": "YUY2", "width": 1280, "height": 720, "fps": 30},
            )
        ],
        metadata={"path": "/dev/video0", "driver": "uvcvideo", "bus": "usb-1-2.3"},
    )


def _second_video_device() -> Device:
    return Device(
        id="/dev/video1",
        kind="video_input",
        name="Synthetic Camera 2",
        capabilities=[
            Capability(
                name="format",
                values={"pixel_format": "YUY2", "width": 1280, "height": 720, "fps": 30},
            )
        ],
        metadata={"path": "/dev/video1", "driver": "uvcvideo", "bus": "usb-1-2.4"},
    )


def _audio_input_device() -> Device:
    return Device(
        id="hw:2,0",
        kind="audio_input",
        name="Synthetic Microphone",
        metadata={"card": "2", "device": "0", "alsa_device": "hw:2,0"},
    )


def _audio_output_device() -> Device:
    return Device(
        id="hw:2,0",
        kind="audio_output",
        name="Synthetic Speaker",
        metadata={"card": "2", "device": "0", "alsa_device": "hw:2,0"},
    )


def _group() -> CompositeDevice:
    return CompositeDevice(
        id="usb-device-1-2-3",
        name="USB Device Group",
        kind="unknown",
        confidence=0.9,
        members=[
            DeviceRef(role="camera", device_id="/dev/video0", path="/dev/video0", subsystem="v4l2"),
            DeviceRef(role="audio-input", device_id="hw:2,0", path=None, subsystem="alsa"),
            DeviceRef(role="audio-output", device_id="hw:2,0", path=None, subsystem="alsa"),
        ],
        evidence=[
            GroupingEvidence(
                source="usb-topology",
                description="devices share USB parent path 1-2.3",
                strength=0.9,
            )
        ],
    )


def _reachy_audio_group() -> CompositeDevice:
    return CompositeDevice(
        id="audio-device-alsa-card-0",
        name="Reachy Mini Audio",
        kind="audio-device",
        confidence=0.9,
        members=[
            DeviceRef(role="audio-input", device_id="hw:2,0", path="hw:2,0", subsystem="alsa"),
            DeviceRef(role="audio-output", device_id="hw:2,0", path="hw:2,0", subsystem="alsa"),
        ],
        evidence=[
            GroupingEvidence(
                source="alsa-card",
                description="audio devices share ALSA card 0",
                strength=0.9,
            )
        ],
    )


def _reachy_camera_group() -> CompositeDevice:
    return CompositeDevice(
        id="usb-device-1-4-1-4",
        name="Reachy Mini Camera",
        kind="unknown",
        confidence=0.9,
        members=[
            DeviceRef(role="camera", device_id="/dev/video0", path="/dev/video0", subsystem="v4l2"),
            DeviceRef(role="camera", device_id="/dev/video1", path="/dev/video1", subsystem="v4l2"),
        ],
        evidence=[
            GroupingEvidence(
                source="usb-topology",
                description="devices share USB parent path 1-4.1.4",
                strength=0.9,
            )
        ],
    )


def _reachy_parent_group() -> CompositeDevice:
    return CompositeDevice(
        id="usb-family-1-4",
        name="Reachy Mini",
        kind="unknown",
        confidence=0.8,
        members=[
            DeviceRef(role="audio-input", device_id="hw:2,0", path="hw:2,0", subsystem="alsa"),
            DeviceRef(role="audio-output", device_id="hw:2,0", path="hw:2,0", subsystem="alsa"),
            DeviceRef(role="camera", device_id="/dev/video0", path="/dev/video0", subsystem="v4l2"),
            DeviceRef(role="camera", device_id="/dev/video1", path="/dev/video1", subsystem="v4l2"),
        ],
        evidence=[
            GroupingEvidence(
                source="usb-topology",
                description="composite groups share USB ancestor 1-4",
                strength=0.8,
            )
        ],
    )


def _video_profile() -> DeviceProfile:
    return DeviceProfile(
        device_kind="video",
        device="/dev/video0",
        display_name="Synthetic Camera",
        candidate_summary={
            "available": [
                ProfileCandidateSummary(
                    candidate_id="generic-v4l2-yuyv-videoconvert-autovideosink",
                    status="available",
                    reason="required elements are available",
                )
            ],
            "unavailable": [],
        },
    )


def _audio_profile(device_kind: str, device: str) -> DeviceProfile:
    return DeviceProfile(
        device_kind=device_kind,
        device=device,
        display_name=device,
        candidate_summary={
            "available": [
                ProfileCandidateSummary(
                    candidate_id="generic-alsa-test",
                    status="available",
                    reason="required elements are available",
                )
            ],
            "unavailable": [],
        },
    )


def _ranking(endpoint_kind: str, endpoint: str) -> CandidateRanking:
    return CandidateRanking(
        kind="candidate_ranking",
        endpoint_kind=endpoint_kind,
        endpoint=endpoint,
        recommended_candidate_id="recommended-candidate",
        ranked_candidates=[
            CandidateRecommendation(
                candidate_id="recommended-candidate",
                rank=1,
                selected_profile="generic",
                available=True,
                score=100,
            )
        ],
    )


def _flatten_ids(nodes: tuple[SidebarNode, ...]) -> list[str]:
    result: list[str] = []
    for node in nodes:
        result.append(node.id)
        result.extend(_flatten_ids(node.children))
    return result


def _action(pane: DetailPaneModel, kind: str) -> GuiAction:
    return next(action for action in pane.actions if action.kind == kind)


def _section_items(pane: DetailPaneModel, title: str) -> tuple[str, ...]:
    return next(section.items for section in pane.sections if section.title == title)
