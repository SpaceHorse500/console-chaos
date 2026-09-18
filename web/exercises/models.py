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


@dataclass(frozen=True)
class FieldSpec:
    """Metadata used by the randomized task grammar.

    ``index`` is the one-based field position for awk-compatible tabular data.
    JSONL datasets leave it as None and use the field name directly with jq.
    ``role`` is semantic guidance rather than a hard restriction; it lets the
    generator prefer sensible combinations while still allowing deliberately
    synthetic practice questions.
    """

    name: str
    label: str
    index: int | None = None
    type: str = "text"  # text | number
    role: str = "categorical"  # identifier | categorical | metric | timestamp
    operators: tuple[str, ...] = ("==", "!=")
    can_filter: bool = True
    can_output: bool = True
    can_group: bool = True
    can_sum: bool = False
    can_average: bool = False
    output_suffix: str = ""
    example: str = "value"
    decimals: int | None = None


@dataclass
class Dataset:
    kind: str
    title: str
    files: dict[str, str]
    records: list[dict[str, Any]] = field(default_factory=list)

    # Optional schema metadata for the compositional exercise generator.
    primary_file: str | None = None
    format: str = "custom"  # csv | whitespace | colon | jsonl | custom
    delimiter: str | None = None
    header_rows: int = 0
    fields: dict[str, FieldSpec] = field(default_factory=dict)


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
