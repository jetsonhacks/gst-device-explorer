"""Synthetic tests for candidate ranking, serialization, rendering, and CLI."""

from pathlib import Path
import json
import sys


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from gst_device_explorer.core.models import (
    Capability,
    CandidateRanking,
    CandidateRecommendation,
    Device,
    EnvironmentFact,
    PipelineCandidate,
    PipelineDiagnostic,
)
from gst_device_explorer.core.ranking import (
    empty_ranking,
    rank_candidates,
)
from gst_device_explorer.cli.serializers import (
    candidate_ranking_to_json_dict,
    candidate_recommendation_to_json_dict,
)
from gst_device_explorer.cli.main import main
import gst_device_explorer.cli.commands as cli_commands


# ---------------------------------------------------------------------------
# Core ranking — availability and scoring
# ---------------------------------------------------------------------------


def test_available_candidates_rank_above_unavailable() -> None:
    candidates = [_candidate("generic-id", confidence=0.8)]
    diagnostics = [
        _unavailable_diagnostic("jetson-id", ["nvjpegdec"]),
        _available_diagnostic("generic-id"),
    ]

    result = rank_candidates(candidates, diagnostics, "video", "/dev/video0")

    ids = [item.candidate_id for item in result.ranked_candidates]
    assert ids.index("generic-id") < ids.index("jetson-id")


def test_higher_confidence_ranks_first_among_available() -> None:
    candidates = [
        _candidate("jetson-id", confidence=0.9),
        _candidate("generic-id", confidence=0.8),
    ]
    diagnostics = [
        _available_diagnostic("jetson-id"),
        _available_diagnostic("generic-id"),
    ]

    result = rank_candidates(candidates, diagnostics, "video", "/dev/video0")

    assert result.ranked_candidates[0].candidate_id == "jetson-id"
    assert result.ranked_candidates[1].candidate_id == "generic-id"


def test_available_candidate_score_exceeds_unavailable() -> None:
    candidates = [_candidate("generic-id", confidence=0.8)]
    diagnostics = [
        _available_diagnostic("generic-id"),
        _unavailable_diagnostic("jetson-id", ["nvjpegdec", "nveglglessink"]),
    ]

    result = rank_candidates(candidates, diagnostics, "video", "/dev/video0")

    available_item = next(
        r for r in result.ranked_candidates if r.candidate_id == "generic-id"
    )
    unavailable_item = next(
        r for r in result.ranked_candidates if r.candidate_id == "jetson-id"
    )
    assert available_item.score > unavailable_item.score


def test_unavailable_candidates_have_score_zero() -> None:
    diagnostics = [
        _unavailable_diagnostic("jetson-id", ["nvjpegdec"]),
        _unavailable_diagnostic("generic-id", ["autovideosink"]),
    ]

    result = rank_candidates([], diagnostics, "video", "/dev/video0")

    for item in result.ranked_candidates:
        assert item.score == 0


def test_ranking_is_deterministic() -> None:
    candidates = [_candidate("b-id"), _candidate("a-id")]
    diagnostics = [
        _unavailable_diagnostic("b-id", ["elem1"]),
        _unavailable_diagnostic("a-id", ["elem1"]),
    ]

    result1 = rank_candidates(candidates, diagnostics, "video", "/dev/video0")
    result2 = rank_candidates(candidates, diagnostics, "video", "/dev/video0")

    ids1 = [r.candidate_id for r in result1.ranked_candidates]
    ids2 = [r.candidate_id for r in result2.ranked_candidates]
    assert ids1 == ids2


def test_unavailable_candidates_sort_by_candidate_id_when_equal_score() -> None:
    diagnostics = [
        _unavailable_diagnostic("z-id", ["elem1"]),
        _unavailable_diagnostic("a-id", ["elem1"]),
    ]

    result = rank_candidates([], diagnostics, "video", "/dev/video0")

    assert result.ranked_candidates[0].candidate_id == "a-id"
    assert result.ranked_candidates[1].candidate_id == "z-id"


# ---------------------------------------------------------------------------
# Core ranking — recommended_candidate_id
# ---------------------------------------------------------------------------


def test_recommended_id_is_set_to_first_available() -> None:
    candidates = [_candidate("generic-id")]
    diagnostics = [_available_diagnostic("generic-id")]

    result = rank_candidates(candidates, diagnostics, "video", "/dev/video0")

    assert result.recommended_candidate_id == "generic-id"


