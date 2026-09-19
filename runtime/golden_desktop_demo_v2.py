"""Golden desktop entry using one persistent typed grounding-model thread."""
from __future__ import annotations

import statistics
import sys
import time
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
RESEARCH = ROOT / "research" / "live_control"
for path in (HERE, RESEARCH):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

import golden_desktop_demo as base
from integrated_efficiency_app_server_model_v1 import PersistentGroundingModel


def run_live(out: Path, seed: int, *, grounding_model_type=PersistentGroundingModel) -> dict:
    health = base.doctor()
    if not health["passed"]:
        raise RuntimeError("doctor failed; run the doctor command for exact missing dependencies")
    if out.exists():
        raise FileExistsError(f"refusing to reuse output directory: {out}")
    out.mkdir(parents=True)
    base.dump(out / "doctor.json", health)
    config = base.configuration()
    chromium = config["chromium"]
    node = config["windows_node"]
    cli = config["windows_cli"]
    assert chromium is not None and node is not None and cli is not None
    implementation, client_type = base.configure_research_modules(config, chromium)
    implementation.OUT = out
    implementation.RuntimeClient = client_type
    started = time.perf_counter_ns()
    preflight = implementation.preflight_call("persistent", "compiled")
    workspace = out / "workspaces" / "persistent"
    with grounding_model_type(
            out / "persistent-grounding-app-server", workspace,
            node=node, cli=base.windows_arg(cli), contract="compiled",
            model="gpt-5.6-luna", effort="low") as grounding:
        implementation.call_model = grounding.call
        rows, independent = implementation.run_arm("persistent", seed, workspace)
        grounding_thread_id = grounding.thread_id
        grounding_turns = grounding.calls
    ended = time.perf_counter_ns()
    usage_fields = ("input_tokens", "cached_input_tokens", "cache_write_input_tokens",
                    "output_tokens", "reasoning_output_tokens")
    calls = [preflight] + [call for row in rows for call in row["model_calls"]]
    usage = {field: sum(call["usage"][field] for call in calls) for field in usage_fields}
    feedback_ms = [value / 1e6 for row in rows for value in row["input_feedback_ns"]]
    report = {
        "schema": "agent_interface_golden_desktop_live_v2",
        "passed": (
            independent.get("success") is True
            and len(rows) == 6
            and all(row["exact_submission"] and row["releases_verified"] for row in rows)
            and rows[3]["repair"] == {
                "required": True, "old_reference_status": "missing",
                "old_reference_pointer_admissions": 0,
                "attempted": True, "succeeded": True,
            }
            and grounding_turns == 2
            and len({call["call_id"] for call in calls}) == len(calls)
        ),
        "seed": seed,
        "tasks_exact": sum(row["exact_submission"] for row in rows),
        "routes": [row["route"] for row in rows],
        "planner_generations_including_preflight": len(calls),
        "model_visible_images": sum(row["model_visible_images"] for row in rows),
        "usage": usage,
        "grounding_transport": "one capability-minimized Codex app-server process/thread",
        "grounding_thread_id": grounding_thread_id,
        "grounding_turns": grounding_turns,
        "grounding_call_ids": [call["call_id"] for row in rows
                               for call in row["model_calls"]],
        "old_target_pointer_admissions": sum(row["old_target_pointer_admissions"] for row in rows),
        "all_releases_verified": all(row["releases_verified"] for row in rows),
        "input_feedback_median_ms": statistics.median(feedback_ms),
        "six_task_elapsed_ms": sum(row["elapsed_ns"] for row in rows) / 1e6,
        "whole_command_elapsed_ms": (ended - started) / 1e6,
        "independent_evaluation": independent,
        "tasks": rows,
        "environment": health,
        "scope": "one fresh persistent typed-grounding demonstration; no baseline, rate, generality, token-efficiency or human-speed claim",
    }
    base.dump(out / "golden-report.json", report)
    return report


def main() -> int:
    base.run_live = run_live
    return base.main()


if __name__ == "__main__":
    raise SystemExit(main())
