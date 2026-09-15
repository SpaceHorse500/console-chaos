from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Dataset:
    kind: str
    title: str
    files: dict[str, str]
    records: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class Exercise:
    title: str
    prompt: str
    difficulty: int
    tools: list[str]
    dataset_kind: str
    files: dict[str, str]
    expected: str
    solution: str
    explanation: str