def test_recommended_id_is_none_when_no_available_candidates() -> None:
    diagnostics = [_unavailable_diagnostic("jetson-id", ["nvjpegdec"])]

    result = rank_candidates([], diagnostics, "video", "/dev/video0")

    assert result.recommended_candidate_id is None


def test_recommended_id_is_none_when_no_diagnostics() -> None:
    result = rank_candidates([], [], "video", "/dev/video0")

    assert result.recommended_candidate_id is None


def test_recommended_id_is_highest_ranked_available() -> None:
    candidates = [
        _candidate("jetson-id", confidence=0.9),
        _candidate("generic-id", confidence=0.8),
    ]
    diagnostics = [
        _available_diagnostic("jetson-id"),
        _available_diagnostic("generic-id"),
    ]

    result = rank_candidates(candidates, diagnostics, "video", "/dev/video0")

    assert result.recommended_candidate_id == "jetson-id"


# ---------------------------------------------------------------------------
# Core ranking — ranks, reasons, warnings, missing elements
# ---------------------------------------------------------------------------


def test_ranks_are_assigned_sequentially_from_one() -> None:
    candidates = [_candidate("a-id")]
    diagnostics = [
        _available_diagnostic("a-id"),
        _unavailable_diagnostic("b-id", ["elem1"]),
    ]

    result = rank_candidates(candidates, diagnostics, "video", "/dev/video0")

    ranks = [r.rank for r in result.ranked_candidates]
    assert ranks == [1, 2]


def test_reasons_are_included_for_available() -> None:
    candidates = [_candidate("generic-id")]
    diagnostics = [_available_diagnostic("generic-id")]

    result = rank_candidates(candidates, diagnostics, "video", "/dev/video0")

    item = result.ranked_candidates[0]
    assert item.available is True
    assert len(item.reasons) > 0
    assert any("available" in r.lower() for r in item.reasons)


def test_reasons_are_included_for_unavailable() -> None:
    diagnostics = [_unavailable_diagnostic("jetson-id", ["nvjpegdec"])]

    result = rank_candidates([], diagnostics, "video", "/dev/video0")

    item = result.ranked_candidates[0]
    assert item.available is False
    assert len(item.reasons) > 0


def test_missing_elements_are_preserved_for_unavailable() -> None:
    diagnostics = [_unavailable_diagnostic("jetson-id", ["nvjpegdec", "nveglglessink"])]

    result = rank_candidates([], diagnostics, "video", "/dev/video0")

    item = result.ranked_candidates[0]
    assert "nvjpegdec" in item.missing_elements
    assert "nveglglessink" in item.missing_elements


def test_missing_elements_are_empty_for_available() -> None:
    candidates = [_candidate("generic-id")]
    diagnostics = [_available_diagnostic("generic-id")]

    result = rank_candidates(candidates, diagnostics, "video", "/dev/video0")

    item = result.ranked_candidates[0]
    assert item.missing_elements == []


def test_candidate_profile_label_is_preserved_for_available() -> None:
    candidates = [_candidate("jetson-id", profile="jetson-video-preview")]
    diagnostics = [_available_diagnostic("jetson-id")]

    result = rank_candidates(candidates, diagnostics, "video", "/dev/video0")

    item = result.ranked_candidates[0]
    assert item.selected_profile == "jetson-video-preview"


def test_candidate_profile_label_is_none_for_unavailable_without_candidate() -> None:
    diagnostics = [_unavailable_diagnostic("jetson-id", ["nvjpegdec"])]

    result = rank_candidates([], diagnostics, "video", "/dev/video0")

    item = result.ranked_candidates[0]
    assert item.selected_profile is None


def test_candidate_warnings_are_propagated() -> None:
    candidate = PipelineCandidate(
        candidate_id="warned-id",
        purpose="test",
        command="gst-launch-1.0 ...",
        confidence=0.8,
        argv=["gst-launch-1.0"],
        warnings=["experimental pipeline"],
        required_elements=["v4l2src"],
        selected_profile="generic-linux-video-preview",
    )
    diagnostics = [_available_diagnostic("warned-id")]

    result = rank_candidates([candidate], diagnostics, "video", "/dev/video0")

    item = result.ranked_candidates[0]
    assert "experimental pipeline" in item.warnings


