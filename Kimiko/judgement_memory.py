"""Case memory support for Kimiko's judgement system."""

from __future__ import annotations

from dataclasses import dataclass
import time


@dataclass
class CaseFile:
    """Represents one evaluated case in judgement mode."""

    case_id: int
    case_input: str
    verdict: str
    score: int
    created_at: float


class JudgementMemory:
    """In-memory case registry with auto-incrementing IDs."""

    def __init__(self) -> None:
        self._next_case_id = 1
        self._cases: list[CaseFile] = []

    def next_case_id(self) -> int:
        case_id = self._next_case_id
        self._next_case_id += 1
        return case_id

    def add_case(self, case_id: int, case_input: str, verdict: str, score: int) -> CaseFile:
        record = CaseFile(
            case_id=case_id,
            case_input=case_input,
            verdict=verdict,
            score=score,
            created_at=time.time(),
        )
        self._cases.append(record)
        return record

    def list_cases(self) -> list[CaseFile]:
        return list(self._cases)

    def clear(self) -> None:
        self._cases.clear()
