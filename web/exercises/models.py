from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class OutputSpec:
    label: str
    example: str
    rules: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class SkillUse:
    skill_id: str
    role: str = "target"  # target | reinforcement | prerequisite


@dataclass
class Dataset:
    kind: str
    title: str
    files: dict[str, str]
    records: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class Exercise:
    template_id: str
    title: str
    prompt: str
    style: str  # focused | integration | challenge
    tools: list[str]
    skills: list[SkillUse]
    output: OutputSpec
    dataset_kind: str
    files: dict[str, str]
    expected: str
    solution: str
    explanation: str