# ---------------------------------------------------------------------------
# Core ranking — endpoint metadata
# ---------------------------------------------------------------------------


def test_ranking_carries_endpoint_kind_and_endpoint() -> None:
    result = rank_candidates([], [], "audio-input", "hw:0,0")

    assert result.endpoint_kind == "audio-input"
    assert result.endpoint == "hw:0,0"
    assert result.kind == "candidate_ranking"


def test_empty_ranking_returns_correct_structure() -> None:
    result = empty_ranking("audio-output", "hw:1,0")

    assert result.kind == "candidate_ranking"
    assert result.endpoint_kind == "audio-output"
    assert result.endpoint == "hw:1,0"
    assert result.recommended_candidate_id is None
    assert result.ranked_candidates == []


# ---------------------------------------------------------------------------
# JSON serialization
# ---------------------------------------------------------------------------


def test_candidate_ranking_json_has_expected_top_level_keys() -> None:
    result = rank_candidates([], [], "video", "/dev/video0")
    data = candidate_ranking_to_json_dict(result)

    assert set(data.keys()) == {
        "endpoint",
        "endpoint_kind",
        "kind",
        "ranked_candidates",
        "recommended_candidate_id",
    }


def test_candidate_ranking_json_kind_is_candidate_ranking() -> None:
    result = rank_candidates([], [], "video", "/dev/video0")
    data = candidate_ranking_to_json_dict(result)

    assert data["kind"] == "candidate_ranking"


def test_candidate_ranking_json_endpoint_fields() -> None:
    result = rank_candidates([], [], "audio-input", "hw:0,0")
    data = candidate_ranking_to_json_dict(result)

    assert data["endpoint_kind"] == "audio-input"
    assert data["endpoint"] == "hw:0,0"


def test_candidate_ranking_json_recommended_id_present() -> None:
    candidates = [_candidate("generic-id")]
    diagnostics = [_available_diagnostic("generic-id")]
    result = rank_candidates(candidates, diagnostics, "video", "/dev/video0")
    data = candidate_ranking_to_json_dict(result)

    assert data["recommended_candidate_id"] == "generic-id"


def test_candidate_ranking_json_recommended_id_null_when_none() -> None:
    result = rank_candidates([], [], "video", "/dev/video0")
    data = candidate_ranking_to_json_dict(result)

    assert data["recommended_candidate_id"] is None


def test_candidate_recommendation_json_has_expected_keys() -> None:
    candidates = [_candidate("generic-id")]
    diagnostics = [_available_diagnostic("generic-id")]
    result = rank_candidates(candidates, diagnostics, "video", "/dev/video0")
    item_data = candidate_recommendation_to_json_dict(result.ranked_candidates[0])

    assert set(item_data.keys()) == {
        "available",
        "candidate_id",
        "missing_elements",
        "rank",
        "reasons",
        "score",
        "selected_profile",
        "warnings",
    }


def test_candidate_recommendation_json_available_true() -> None:
    candidates = [_candidate("generic-id")]
    diagnostics = [_available_diagnostic("generic-id")]
    result = rank_candidates(candidates, diagnostics, "video", "/dev/video0")
    item_data = candidate_recommendation_to_json_dict(result.ranked_candidates[0])

    assert item_data["available"] is True
    assert item_data["missing_elements"] == []


def test_candidate_recommendation_json_unavailable_has_missing_elements() -> None:
    diagnostics = [_unavailable_diagnostic("jetson-id", ["nvjpegdec", "nveglglessink"])]
    result = rank_candidates([], diagnostics, "video", "/dev/video0")
    item_data = candidate_recommendation_to_json_dict(result.ranked_candidates[0])

    assert item_data["available"] is False
    assert "nvjpegdec" in item_data["missing_elements"]
    assert "nveglglessink" in item_data["missing_elements"]


def test_candidate_ranking_json_is_valid_json_string() -> None:
    candidates = [_candidate("generic-id")]
    diagnostics = [_available_diagnostic("generic-id")]
    result = rank_candidates(candidates, diagnostics, "video", "/dev/video0")
    data = candidate_ranking_to_json_dict(result)
    serialized = json.dumps(data, indent=2, sort_keys=True)
    parsed = json.loads(serialized)

    assert parsed["kind"] == "candidate_ranking"
    assert len(parsed["ranked_candidates"]) == 1


