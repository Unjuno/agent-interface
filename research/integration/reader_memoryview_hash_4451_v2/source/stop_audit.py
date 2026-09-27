"""Audit a supervisor-generated partial STOP without importing its runner."""

import argparse
import json
from pathlib import Path

from common import sha256_path


SOURCE_ROOT = Path(__file__).resolve().parent
STUDY_ROOT = SOURCE_ROOT.parent


def audit(stop_path):
    stop_path = Path(stop_path)
    root = stop_path.parent
    errors = []
    checks = 0
    stop = json.loads(stop_path.read_text(encoding="utf-8"))
    partial_path = root / "RAW_PARTIAL.json"
    partial = json.loads(partial_path.read_text(encoding="utf-8"))
    journal_path = root / "PROGRESS.jsonl"
    events = [json.loads(line) for line in journal_path.read_text(encoding="utf-8").splitlines() if line]
    freeze_path = STUDY_ROOT / "FREEZE.json"
    environment_path = STUDY_ROOT / "ENVIRONMENT.json"
    freeze = json.loads(freeze_path.read_text(encoding="utf-8"))

    checks += 4
    if stop.get("reason") != "STOP_SUPERVISOR_TIMEOUT":
        errors.append("stop_reason")
    if stop.get("partial_sha256") != sha256_path(partial_path):
        errors.append("partial_sha256")
    if stop.get("journal_sha256") != sha256_path(journal_path) or partial.get("journal_sha256") != sha256_path(journal_path):
        errors.append("journal_sha256")
    if partial.get("journal") != events:
        errors.append("journal_content")

    run_path = root / "RUN.json"
    run = json.loads(run_path.read_text(encoding="utf-8"))
    checks += 4
    if partial.get("corpus_sha256") != stop.get("corpus_sha256"):
        errors.append("corpus_identity")
    if partial.get("freeze_sha256") != sha256_path(freeze_path) or stop.get("freeze_sha256") != sha256_path(freeze_path):
        errors.append("freeze_identity")
    if partial.get("source_sha256") != freeze.get("source_sha256"):
        errors.append("source_manifest")
    if freeze.get("environment_sha256") != sha256_path(environment_path):
        errors.append("environment_sha256")

    corpus_path = root / "corpus.jsonl"
    checks += 2
    if not corpus_path.exists() or sha256_path(corpus_path) != stop.get("corpus_sha256"):
        errors.append("corpus_bytes")
    if run.get("corpus_sha256") != stop.get("corpus_sha256"):
        errors.append("run_corpus")

    intents = {event.get("worker_id"): event for event in events if event.get("event") == "worker_intent"}
    starts = {event.get("worker_id"): event for event in events if event.get("event") == "worker_start"}
    completed = {event.get("worker_id"): event for event in events if event.get("event") == "worker_complete"}
    checks += 4
    if len(intents) != stop.get("intended_workers"):
        errors.append("intent_count")
    if len(starts) != stop.get("started_workers"):
        errors.append("start_count")
    if len([item for item in completed.values() if item.get("kind") == "resource"]) != stop.get("completed_resource_workers"):
        errors.append("completed_resource_count")
    if len([item for item in completed.values() if item.get("kind") == "contract"]) != stop.get("completed_contract_workers"):
        errors.append("completed_contract_count")

    for worker_id, start in starts.items():
        checks += 2
        intent = intents.get(worker_id)
        if intent is None or intent.get("argv") != start.get("argv") or intent.get("identity") != start.get("identity"):
            errors.append("worker_intent:" + str(worker_id))
        for stream in ("stdout", "stderr"):
            name = start.get(stream + "_path", "")
            log = root / name
            if Path(name).name != name or not log.exists():
                errors.append("worker_log_path:" + str(worker_id) + ":" + stream)

    for worker_id, complete in completed.items():
        checks += 2
        if worker_id not in starts:
            errors.append("completion_without_start:" + str(worker_id))
        elif complete.get("pid") != starts[worker_id].get("pid") or complete.get("argv") != starts[worker_id].get("argv"):
            errors.append("completion_identity:" + str(worker_id))

    decision = "PASS_STOP_EVIDENCE_RETAINED" if not errors else "FAIL_STOP_EVIDENCE_AUDIT"
    return {"schema": "reader-memoryview-stop-audit-v1", "checks": checks, "errors": errors, "decision": decision}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("stop")
    args = parser.parse_args()
    report = audit(args.stop)
    print(json.dumps(report, sort_keys=True, indent=2))
    raise SystemExit(0 if not report["errors"] else 1)
