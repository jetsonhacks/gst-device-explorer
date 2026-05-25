from pathlib import Path
import subprocess
import sys


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from gst_device_explorer.core.models import (
    CandidateRanking,
    CandidateRecommendation,
    CameraControlSet,
    Capability,
    CompositeDevice,
    Device,
    DeviceProfile,
    DeviceRef,
    EnvironmentFact,
    GroupingEvidence,
    PipelineDiagnostic,
)
from gst_device_explorer.gui.live import (
    GuiSnapshotBundle,
    build_empty_snapshot,
    build_error_detail_pane,
    build_live_gui_snapshot,
    refresh_gui_snapshot,
)
import gst_device_explorer.gui.live as live


def test_live_snapshot_builder_uses_mocked_discovery_inputs(monkeypatch) -> None:
    _patch_live_inputs(monkeypatch)

    bundle = build_live_gui_snapshot()

    assert bundle.snapshot.selected_node_id == "group:usb-device-1-2-3"
    assert bundle.snapshot.detail_pane.kind == "group"
    ids = _flatten_sidebar_ids(bundle.snapshot.sidebar_roots)
    assert "video:/dev/video0" in ids
    assert "audio_input:hw:2,0" in ids
    assert "audio_output:hw:2,0" in ids
    assert "group:usb-device-1-2-3:video:/dev/video0" in ids
    assert bundle.detail_panes["video:/dev/video0"].kind == "video"
    assert bundle.detail_panes["group:usb-device-1-2-3:audio_input:hw:2,0"].kind == "audio_input"


def test_live_snapshot_preserves_selection_when_still_available(monkeypatch) -> None:
    _patch_live_inputs(monkeypatch)

    bundle = build_live_gui_snapshot(selected_id="video:/dev/video0")

    assert bundle.snapshot.selected_node_id == "video:/dev/video0"
    assert bundle.snapshot.detail_pane.kind == "video"


def test_live_snapshot_preserves_group_child_selection(monkeypatch) -> None:
    _patch_live_inputs(monkeypatch)

    selected = "group:usb-device-1-2-3:video:/dev/video0"
    bundle = build_live_gui_snapshot(selected_id=selected)

    assert bundle.snapshot.selected_node_id == selected
    assert bundle.detail_panes[selected].kind == "video"


def test_empty_discovery_produces_useful_empty_state(monkeypatch) -> None:
    monkeypatch.setattr(live.v4l2_probe, "discover_v4l2_video_devices", lambda: [])
    monkeypatch.setattr(live.alsa_probe, "discover_alsa_audio_inputs", lambda: [])
    monkeypatch.setattr(live.alsa_probe, "discover_alsa_audio_outputs", lambda: [])
    monkeypatch.setattr(live, "build_groupable_devices", lambda devices: [])
    monkeypatch.setattr(live, "build_composite_devices", lambda groupable: [])
    monkeypatch.setattr(
        live.gst_probe,
        "inspect_gstreamer_environment",
        lambda: [EnvironmentFact(name="gst", value="ok")],
    )

    bundle = build_live_gui_snapshot()

    assert bundle.snapshot.status == "empty"
    assert bundle.snapshot.detail_pane.title == "No Media Devices Discovered"
    assert bundle.snapshot.detail_pane.summary == (
        "Use Refresh after connecting a camera, microphone, or speaker.",
    )


def test_build_empty_snapshot_is_renderable() -> None:
    snapshot = build_empty_snapshot()

    assert snapshot.sidebar_roots[0].status == "empty"
    assert snapshot.detail_pane.kind == "empty"


def test_refresh_failure_produces_error_model() -> None:
    def fail_builder(selected_id: str | None = None) -> GuiSnapshotBundle:
        raise RuntimeError("synthetic refresh failure")

    bundle = refresh_gui_snapshot(fail_builder, previous_selected_id="video:/dev/video0")

    assert bundle.snapshot.status == "error"
    assert bundle.snapshot.detail_pane.kind == "error"
    assert bundle.snapshot.detail_pane.selected_id == "video:/dev/video0"
    assert "synthetic refresh failure" in bundle.snapshot.detail_pane.sections[-1].items


def test_refresh_helper_updates_current_snapshot() -> None:
    calls: list[str | None] = []

    def builder(selected_id: str | None = None) -> GuiSnapshotBundle:
        calls.append(selected_id)
        return build_empty_gui_bundle("Updated")

    bundle = refresh_gui_snapshot(builder, previous_selected_id="video:/old")

    assert calls == ["video:/old"]
    assert bundle.snapshot.detail_pane.title == "Updated"


def test_error_detail_pane_keeps_primary_message_clean() -> None:
    pane = build_error_detail_pane("Unable to refresh media devices.", details="boom")

    assert pane.title == "Unable to refresh media devices."
    assert pane.summary == ("Live discovery did not complete.",)
    assert pane.sections[-1].title == "Details"
    assert pane.sections[-1].items == ("boom",)


def test_live_refresh_tests_do_not_execute_subprocesses(monkeypatch) -> None:
    _patch_live_inputs(monkeypatch)

    def fail_popen(*args: object, **kwargs: object) -> None:
        raise AssertionError("GUI live refresh must not spawn subprocesses directly")

    monkeypatch.setattr(subprocess, "Popen", fail_popen)

    bundle = build_live_gui_snapshot()

    assert bundle.snapshot.status == "available"


