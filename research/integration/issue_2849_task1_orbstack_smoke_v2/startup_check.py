"""No-model checked-runtime startup gate; performs observation only."""
from __future__ import annotations

import json
import os
from pathlib import Path
import sys

REPO = Path(os.environ["ISSUE_2849_REPO"]).resolve()
OUT = Path(os.environ["ISSUE_2849_STARTUP_DIR"]).resolve()
for root in (REPO, REPO / "research/live_control",
             REPO / "research/observation_tiles",
             REPO / "research/observation_gating",
             REPO / "research/real_apps_v1"):
    sys.path.insert(0, str(root))

import integrated_efficiency_client_v1 as client_module

client_module.HERE = Path(__file__).resolve().parent
RuntimeClient = client_module.RuntimeClient


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=False)
    with RuntimeClient(OUT / "runtime", 284901) as client:
        tasks = client.ready["goal"]["tasks"]
        if len(tasks) != 6 or tasks[0]["task_id"] != "task-1":
            raise RuntimeError("STOP_UNEXPECTED_FIXTURE_TASKS")
        observation = client.submit("startup-read-only-observe", [{"op": "observe"}])
        release = observation["terminal"].get("release", {})
        receipt = {
            "status": "PASS_RUNTIME_STARTUP_NO_MODEL" if (
                observation["terminal"].get("status") == "completed"
                and bool(observation["observations"])
                and release.get("verified") is True
                and release.get("keys_down") == []
                and release.get("buttons_down") == []
                and not (client.runtime / "submission-history.jsonl").exists()
            ) else "FAIL_RUNTIME_STARTUP_NO_MODEL",
            "app": "chromium", "seed": 284901,
            "task_count": len(tasks),
            "first_task": {k: tasks[0][k] for k in ("task_id", "layout", "phase")},
            "observation_count": len(observation["observations"]),
            "model_calls": 0, "submission_history_exists":
                (client.runtime / "submission-history.jsonl").exists(),
            "release": release,
        }
        (OUT / "startup-result.json").write_text(
            json.dumps(receipt, indent=2, sort_keys=True) + "\n",
            encoding="utf-8", newline="\n")
    return 0 if receipt["status"] == "PASS_RUNTIME_STARTUP_NO_MODEL" else 1


if __name__ == "__main__":
    raise SystemExit(main())
