"""Host-only construction contract for the frozen six-task runner.

This module does not launch Mindustry, call a model, or authorize a live run.
It makes the preregistered arm schedule and private reset/geometry barriers
executable so the eventual runtime composition can be checked before allocation.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json


HERE = Path(__file__).resolve().parent
PREREGISTRATION = HERE.parent / "mindustry_three_arm_economics_prereg_v1" / "PREREGISTRATION.json"


@dataclass(frozen=True)
class Task:
    task_id: str
    layout: str
    route: str
    model_calls: int
    epoch: int


def load_plan(path: Path = PREREGISTRATION) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def arm_schedule(plan: dict, arm: str) -> tuple[Task, ...]:
    """Return the frozen tasks for one arm, rejecting incomplete/mutated plans."""
    if arm not in plan["arm_order"]:
        raise ValueError("unknown arm")
    ids, layouts = plan["tasks"], plan["layouts"]
    routes, counts = plan["routes"][arm], plan["task_model_calls"][arm]
    if not (len(ids) == len(layouts) == len(routes) == len(counts) == 6):
        raise ValueError("six-task schedule required")
    if ids != ["A1", "A2", "A3", "B1", "B2", "B3"]:
        raise ValueError("task order differs from preregistration")
    expected_routes = {
        "plain": ["cold"] * 6,
        "ephemeral": ["cold"] * 6,
        "persistent": ["cold", "reuse", "reuse", "repair", "reuse", "reuse"],
    }
    expected_calls = {"plain": [1] * 6, "ephemeral": [1] * 6,
                      "persistent": [1, 0, 0, 1, 0, 0]}
    if routes != expected_routes[arm] or counts != expected_calls[arm]:
        raise ValueError("route or model-call schedule differs from preregistration")
    if layouts != ["A", "A", "A", "B", "B", "B"]:
        raise ValueError("layout schedule differs from preregistration")
    return tuple(Task(task_id, layout, route, calls, index)
                 for index, (task_id, layout, route, calls) in enumerate(
                     zip(ids, layouts, routes, counts), start=1))


def controller_envelope(plan: dict, task: Task) -> dict:
    """Construct only the fields permitted on the agent-visible task channel."""
    visible = plan["task_contract"]["controller_visible_fields"]
    if visible != ["task_id", "task", "layout", "benchmark_epoch"]:
        raise ValueError("controller-visible field contract differs from preregistration")
    return {"task_id": task.task_id, "task": plan["task_contract"]["text"],
            "layout": task.layout, "benchmark_epoch": task.epoch}


class Lifecycle:
    """Enforce score-before-reset, witness-before-next, and the single A→B flip."""

    def __init__(self, plan: dict, arm: str = "plain"):
        self.plan = plan
        self.arm = arm
        self.tasks = arm_schedule(plan, arm)
        self.index = 0
        self.phase = "ready"
        self.events: list[dict] = []

    @property
    def current(self) -> Task:
        if self.index >= len(self.tasks):
            raise ValueError("all tasks complete")
        return self.tasks[self.index]

    def _emit(self, event: str, **fields) -> dict:
        row = {"event": event, **fields}
        self.events.append(row)
        return row

    def score(self, passed: bool) -> dict:
        if type(passed) is not bool:
            raise ValueError("score outcome must be boolean")
        if self.phase != "ready":
            raise ValueError("score requires a ready task")
        row = self._emit("score", task_id=self.current.task_id, passed=passed)
        self.phase = "scored" if passed else "failed"
        return row

    def reset(self, witness: bool) -> dict:
        if type(witness) is not bool:
            raise ValueError("reset witness must be boolean")
        if self.phase != "scored":
            raise ValueError("reset requires an independently passing score")
        row = self._emit("reset_witness", task_id=self.current.task_id,
                         verified=witness)
        if not witness:
            self.phase = "failed"
            return row
        self.phase = "between_tasks"
        return row

    def advance(self) -> dict | None:
        if self.phase != "between_tasks":
            raise ValueError("next task requires a verified reset witness")
        prior = self.current
        self.index += 1
        if self.index == len(self.tasks):
            self.phase = "complete"
            return self._emit("complete", task_id=prior.task_id)
        current = self.current
        if prior.task_id == "A3":
            if prior.layout != "A" or current.layout != "B":
                raise ValueError("geometry transition is not A3→B1")
            self._emit("geometry_mutation", after="A3.reset_witness",
                       before="B1.task_ready", from_layout="A", to_layout="B")
        self.phase = "ready"
        return self._emit("task_ready", task_id=current.task_id,
                          layout=current.layout, benchmark_epoch=current.epoch)