def _patch_live_inputs(monkeypatch) -> None:
    video = Device(
        id="/dev/video0",
        kind="video_input",
        name="USB Camera",
        capabilities=[Capability(name="format", values={"pixel_format": "YUY2"})],
        metadata={"path": "/dev/video0", "backend": "v4l2"},
    )
    audio_input = Device(
        id="hw:2,0",
        kind="audio_input",
        name="USB Microphone",
        metadata={"alsa_device": "hw:2,0", "backend": "alsa"},
    )
    audio_output = Device(
        id="hw:2,0",
        kind="audio_output",
        name="USB Speaker",
        metadata={"alsa_device": "hw:2,0", "backend": "alsa"},
    )
    group = CompositeDevice(
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
                source="synthetic",
                description="devices share a synthetic parent",
                strength=0.9,
            )
        ],
    )

    monkeypatch.setattr(live.v4l2_probe, "discover_v4l2_video_devices", lambda: [video])
    monkeypatch.setattr(live.alsa_probe, "discover_alsa_audio_inputs", lambda: [audio_input])
    monkeypatch.setattr(live.alsa_probe, "discover_alsa_audio_outputs", lambda: [audio_output])
    monkeypatch.setattr(live, "build_groupable_devices", lambda devices: ["groupable"])
    monkeypatch.setattr(live, "build_composite_devices", lambda groupable: [group])
    monkeypatch.setattr(live.v4l2_probe, "discover_v4l2_capabilities", lambda target: video.capabilities)
    monkeypatch.setattr(
        live.v4l2_probe,
        "discover_v4l2_controls",
        lambda target: CameraControlSet(device_path=target, source="v4l2-ctl"),
    )
    monkeypatch.setattr(
        live.gst_probe,
        "inspect_gstreamer_environment",
        lambda: [EnvironmentFact(name="gst", value="ok")],
    )
    monkeypatch.setattr(
        live.profile_builders,
        "build_video_profile",
        lambda device, capabilities, environment, groups: DeviceProfile(
            device_kind="video",
            device="/dev/video0",
            display_name="USB Camera",
            candidate_summary={"available": [], "unavailable": []},
        ),
    )
    monkeypatch.setattr(
        live.profile_builders,
        "build_audio_input_profile",
        lambda device, environment, groups: DeviceProfile(
            device_kind="audio-input",
            device="hw:2,0",
            display_name="USB Microphone",
            candidate_summary={"available": [], "unavailable": []},
        ),
    )
    monkeypatch.setattr(
        live.profile_builders,
        "build_audio_output_profile",
        lambda device, environment, groups: DeviceProfile(
            device_kind="audio-output",
            device="hw:2,0",
            display_name="USB Speaker",
            candidate_summary={"available": [], "unavailable": []},
        ),
    )
    monkeypatch.setattr(live.video_pipelines, "build_video_preview_candidates", lambda *args: [])
    monkeypatch.setattr(live.audio_pipelines, "build_audio_input_test_candidates", lambda *args: [])
    monkeypatch.setattr(live.audio_pipelines, "build_audio_output_test_candidates", lambda *args: [])
    monkeypatch.setattr(
        live.video_diagnostics,
        "build_video_preview_diagnostics",
        lambda *args: [_diagnostic("video-candidate", "video", "/dev/video0")],
    )
    monkeypatch.setattr(
        live.audio_diagnostics,
        "build_audio_input_test_diagnostics",
        lambda *args: [_diagnostic("audio-input-candidate", "audio-input", "hw:2,0")],
    )
    monkeypatch.setattr(
        live.audio_diagnostics,
        "build_audio_output_test_diagnostics",
        lambda *args: [_diagnostic("audio-output-candidate", "audio-output", "hw:2,0")],
    )
    monkeypatch.setattr(live.validation, "build_group_validation", lambda group, profiles: None)
    monkeypatch.setattr(
        live.ranking,
        "rank_candidates",
        lambda candidates, diagnostics, endpoint_kind, endpoint: CandidateRanking(
            kind="candidate_ranking",
            endpoint_kind=endpoint_kind,
            endpoint=endpoint,
            recommended_candidate_id="candidate",
            ranked_candidates=[
                CandidateRecommendation(
                    candidate_id="candidate",
                    rank=1,
                    selected_profile="synthetic",
                    available=True,
                    score=100,
                )
            ],
        ),
    )


def _diagnostic(candidate_id: str, device_kind: str, device: str) -> PipelineDiagnostic:
    return PipelineDiagnostic(
        candidate_id=candidate_id,
        device_kind=device_kind,
        device=device,
        status="available",
        reason="synthetic diagnostic",
    )


def build_empty_gui_bundle(title: str) -> GuiSnapshotBundle:
    snapshot = build_empty_snapshot()
    detail = snapshot.detail_pane.__class__(
        selected_id=snapshot.detail_pane.selected_id,
        title=title,
        kind=snapshot.detail_pane.kind,
        status=snapshot.detail_pane.status,
        summary=snapshot.detail_pane.summary,
        sections=snapshot.detail_pane.sections,
        actions=snapshot.detail_pane.actions,
    )
    return GuiSnapshotBundle(
        snapshot=snapshot.__class__(
            sidebar_roots=snapshot.sidebar_roots,
            selected_node_id=snapshot.selected_node_id,
            detail_pane=detail,
            status=snapshot.status,
            summary=snapshot.summary,
            generated_at=snapshot.generated_at,
        ),
        detail_panes={detail.selected_id: detail},
    )


def _flatten_sidebar_ids(nodes) -> list[str]:
    result: list[str] = []
    for node in nodes:
        result.append(node.id)
        result.extend(_flatten_sidebar_ids(node.children))
    return result