# ---------------------------------------------------------------------------
# Text rendering
# ---------------------------------------------------------------------------


def test_print_candidate_ranking_shows_recommended(capsys) -> None:
    from gst_device_explorer.cli.renderer import print_candidate_ranking

    candidates = [_candidate("generic-id")]
    diagnostics = [_available_diagnostic("generic-id")]
    result = rank_candidates(candidates, diagnostics, "video", "/dev/video0")

    print_candidate_ranking(result, as_json=False)
    out = capsys.readouterr().out

    assert "Recommended: generic-id" in out


def test_print_candidate_ranking_shows_no_available_when_none(capsys) -> None:
    from gst_device_explorer.cli.renderer import print_candidate_ranking

    result = rank_candidates([], [], "video", "/dev/video0")

    print_candidate_ranking(result, as_json=False)
    out = capsys.readouterr().out

    assert "No available candidate." in out


def test_print_candidate_ranking_shows_endpoint(capsys) -> None:
    from gst_device_explorer.cli.renderer import print_candidate_ranking

    result = rank_candidates([], [], "audio-input", "hw:0,0")

    print_candidate_ranking(result, as_json=False)
    out = capsys.readouterr().out

    assert "audio-input" in out
    assert "hw:0,0" in out


def test_print_candidate_ranking_shows_profile_label(capsys) -> None:
    from gst_device_explorer.cli.renderer import print_candidate_ranking

    candidates = [_candidate("generic-id", profile="generic-linux-video-preview")]
    diagnostics = [_available_diagnostic("generic-id")]
    result = rank_candidates(candidates, diagnostics, "video", "/dev/video0")

    print_candidate_ranking(result, as_json=False)
    out = capsys.readouterr().out

    assert "generic-linux-video-preview" in out


def test_print_candidate_ranking_shows_missing_elements_for_unavailable(capsys) -> None:
    from gst_device_explorer.cli.renderer import print_candidate_ranking

    diagnostics = [_unavailable_diagnostic("jetson-id", ["nvjpegdec", "nveglglessink"])]
    result = rank_candidates([], diagnostics, "video", "/dev/video0")

    print_candidate_ranking(result, as_json=False)
    out = capsys.readouterr().out

    assert "nvjpegdec" in out
    assert "nveglglessink" in out


def test_print_candidate_ranking_shows_suggested_checks(capsys) -> None:
    from gst_device_explorer.cli.renderer import print_candidate_ranking

    diagnostics = [_unavailable_diagnostic("jetson-id", ["nvjpegdec"])]
    result = rank_candidates([], diagnostics, "video", "/dev/video0")

    print_candidate_ranking(result, as_json=False)
    out = capsys.readouterr().out

    assert "gst-inspect-1.0 nvjpegdec" in out


def test_print_candidate_ranking_json_mode_emits_valid_json(capsys) -> None:
    from gst_device_explorer.cli.renderer import print_candidate_ranking

    result = rank_candidates([], [], "video", "/dev/video0")

    print_candidate_ranking(result, as_json=True)
    data = json.loads(capsys.readouterr().out)

    assert data["kind"] == "candidate_recommendation"
    assert data["data"]["kind"] == "candidate_ranking"


# ---------------------------------------------------------------------------
# CLI — recommend video
# ---------------------------------------------------------------------------


def test_recommend_video_json_exits_zero(monkeypatch, capsys) -> None:
    _patch_video_probes_with_available(monkeypatch)

    exit_code = main(["recommend", "video", "/dev/video0", "--json"])

    assert exit_code == 0


def test_recommend_video_json_emits_valid_json(monkeypatch, capsys) -> None:
    _patch_video_probes_with_available(monkeypatch)

    main(["recommend", "video", "/dev/video0", "--json"])
    data = json.loads(capsys.readouterr().out)

    assert isinstance(data, dict)
    assert data["kind"] == "candidate_recommendation"
    assert data["data"]["kind"] == "candidate_ranking"


