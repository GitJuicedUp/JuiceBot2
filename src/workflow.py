"""Multi-step workflow orchestration engine for JuiceBot."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable

logger = logging.getLogger(__name__)


class StepStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class WorkflowStep:
    """A single step within a workflow."""

    name: str
    handler: Callable[..., Any]
    args: tuple[Any, ...] = field(default_factory=tuple)
    kwargs: dict[str, Any] = field(default_factory=dict)
    status: StepStatus = StepStatus.PENDING
    result: Any = None
    error: str | None = None
    duration_ms: float = 0.0

    def run(self) -> Any:
        self.status = StepStatus.RUNNING
        start = time.monotonic()
        try:
            self.result = self.handler(*self.args, **self.kwargs)
            self.status = StepStatus.SUCCESS
        except Exception as exc:  # noqa: BLE001
            self.error = str(exc)
            self.status = StepStatus.FAILED
            logger.error("Step '%s' failed: %s", self.name, exc)
        finally:
            self.duration_ms = (time.monotonic() - start) * 1000
        return self.result


@dataclass
class WorkflowResult:
    """Aggregated result of a completed workflow run."""

    name: str
    steps: list[WorkflowStep]
    success: bool
    total_duration_ms: float

    def summary(self) -> str:
        lines = [f"Workflow: {self.name}", f"Status: {'✓ success' if self.success else '✗ failed'}"]
        for step in self.steps:
            icon = {"success": "✓", "failed": "✗", "skipped": "–", "pending": "?", "running": "…"}.get(
                step.status.value, "?"
            )
            lines.append(f"  {icon} {step.name} ({step.duration_ms:.0f} ms)")
            if step.error:
                lines.append(f"      Error: {step.error}")
        lines.append(f"Total time: {self.total_duration_ms:.0f} ms")
        return "\n".join(lines)


class Workflow:
    """Executes a named sequence of WorkflowSteps, stopping on the first failure."""

    def __init__(self, name: str) -> None:
        self.name = name
        self._steps: list[WorkflowStep] = []

    def add_step(
        self,
        name: str,
        handler: Callable[..., Any],
        *args: Any,
        **kwargs: Any,
    ) -> "Workflow":
        self._steps.append(WorkflowStep(name=name, handler=handler, args=args, kwargs=kwargs))
        return self

    def run(self) -> WorkflowResult:
        logger.info("Starting workflow '%s' with %d step(s)", self.name, len(self._steps))
        start = time.monotonic()
        failed = False

        for step in self._steps:
            if failed:
                step.status = StepStatus.SKIPPED
                continue
            step.run()
            if step.status == StepStatus.FAILED:
                failed = True

        total_ms = (time.monotonic() - start) * 1000
        result = WorkflowResult(
            name=self.name,
            steps=self._steps,
            success=not failed,
            total_duration_ms=total_ms,
        )
        logger.info("Workflow '%s' finished in %.0f ms — %s", self.name, total_ms, "OK" if result.success else "FAILED")
        return result
