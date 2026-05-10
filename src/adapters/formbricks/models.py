from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class QuestionnaireResponse:
    respondent_id: str
    demographics: dict[str, Any] = field(default_factory=dict)
    scales: dict[str, dict[str, Any]] = field(default_factory=dict)
    nps: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class TaskResult:
    task_id: str
    seconds: int
    status: str


@dataclass
class UserTestResult:
    respondent_id: str
    system_name: str
    tasks: list[TaskResult]
    demographics: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