def test_recommend_video_json_has_expected_keys(monkeypatch, capsys) -> None:
    _patch_video_probes_with_available(monkeypatch)

    main(["recommend", "video", "/dev/video0", "--json"])
    data = json.loads(capsys.readouterr().out)

    assert "kind" in data
    assert "schema_version" in data
    assert "tool_version" in data
    assert "data" in data
    assert "endpoint_kind" in data["data"]
    assert "endpoint" in data["data"]
    assert "recommended_candidate_id" in data["data"]
    assert "ranked_candidates" in data["data"]


def test_recommend_video_json_endpoint_is_device_path(monkeypatch, capsys) -> None:
    _patch_video_probes_with_available(monkeypatch)

    main(["recommend", "video", "/dev/video0", "--json"])
    data = json.loads(capsys.readouterr().out)

    assert data["data"]["endpoint"] == "/dev/video0"
    assert data["data"]["endpoint_kind"] == "video"


def test_recommend_video_text_exits_zero(monkeypatch, capsys) -> None:
    _patch_video_probes_with_available(monkeypatch)

    exit_code = main(["recommend", "video", "/dev/video0"])

    assert exit_code == 0


def test_recommend_video_text_shows_endpoint(monkeypatch, capsys) -> None:
    _patch_video_probes_with_available(monkeypatch)

    main(["recommend", "video", "/dev/video0"])
    out = capsys.readouterr().out

    assert "/dev/video0" in out


def test_recommend_video_no_capabilities_returns_empty_ranking(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        cli_commands.v4l2_probe, "discover_v4l2_capabilities", lambda path: []
    )
    monkeypatch.setattr(
        cli_commands.gst_probe, "inspect_gstreamer_environment", lambda: []
    )

    main(["recommend", "video", "/dev/video0", "--json"])
    data = json.loads(capsys.readouterr().out)

    assert data["data"]["recommended_candidate_id"] is None
    assert data["data"]["ranked_candidates"] == []


# ---------------------------------------------------------------------------
# CLI — recommend audio-input
# ---------------------------------------------------------------------------


def test_recommend_audio_input_json_exits_zero(monkeypatch, capsys) -> None:
    _patch_audio_input_probes_with_available(monkeypatch)

    exit_code = main(["recommend", "audio-input", "hw:0,0", "--json"])

    assert exit_code == 0


def test_recommend_audio_input_json_has_expected_keys(monkeypatch, capsys) -> None:
    _patch_audio_input_probes_with_available(monkeypatch)

    main(["recommend", "audio-input", "hw:0,0", "--json"])
    data = json.loads(capsys.readouterr().out)

    assert data["kind"] == "candidate_recommendation"
    assert data["data"]["endpoint_kind"] == "audio-input"
    assert data["data"]["endpoint"] == "hw:0,0"


def test_recommend_audio_input_text_exits_zero(monkeypatch, capsys) -> None:
    _patch_audio_input_probes_with_available(monkeypatch)

    exit_code = main(["recommend", "audio-input", "hw:0,0"])

    assert exit_code == 0


def test_recommend_audio_input_device_not_found_returns_empty(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        cli_commands.alsa_probe, "discover_alsa_audio_inputs", lambda: []
    )
    monkeypatch.setattr(
        cli_commands.gst_probe, "inspect_gstreamer_environment", lambda: []
    )

    main(["recommend", "audio-input", "hw:0,0", "--json"])
    data = json.loads(capsys.readouterr().out)

    assert data["data"]["recommended_candidate_id"] is None
    assert data["data"]["ranked_candidates"] == []


# ---------------------------------------------------------------------------
# CLI — recommend audio-output
# ---------------------------------------------------------------------------


def test_recommend_audio_output_json_exits_zero(monkeypatch, capsys) -> None:
    _patch_audio_output_probes_with_available(monkeypatch)

    exit_code = main(["recommend", "audio-output", "hw:0,0", "--json"])

    assert exit_code == 0


def test_recommend_audio_output_json_has_expected_keys(monkeypatch, capsys) -> None:
    _patch_audio_output_probes_with_available(monkeypatch)

    main(["recommend", "audio-output", "hw:0,0", "--json"])
    data = json.loads(capsys.readouterr().out)

    assert data["kind"] == "candidate_recommendation"
    assert data["data"]["endpoint_kind"] == "audio-output"
    assert data["data"]["endpoint"] == "hw:0,0"


