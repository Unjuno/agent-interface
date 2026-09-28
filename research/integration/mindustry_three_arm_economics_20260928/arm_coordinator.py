"""Compose frozen task lifecycle with the bounded adaptive route adapter.

This host-only coordinator has no game, model, or input backend. A caller must
provide each observation/model response and separately obtain a final fresh
locator before any pointer action.
"""

from __future__ import annotations

from adaptive_route import (TargetBundle, require_current_locator, route_task)
from runner_contract import Lifecycle, load_plan


class ArmCoordinator:
    def __init__(self, arm: str, plan: dict | None = None):
        self.plan = plan if plan is not None else load_plan()
        self.arm = arm
        self.lifecycle = Lifecycle(self.plan, arm)
        self.cached: TargetBundle | None = None
        self.resolved_bundle: TargetBundle | None = None
        self.task_records: list[dict] = []
        self.pending_resolution = False
        self.attempt_started = False

    def resolve(self, observation: dict, width: int, height: int, model_call) -> dict:
        """Resolve exactly the current scheduled task without granting input."""
        task = self.lifecycle.current
        if (self.lifecycle.phase != "ready" or self.pending_resolution
                or self.attempt_started):
            raise ValueError("task routing requires one unresolved ready task")
        # Consume this task's sole attempt before any model callback. A refusal
        # or exception after dispatch must not become a silent formal retry.
        self.attempt_started = True
        result = route_task(arm=self.arm, route=task.route,
            task_id=task.task_id, layout=task.layout, cached=self.cached,
            observation=observation, width=width, height=height,
            model_call=model_call)
        if self.arm == "persistent":
            self.cached = result["cache_update"]
        self.resolved_bundle = result["bundle"]
        self.pending_resolution = True
        record = {"task_id": task.task_id, "layout": task.layout,
                  "route": task.route, "model_calls": result["model_calls"],
                  "old_reference_pointer_admissions":
                      result["old_reference_pointer_admissions"],
                  "old_reference_status": result["old_reference_status"]}
        self.task_records.append(record)
        return {"task": task, "bundle": result["bundle"], "record": record}

    def locator_for_input(self, observation: dict, layout: str) -> dict:
        """Revalidate one resolved locator against a fresh pre-input observation."""
        if not self.pending_resolution or self.resolved_bundle is None:
            raise ValueError("pre-input locator requires one resolved task")
        return require_current_locator(self.resolved_bundle, observation, layout)

    def score(self, passed: bool) -> dict:
        """Record independent task scoring; failed tasks cannot be reset."""
        if not self.pending_resolution:
            raise ValueError("task score requires one resolved task")
        return self.lifecycle.score(passed)

    def reset(self, witness: bool) -> dict:
        """Accept only the private verified reset witness for a passing task."""
        return self.lifecycle.reset(witness)

    def advance(self) -> dict | None:
        """Advance only after a passing score and verified reset."""
        result = self.lifecycle.advance()
        self.pending_resolution = False
        self.attempt_started = False
        self.resolved_bundle = None
        return result
