from __future__ import annotations

import re
from typing import Any


SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?。！？])\s+")


def split_sentences(text: str) -> list[str]:
    cleaned = re.sub(r"\s+", " ", text).strip()
    if not cleaned:
        return []
    parts = SENTENCE_SPLIT_RE.split(cleaned)
    return [part.strip() for part in parts if part.strip()]


def _make_issue(
    issue_id: str,
    issue_type: str,
    severity: str,
    sentence_id: str,
    title: str,
    detail: str,
) -> dict[str, str]:
    return {
        "id": issue_id,
        "type": issue_type,
        "severity": severity,
        "sentence_id": sentence_id,
        "title": title,
        "detail": detail,
    }


def detect_heuristic_issues(sentences: list[str]) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    lower_sentences = [sentence.lower() for sentence in sentences]
    sid = lambda idx: f"s-{idx + 1}"

    term_idx_a = next(
        (
            idx
            for idx, sentence in enumerate(lower_sentences)
            if "threshold voltage window" in sentence
        ),
        None,
    )
    term_idx_b = next(
        (
            idx
            for idx, sentence in enumerate(lower_sentences)
            if "switching threshold bandwidth" in sentence
        ),
        None,
    )
    if term_idx_a is not None and term_idx_b is not None:
        issues.append(
            _make_issue(
                issue_id="h-term-1",
                issue_type="term",
                severity="medium",
                sentence_id=sid(term_idx_b),
                title="Terminology Drift",
                detail=(
                    "The concept name changes from 'threshold voltage window' "
                    "to 'switching threshold bandwidth'."
                ),
            )
        )

    improve_idx = next(
        (
            idx
            for idx, sentence in enumerate(lower_sentences)
            if ("improve" in sentence or "higher robustness" in sentence)
            and "robust" in sentence
        ),
        None,
    )
    reduce_idx = next(
        (
            idx
            for idx, sentence in enumerate(lower_sentences)
            if ("reduce" in sentence or "lower robustness" in sentence)
            and "robust" in sentence
        ),
        None,
    )
    if improve_idx is not None and reduce_idx is not None and improve_idx != reduce_idx:
        issues.append(
            _make_issue(
                issue_id="h-logic-1",
                issue_type="logic",
                severity="high",
                sentence_id=sid(reduce_idx),
                title="Logic Conflict",
                detail=(
                    "One sentence claims robustness improves while another says it decreases."
                ),
            )
        )

    figure_claim_idx = next(
        (
            idx
            for idx, sentence in enumerate(lower_sentences)
            if "figure" in sentence and "improve" in sentence and "robust" in sentence
        ),
        None,
    )
    caption_conflict_idx = next(
        (
            idx
            for idx, sentence in enumerate(lower_sentences)
            if "caption" in sentence and "reduce" in sentence and "robust" in sentence
        ),
        None,
    )
    if figure_claim_idx is not None and caption_conflict_idx is not None:
        issues.append(
            _make_issue(
                issue_id="h-cite-1",
                issue_type="citation_figure",
                severity="high",
                sentence_id=sid(caption_conflict_idx),
                title="Figure Caption Conflict",
                detail=(
                    "Main text and figure caption describe opposite robustness trends."
                ),
            )
        )

    return issues


def merge_issues(
    base_issues: list[dict[str, str]], glm_issues: list[dict[str, str]]
) -> list[dict[str, str]]:
    seen: set[tuple[str, str]] = set()
    merged: list[dict[str, str]] = []

    for issue in base_issues + glm_issues:
        key = (issue.get("type", ""), issue.get("sentence_id", ""))
        if key in seen:
            continue
        seen.add(key)
        merged.append(issue)
    return merged


def normalize_glm_issues(raw_issues: list[dict[str, Any]]) -> list[dict[str, str]]:
    normalized: list[dict[str, str]] = []
    for idx, issue in enumerate(raw_issues):
        sentence_id = str(issue.get("sentence_id", "")).strip()
        issue_type = str(issue.get("type", "")).strip() or "logic"
        severity = str(issue.get("severity", "")).strip().lower() or "medium"
        title = str(issue.get("title", "")).strip() or "LLM Review Issue"
        detail = str(issue.get("detail", "")).strip() or "Detected by LLM review."

        if not sentence_id.startswith("s-"):
            continue
        if severity not in {"low", "medium", "high"}:
            severity = "medium"
        if issue_type not in {"term", "logic", "citation_figure"}:
            issue_type = "logic"

        normalized.append(
            {
                "id": f"g-{issue_type}-{idx + 1}",
                "type": issue_type,
                "severity": severity,
                "sentence_id": sentence_id,
                "title": title,
                "detail": detail,
            }
        )
    return normalized


def analyze_text(text: str) -> dict[str, Any]:
    sentences = split_sentences(text)
    issues = detect_heuristic_issues(sentences)
    return {
        "sentences": [{"id": f"s-{idx + 1}", "text": sentence} for idx, sentence in enumerate(sentences)],
        "issues": issues,
        "source": "heuristic",
    }