def test_recommend_audio_output_text_exits_zero(monkeypatch, capsys) -> None:
    _patch_audio_output_probes_with_available(monkeypatch)

    exit_code = main(["recommend", "audio-output", "hw:0,0"])

    assert exit_code == 0


def test_recommend_audio_output_device_not_found_returns_empty(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        cli_commands.alsa_probe, "discover_alsa_audio_outputs", lambda: []
    )
    monkeypatch.setattr(
        cli_commands.gst_probe, "inspect_gstreamer_environment", lambda: []
    )

    main(["recommend", "audio-output", "hw:0,0", "--json"])
    data = json.loads(capsys.readouterr().out)

    assert data["data"]["recommended_candidate_id"] is None


# ---------------------------------------------------------------------------
# No pipeline execution
# ---------------------------------------------------------------------------


def test_rank_candidates_does_not_call_execution(monkeypatch) -> None:
    import gst_device_explorer.core.execution as execution_mod

    def _guard(*args, **kwargs):
        raise AssertionError("ranking must not execute pipelines")

    monkeypatch.setattr(execution_mod, "run_execution_plan", _guard)
    monkeypatch.setattr(execution_mod, "select_pipeline_candidate", _guard)

    candidates = [_candidate("generic-id")]
    diagnostics = [_available_diagnostic("generic-id")]
    result = rank_candidates(candidates, diagnostics, "video", "/dev/video0")

    assert result.recommended_candidate_id == "generic-id"


def test_recommend_cli_does_not_execute_pipeline(monkeypatch, capsys) -> None:
    import gst_device_explorer.core.execution as execution_mod

    execution_calls: list[str] = []

    def _guard(*args, **kwargs):
        execution_calls.append("called")
        raise AssertionError("CLI recommend must not execute pipelines")

    monkeypatch.setattr(execution_mod, "run_execution_plan", _guard)
    _patch_video_probes_with_available(monkeypatch)

    main(["recommend", "video", "/dev/video0", "--json"])

    assert execution_calls == []


# ---------------------------------------------------------------------------
# Regression — existing commands unchanged
# ---------------------------------------------------------------------------


def test_existing_pipeline_command_still_works(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        cli_commands.v4l2_probe,
        "discover_v4l2_capabilities",
        lambda path: [],
    )
    monkeypatch.setattr(
        cli_commands.gst_probe,
        "inspect_gstreamer_environment",
        lambda: [],
    )

    exit_code = main(["pipeline", "video", "/dev/video0"])
    assert exit_code == 0


def test_existing_profile_command_still_works(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        cli_commands.v4l2_probe,
        "discover_v4l2_capabilities",
        lambda path: [],
    )
    monkeypatch.setattr(
        cli_commands.gst_probe,
        "inspect_gstreamer_environment",
        lambda: [],
    )
    monkeypatch.setattr(
        cli_commands.discovery,
        "discover_composite_devices",
        lambda: [],
    )

    exit_code = main(["profile", "video", "/dev/video0"])
    assert exit_code == 0


def test_existing_report_command_still_works(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        cli_commands.v4l2_probe, "discover_v4l2_video_devices", lambda: []
    )
    monkeypatch.setattr(
        cli_commands.alsa_probe, "discover_alsa_audio_inputs", lambda: []
    )
    monkeypatch.setattr(
        cli_commands.alsa_probe, "discover_alsa_audio_outputs", lambda: []
    )
    monkeypatch.setattr(
        cli_commands.gst_probe, "inspect_gstreamer_environment", lambda: []
    )
    monkeypatch.setattr(
        cli_commands.discovery, "discover_composite_devices", lambda: []
    )
    monkeypatch.setattr(
        cli_commands.v4l2_probe, "discover_v4l2_capabilities", lambda path: []
    )

    exit_code = main(["report", "--json"])
    assert exit_code == 0


# ---------------------------------------------------------------------------
# Helpers and fixtures
# ---------------------------------------------------------------------------


def _available_diagnostic(
    candidate_id: str,
    device_kind: str = "video",
    device: str = "/dev/video0",
) -> PipelineDiagnostic:
    return PipelineDiagnostic(
        candidate_id=candidate_id,
        device_kind=device_kind,
        device=device,
        status="available",
        reason="Required GStreamer elements are available.",
        required_elements=["v4l2src", "autovideosink"],
        available_elements=["v4l2src", "autovideosink"],
        missing_elements=[],
        suggested_next_checks=[],
    )


