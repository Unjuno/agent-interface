"""Execute one fresh plain-arm task through the OrbStack selected backend."""
from __future__ import annotations

import json
import os
from pathlib import Path
import sys

REPO = Path(os.environ["ISSUE_2849_REPO"]).resolve()
OUT = Path(os.environ["ISSUE_2849_RUN_DIR"]).resolve()
SEED = int(os.environ["ISSUE_2849_SEED"])
LIVE = REPO / "research/live_control"
for import_root in (REPO, LIVE, REPO / "research/observation_tiles",
                    REPO / "research/observation_gating",
                    REPO / "research/real_apps_v1"):
    sys.path.insert(0, str(import_root))

from docker_model_call_backend_v1 import call as docker_model_call
import integrated_efficiency_client_v1 as client_module
from run_integrated_efficiency_live_v1 import run_task

client_module.HERE = Path(__file__).resolve().parent
RuntimeClient = client_module.RuntimeClient


def dump(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n",
                    encoding="utf-8", newline="\n")


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    allowed_existing = {"pre-call-source-manifest.json"}
    unexpected = {path.name for path in OUT.iterdir()} - allowed_existing
    if unexpected:
        raise RuntimeError("STOP_OUTPUT_PATH_NOT_FRESH:" + ",".join(sorted(unexpected)))
    if not (OUT / "pre-call-source-manifest.json").is_file():
        raise RuntimeError("STOP_MISSING_PRECALL_SOURCE_MANIFEST")
    dump(OUT / "execution-config.json", {
        "source_manifest": "pre-call-source-manifest.json",
        "task_seed": SEED, "task_scope": "task-1/layout-A/cold/plain",
        "docker_host": os.environ.get("DOCKER_HOST"),
        "selected_backend": "docker_model_call_backend_v1.call",
        "selected_runner": os.environ.get("AGENT_INTERFACE_DOCKER_RUNNER"),
        "model_container_image": os.environ.get("AGENT_INTERFACE_DOCKER_IMAGE"),
        "model_call_limit": 1, "authority_granted": False,
    })
    workspace = OUT / "workspace"
    workspace.mkdir()
    runtime_root = OUT / "runtime"
    with RuntimeClient(runtime_root, SEED) as client:
        task = client.ready["goal"]["tasks"][0]
        if (task["task_id"], task["layout"], task["phase"]) != (
                "task-1", "A", "cold"):
            raise RuntimeError("STOP_UNEXPECTED_FIRST_TASK")
        dump(OUT / "frozen-task.json", {
            "seed": SEED, "task_id": task["task_id"], "layout": task["layout"],
            "phase": task["phase"], "token": task["token"], "url": task["url"],
            "route": "plain", "maximum_image_model_calls": 1,
        })
        row, cached, detail = run_task(
            client, "plain", task, 0, None, workspace,
            OUT / "model-calls" / "plain", model_call=docker_model_call)
        dump(OUT / "task-trace.json", row)
        dump(OUT / "task-detail.json", detail)
        full_fixture = client.finish("issue-2849-task1-orbstack-smoke-v2")
        dump(OUT / "six-task-fixture-evaluation.json", full_fixture)
        history = client.runtime / "submission-history.jsonl"
        records = ([json.loads(line) for line in history.read_text(
            encoding="utf-8").splitlines()] if history.exists() else [])
        dump(OUT / "submission-history.snapshot.json", records)
        task_rows = [record for record in records
                     if record.get("task_id") == task["task_id"]]
        scoped = {
            "status": "PASS_TASK1_SCOPED" if (
                row.get("typed_outcome") == "completed"
                and row.get("model_visible_images") == 1
                and len(row.get("model_calls", [])) == 1
                and row.get("submission_count") == 1
                and row.get("exact_submission") is True
                and row.get("releases_verified") is True
                and len(task_rows) == 1
                and task_rows[0].get("exact") is True
                and task_rows[0].get("submitted_values") == [task["token"]]
                and len(records) == 1
            ) else "FAIL_TASK1_SCOPED",
            "task_id": task["task_id"],
            "exact_submission_count": len(task_rows),
            "total_fixture_submission_count": len(records),
            "full_six_task_fixture_success": full_fixture.get("success"),
            "model_call_count": len(row.get("model_calls", [])),
            "model_visible_images": row.get("model_visible_images"),
            "runtime_releases_verified": row.get("releases_verified"),
            "authority_granted": False,
        }
        dump(OUT / "task1-scope-result.json", scoped)
        return 0 if scoped["status"] == "PASS_TASK1_SCOPED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
