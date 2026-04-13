"""Working-set evaluation routines."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from change_radar.index.service import index_repository
from change_radar.ranking.task import build_working_set


@dataclass(slots=True, frozen=True)
class WorkingSetEvalCase:
    name: str
    task: str
    expected_files: tuple[str, ...]


@dataclass(slots=True, frozen=True)
class WorkingSetEvalResult:
    name: str
    task: str
    expected_files: tuple[str, ...]
    predicted_top_10: tuple[str, ...]
    recall_at_5: float
    recall_at_10: float
    missing_from_top_10: tuple[str, ...]


def load_eval_cases(path: Path) -> list[WorkingSetEvalCase]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    cases = payload["cases"] if isinstance(payload, dict) else payload

    return [
        WorkingSetEvalCase(
            name=str(case["name"]),
            task=str(case["task"]),
            expected_files=tuple(str(item) for item in case["expected_files"]),
        )
        for case in cases
    ]


def evaluate_working_set(
    repo_root: Path, case_file: Path, *, limit: int = 10, refresh_index: bool = True
) -> list[WorkingSetEvalResult]:
    repo_root = repo_root.resolve()
    if refresh_index:
        index_repository(repo_root)

    cases = load_eval_cases(case_file)
    results: list[WorkingSetEvalResult] = []

    for case in cases:
        ranked = build_working_set(repo_root, case.task, limit=limit)
        predicted = tuple(item.relative_path for item in ranked[:limit])
        predicted_top_5 = predicted[:5]
        recall_at_5 = _recall(case.expected_files, predicted_top_5)
        recall_at_10 = _recall(case.expected_files, predicted)
        missing = tuple(item for item in case.expected_files if item not in predicted)
        results.append(
            WorkingSetEvalResult(
                name=case.name,
                task=case.task,
                expected_files=case.expected_files,
                predicted_top_10=predicted,
                recall_at_5=recall_at_5,
                recall_at_10=recall_at_10,
                missing_from_top_10=missing,
            )
        )

    return results


def _recall(expected_files: tuple[str, ...], predicted_files: tuple[str, ...]) -> float:
    if not expected_files:
        return 1.0
    hits = sum(1 for item in expected_files if item in predicted_files)
    return hits / len(expected_files)