def _unavailable_diagnostic(
    candidate_id: str,
    missing: list[str],
    device_kind: str = "video",
    device: str = "/dev/video0",
) -> PipelineDiagnostic:
    required = ["v4l2src"] + missing
    return PipelineDiagnostic(
        candidate_id=candidate_id,
        device_kind=device_kind,
        device=device,
        status="unavailable",
        reason="Required GStreamer elements are missing.",
        required_elements=required,
        available_elements=["v4l2src"],
        missing_elements=missing,
        suggested_next_checks=[f"gst-inspect-1.0 {e}" for e in missing],
    )


def _candidate(
    candidate_id: str,
    confidence: float = 0.8,
    profile: str = "generic-linux-video-preview",
    warnings: list[str] | None = None,
) -> PipelineCandidate:
    return PipelineCandidate(
        candidate_id=candidate_id,
        purpose="preview",
        command="gst-launch-1.0 ...",
        confidence=confidence,
        argv=["gst-launch-1.0"],
        reasons=["selected device"],
        warnings=warnings or [],
        required_elements=["v4l2src", "autovideosink"],
        selected_profile=profile,
    )


def _element_fact(element: str, available: bool) -> EnvironmentFact:
    return EnvironmentFact(
        name="gstreamer_element_available",
        value=available,
        source="gst-inspect-1.0",
        metadata={"element": element},
    )


def _mjpeg_capability() -> Capability:
    return Capability(
        name="video/x-raw",
        values={
            "media_type": "video",
            "pixel_format": "MJPG",
            "width": 1920,
            "height": 1080,
            "fps": [30.0],
        },
        source="v4l2-ctl",
    )


def _generic_video_environment() -> list[EnvironmentFact]:
    return [
        _element_fact("v4l2src", True),
        _element_fact("videoconvert", True),
        _element_fact("autovideosink", True),
        _element_fact("jpegparse", False),
        _element_fact("nvjpegdec", False),
        _element_fact("nvvidconv", False),
        _element_fact("nveglglessink", False),
    ]


def _audio_input_environment() -> list[EnvironmentFact]:
    return [
        _element_fact("alsasrc", True),
        _element_fact("audioconvert", True),
        _element_fact("audioresample", True),
        _element_fact("level", True),
        _element_fact("fakesink", True),
    ]


def _audio_output_environment() -> list[EnvironmentFact]:
    return [
        _element_fact("audiotestsrc", True),
        _element_fact("audioconvert", True),
        _element_fact("audioresample", True),
        _element_fact("alsasink", True),
    ]


def _audio_input_device() -> Device:
    return Device(
        id="hw:0,0",
        kind="audio_input",
        name="USB Audio: Capture",
        metadata={"backend": "alsa", "alsa_device": "hw:0,0"},
    )


def _audio_output_device() -> Device:
    return Device(
        id="hw:0,0",
        kind="audio_output",
        name="USB Audio: Playback",
        metadata={"backend": "alsa", "alsa_device": "hw:0,0"},
    )


def _patch_video_probes_with_available(monkeypatch) -> None:
    monkeypatch.setattr(
        cli_commands.v4l2_probe,
        "discover_v4l2_capabilities",
        lambda path: [_mjpeg_capability()],
    )
    monkeypatch.setattr(
        cli_commands.gst_probe,
        "inspect_gstreamer_environment",
        lambda: _generic_video_environment(),
    )


def _patch_audio_input_probes_with_available(monkeypatch) -> None:
    monkeypatch.setattr(
        cli_commands.alsa_probe,
        "discover_alsa_audio_inputs",
        lambda: [_audio_input_device()],
    )
    monkeypatch.setattr(
        cli_commands.gst_probe,
        "inspect_gstreamer_environment",
        lambda: _audio_input_environment(),
    )


def _patch_audio_output_probes_with_available(monkeypatch) -> None:
    monkeypatch.setattr(
        cli_commands.alsa_probe,
        "discover_alsa_audio_outputs",
        lambda: [_audio_output_device()],
    )
    monkeypatch.setattr(
        cli_commands.gst_probe,
        "inspect_gstreamer_environment",
        lambda: _audio_output_environment(),
    )
