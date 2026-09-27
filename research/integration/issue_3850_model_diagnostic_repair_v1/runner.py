from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import uuid


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    base = Path(__file__).resolve().parent
    cases_path = base / "cases.json"
    schema_path = base / "response.schema.json"
    template_path = base / "prompt_template.txt"
    cases_doc = json.loads(cases_path.read_text(encoding="utf-8"))
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    template = template_path.read_text(encoding="utf-8")
    by_id = {case["id"]: case for case in cases_doc["cases"]}
    results = Path(os.environ["RESULTS_DIR"])
    ipc = Path(os.environ["HOST_MODEL_IPC_DIR"])
    results.mkdir(parents=True, exist_ok=False)
    rows = []
    for ordinal, allocation in enumerate(cases_doc["order"], 1):
        case = by_id[allocation["case"]]
        row_id = f"{ordinal:02d}-{case['id']}-r{allocation['rep']}-{allocation['arm'].lower()}"
        row = results / row_id
        row.mkdir()
        refusal = dict(cases_doc["refusal"])
        if allocation["arm"] == "BOUNDED_DETAIL":
            refusal.update(detail=case["diagnostic"],
                           detail_source=cases_doc["detail_source"],
                           validation_operation_index=cases_doc["validation_operation_index"])
        prompt = template.replace("{task}", case["task"])
        prompt = prompt.replace("{program_json}", json.dumps(case["program"], separators=(",", ":")))
        prompt = prompt.replace("{refusal_json}", json.dumps(refusal, separators=(",", ":")))
        request_id = uuid.uuid4().hex
        request = {
            "request_id": request_id,
            "allocation_id": row_id,
            "prompt": prompt,
            "working": "/repo",
            "schema": "/repo/response.schema.json",
            "schema_sha256": digest(schema_path),
            "mode": "one_turn_json_schema",
            "authority_granted": False,
        }
        (row / "allocation.json").write_text(json.dumps({
            "ordinal": ordinal, "case": case["id"], "rep": allocation["rep"],
            "arm": allocation["arm"], "program": case["program"],
            "expected_repair": case["expected_repair"], "refusal": refusal,
            "request_id": request_id, "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(),
            "schema_sha256": request["schema_sha256"],
            "authority_granted": False,
        }, indent=2) + "\n", encoding="utf-8")
        (row / "prompt.txt").write_text(prompt, encoding="utf-8")
        request_path = ipc / f"{request_id}.request.json"
        response_path = ipc / f"{request_id}.response.jsonl"
        broker_path = ipc / f"{request_id}.broker.json"
        started = time.monotonic()
        request_path.write_text(json.dumps(request) + "\n", encoding="utf-8")
        deadline = started + 150
        while not (response_path.exists() and broker_path.exists()):
            if time.monotonic() >= deadline:
                (row / "stop.json").write_text(json.dumps({
                    "status": "STOP_IPC_TIMEOUT", "request_id": request_id,
                    "attempts": 1, "authority_granted": False,
                }, indent=2) + "\n", encoding="utf-8")
                return 1
            time.sleep(.05)
        shutil.copyfile(response_path, row / "events.jsonl")
        broker = json.loads(broker_path.read_text(encoding="utf-8"))
        (row / "broker.json").write_text(json.dumps(broker, indent=2) + "\n", encoding="utf-8")
        rows.append({"ordinal": ordinal, "request_id": request_id, "allocation_id": row_id,
                     "runner_observed_seconds": time.monotonic() - started,
                     "broker_returncode": broker.get("returncode")})
        if broker.get("returncode") != 0 or not response_path.stat().st_size:
            (row / "stop.json").write_text(json.dumps({
                "status": "STOP_CALL_OR_EMPTY_RESPONSE", "request_id": request_id,
                "attempts": 1, "authority_granted": False,
            }, indent=2) + "\n", encoding="utf-8")
            return 1
    (results / "runner-manifest.json").write_text(json.dumps({
        "status": "ALL_ROWS_RETURNED", "rows": rows, "calls": len(rows),
        "retries": 0, "authority_granted": False,
        "cases_sha256": digest(cases_path), "prompt_template_sha256": digest(template_path),
        "schema_sha256": digest(schema_path),
    }, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
