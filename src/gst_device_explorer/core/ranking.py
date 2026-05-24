"""Candidate ranking and recommendation builder."""

from __future__ import annotations

from gst_device_explorer.core.models import (
    CandidateRanking,
    CandidateRecommendation,
    PipelineCandidate,
    PipelineDiagnostic,
)


def rank_candidates(
    candidates: list[PipelineCandidate],
    diagnostics: list[PipelineDiagnostic],
    endpoint_kind: str,
    endpoint: str,
) -> CandidateRanking:
    """Rank existing pipeline candidates for one endpoint.

    Accepts already-generated candidates and diagnostics.
    Does not probe hardware or execute pipelines.
    """
    candidate_map = {c.candidate_id: c for c in candidates}

    scored: list[tuple[int, str, CandidateRecommendation]] = []
    for diagnostic in diagnostics:
        candidate = candidate_map.get(diagnostic.candidate_id)
        available = diagnostic.status == "available"
        score = _compute_score(available, candidate)
        reasons = _build_reasons(diagnostic)
        warnings = _build_warnings(diagnostic, candidate)
        item = CandidateRecommendation(
            candidate_id=diagnostic.candidate_id,
            rank=0,
            selected_profile=candidate.selected_profile if candidate else None,
            available=available,
            score=score,
            reasons=reasons,
            warnings=warnings,
            missing_elements=list(diagnostic.missing_elements),
        )
        scored.append((score, diagnostic.candidate_id, item))

    scored.sort(key=lambda t: (-t[0], t[1]))

    ranked: list[CandidateRecommendation] = []
    recommended_id: str | None = None
    for rank, (score, cid, item) in enumerate(scored, start=1):
        ranked.append(
            CandidateRecommendation(
                candidate_id=item.candidate_id,
                rank=rank,
                selected_profile=item.selected_profile,
                available=item.available,
                score=item.score,
                reasons=item.reasons,
                warnings=item.warnings,
                missing_elements=item.missing_elements,
            )
        )
        if recommended_id is None and item.available:
            recommended_id = cid

    return CandidateRanking(
        kind="candidate_ranking",
        endpoint_kind=endpoint_kind,
        endpoint=endpoint,
        recommended_candidate_id=recommended_id,
        ranked_candidates=ranked,
    )


def empty_ranking(endpoint_kind: str, endpoint: str) -> CandidateRanking:
    """Return an empty ranking when no device or candidates are found."""
    return CandidateRanking(
        kind="candidate_ranking",
        endpoint_kind=endpoint_kind,
        endpoint=endpoint,
        recommended_candidate_id=None,
        ranked_candidates=[],
    )


def _compute_score(available: bool, candidate: PipelineCandidate | None) -> int:
    if not available:
        return 0
    score = 100
    if candidate is not None:
        score += int(candidate.confidence * 10)
    return score


def _build_reasons(diagnostic: PipelineDiagnostic) -> list[str]:
    return [diagnostic.reason]


def _build_warnings(
    diagnostic: PipelineDiagnostic,
    candidate: PipelineCandidate | None,
) -> list[str]:
    if candidate is not None:
        return list(candidate.warnings)
    return []
