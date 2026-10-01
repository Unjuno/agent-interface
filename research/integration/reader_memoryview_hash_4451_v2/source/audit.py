"""Independent raw-only audit; imports neither the reader nor the runner."""

import argparse
import hashlib
import json
import math
import statistics
from pathlib import Path


RECORD_BYTES = 256
SOURCE_ROOT = Path(__file__).resolve().parent
STUDY_ROOT = SOURCE_ROOT.parent


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


def invalid_constant(value):
    raise ValueError("non-finite JSON value: " + value)


def strict_load_line(data):
    return json.loads(data.decode(), object_pairs_hook=unique, parse_constant=invalid_constant)


def expected_read(data, cursor_records, max_records=32):
    offset = cursor_records * RECORD_BYTES
    sequence = cursor_records + 1
    records = []
    tail_state = "end"
    problem = None
    prefix_sha = hashlib.sha256(data[:offset]).hexdigest()
    while offset < len(data) and len(records) < max_records:
        end = data.find(b"\n", offset)
        if end < 0:
            tail_state = "incomplete"
            break
        try:
            record = strict_load_line(data[offset:end])
        except Exception:
            tail_state, problem = "blocked", "INVALID_JSON_RECORD"
            break
        if (
            not isinstance(record, dict)
            or not isinstance(record.get("event"), str)
            or not record["event"]
            or record.get("delivery_id") != "delivery:" + str(sequence)
        ):
            tail_state, problem = "blocked", "INVALID_RECORD_OR_DELIVERY_SEQUENCE"
            break
        records.append(record)
        offset = end + 1
        sequence += 1
    if len(records) == max_records and offset < len(data):
        tail_state = "limit"
    return {
        "schema": "agent-interface/experimental-inbox-read-v1",
        "records": records,
        "tail_state": tail_state,
        "problem": problem,
        "next_cursor": {
            "schema": "agent-interface/experimental-read-cursor-v1",
            "stream_id": "formal-stream",
            "offset": offset,
            "prefix_sha256": hashlib.sha256(data[:offset]).hexdigest(),
            "next_sequence": sequence,
        },
        "authority": "none",
        "acknowledged": False,
        "input_dispatched": False,
    }


def _check_source_and_environment(raw, errors):
    freeze_path = STUDY_ROOT / "FREEZE.json"
    environment_path = STUDY_ROOT / "ENVIRONMENT.json"
    freeze = json.loads(freeze_path.read_text(encoding="utf-8"))
    checks = 0
    checks += 1
    if raw.get("freeze_sha256") != sha(freeze_path):
        errors.append("freeze_sha256")
    checks += 1
    if freeze.get("environment_sha256") != sha(environment_path):
        errors.append("environment_sha256")
    environment = raw.get("environment", {})
    checks += 1
    if environment.get("image_id") != freeze.get("container_image_id"):
        errors.append("environment_image_id")
    checks += 1
    if environment.get("python_version") != "3.13.5":
        errors.append("python_version")

    actual = {name: sha(SOURCE_ROOT / name) for name in freeze["source_sha256"]}
    checks += len(actual)
    if actual != freeze["source_sha256"]:
        errors.append("frozen_source_hashes")
    if raw.get("source_sha256") != actual:
        errors.append("raw_source_hashes")
    return checks, actual


def _check_journal(raw, root, errors):
    checks = 0
    journal_path = root / "PROGRESS.jsonl"
    checks += 1
    if not journal_path.exists() or sha(journal_path) != raw.get("journal_sha256"):
        errors.append("journal_sha256")
        return checks, []
    events = [json.loads(line) for line in journal_path.read_text(encoding="utf-8").splitlines() if line]
    checks += 1
    if events != raw.get("journal"):
        errors.append("journal_content")
    starts = {event.get("worker_id"): event for event in events if event.get("event") == "worker_start"}
    completed = {event.get("worker_id"): event for event in events if event.get("event") == "worker_complete"}
    rows = raw.get("resource", []) + raw.get("contracts", [])
    checks += 1
    if len(completed) != len(rows):
        errors.append("journal_completion_count")
    for row in rows:
        checks += 3
        start = starts.get(row.get("worker_id"))
        complete = completed.get(row.get("worker_id"))
        if start is None or complete is None:
            errors.append("journal_worker_pair:" + str(row.get("worker_id")))
            continue
        if start.get("pid") != row.get("pid") or start.get("argv") != row.get("argv"):
            errors.append("journal_worker_start:" + row["worker_id"])
        if any(complete.get(key) != row.get(key) for key in ("exit", "stdout", "stderr", "stdout_sha256", "stderr_sha256")):
            errors.append("journal_worker_complete:" + row["worker_id"])
        for stream in ("stdout", "stderr"):
            log_path = root / ("worker-" + row["worker_id"] + "." + stream)
            if not log_path.exists() or sha(log_path) != row.get(stream + "_sha256"):
                errors.append("worker_log:" + row["worker_id"] + ":" + stream)
    return checks, events


def audit(raw_path):
    raw_path = Path(raw_path)
    root = raw_path.parent
    raw = json.loads(raw_path.read_text(encoding="utf-8"))
    errors = []
    checks, actual_sources = _check_source_and_environment(raw, errors)

    corpus_path = root / "corpus.jsonl"
    data = corpus_path.read_bytes()
    checks += 1
    if hashlib.sha256(data).hexdigest() != raw.get("corpus_sha256"):
        errors.append("corpus_sha256")
    run_path = root / "RUN.json"
    checks += 1
    if not run_path.exists():
        errors.append("run_manifest_missing")
    else:
        run = json.loads(run_path.read_text(encoding="utf-8"))
        for key in ("phase", "records", "corpus_bytes", "corpus_sha256", "freeze_sha256", "source_sha256", "environment"):
            checks += 1
            if raw.get(key) != run.get(key):
                errors.append("run_manifest:" + key)

    expected_resources = 6 if raw.get("phase") == "construction" else 24
    checks += 1
    if len(raw.get("resource", [])) != expected_resources:
        errors.append("resource_count")
    checks += 1
    if len(raw.get("contracts", [])) != 2:
        errors.append("contract_count")
    checks += 1
    if raw.get("stop_reason") is not None:
        errors.append("unexpected_stop_reason")

    groups = {}
    for index, record in enumerate(raw.get("resource", [])):
        checks += 7
        if record.get("status") != "complete" or record.get("exit") != 0 or record.get("stderr") != "":
            errors.append("resource_process:" + str(index))
        try:
            row = json.loads(record["stdout"])
        except Exception:
            errors.append("resource_json:" + str(index))
            continue
        if row.get("arm") != record.get("arm") or row.get("cursor_records") != record.get("cursor_records"):
            errors.append("resource_identity:" + str(index))
        expected_source = actual_sources.get("baseline_reader.py" if record.get("arm") == "BASELINE" else "candidate_reader.py")
        if row.get("source_sha256") != expected_source:
            errors.append("resource_source:" + str(index))
        if row.get("input_sha256_before") != raw.get("corpus_sha256") or row.get("input_sha256_after") != raw.get("corpus_sha256"):
            errors.append("resource_input:" + str(index))
        if row.get("error") is not None or row.get("result") != expected_read(data, record["cursor_records"]):
            errors.append("resource_result:" + str(index))
        if row.get("pid") != record.get("pid"):
            errors.append("resource_pid:" + str(index))
        groups[(record["cursor_records"], record["rep"], record["arm"])] = row

    cursor_set = {record.get("cursor_records") for record in raw.get("resource", [])}
    for cursor in sorted(cursor_set):
        if raw.get("phase") == "formal":
            for repetition in range(3):
                checks += 2
                pair = (cursor, repetition, "BASELINE")
                candidate = (cursor, repetition, "MEMORYVIEW")
                if pair not in groups or candidate not in groups:
                    errors.append("matched_pair_missing:" + str(cursor) + ":" + str(repetition))
                elif groups[pair]["result"] != groups[candidate]["result"]:
                    errors.append("pair_result:" + str(cursor) + ":" + str(repetition))

    metrics = {}
    if raw.get("phase") == "formal" and all((cursor, repetition, arm) in groups for cursor in (0, 2048, 4064, 4096) for repetition in range(3) for arm in ("BASELINE", "MEMORYVIEW")):
        for cursor in (0, 2048, 4064, 4096):
            ratios = []
            wall = []
            cpu = []
            for repetition in range(3):
                base = groups[(cursor, repetition, "BASELINE")]
                candidate = groups[(cursor, repetition, "MEMORYVIEW")]
                ratios.append(candidate["traced_peak_bytes"] / base["traced_peak_bytes"])
                wall.append(candidate["wall_ns"] / base["wall_ns"])
                cpu.append(candidate["cpu_ns"] / base["cpu_ns"])
            metrics[str(cursor)] = {
                "peak_ratio_median": statistics.median(ratios),
                "peak_ratios": ratios,
                "wall_ratio_median": statistics.median(wall),
                "cpu_ratio_median": statistics.median(cpu),
                "baseline_peak": [groups[(cursor, rep, "BASELINE")]["traced_peak_bytes"] for rep in range(3)],
                "candidate_peak": [groups[(cursor, rep, "MEMORYVIEW")]["traced_peak_bytes"] for rep in range(3)],
            }
        for cursor in (2048, 4064):
            metric = metrics[str(cursor)]
            checks += 4
            if not all(candidate < baseline for candidate, baseline in zip(metric["candidate_peak"], metric["baseline_peak"])):
                errors.append("peak_not_lower:" + str(cursor))
            if metric["peak_ratio_median"] > 0.75:
                errors.append("peak_ratio:" + str(cursor))
            if metric["wall_ratio_median"] > 1.20:
                errors.append("wall_guard:" + str(cursor))
            if metric["cpu_ratio_median"] > 1.20:
                errors.append("cpu_guard:" + str(cursor))

    contract_results = []
    for index, record in enumerate(raw.get("contracts", [])):
        checks += 4
        if record.get("status") != "complete" or record.get("exit") != 0 or record.get("stderr") != "":
            errors.append("contract_process:" + str(index))
        try:
            result = json.loads(record["stdout"])
            contract_results.append(result)
        except Exception:
            errors.append("contract_json:" + str(index))
            continue
        if result.get("arm") != record.get("arm"):
            errors.append("contract_identity:" + str(index))
        if sha(root / ("worker-" + record["worker_id"] + ".stdout")) != record.get("stdout_sha256"):
            errors.append("contract_stdout_hash:" + str(index))
        if sha(root / ("worker-" + record["worker_id"] + ".stderr")) != record.get("stderr_sha256"):
            errors.append("contract_stderr_hash:" + str(index))
    if len(contract_results) == 2:
        checks += 8
        if contract_results[0].get("rows") != contract_results[1].get("rows"):
            errors.append("contract_parity")
        by_name = dict(contract_results[0].get("rows", []))
        required = {
            "incomplete": ("result", "incomplete"),
            "bad_json": ("result", "blocked"),
            "gap": ("result", "blocked"),
            "duplicate_key": ("result", "blocked"),
            "changed_prefix": ("error", "CURSOR_PREFIX_CHANGED"),
            "wrong_stream": ("error", "INVALID_CURSOR"),
            "bound": ("error", "STREAM_READ_BOUND_EXCEEDED"),
        }
        for name, (kind, value) in required.items():
            checks += 1
            got = by_name.get(name, {})
            if got.get("kind") != kind:
                errors.append("contract_kind:" + name)
            elif kind == "result" and got.get("value", {}).get("tail_state") != value:
                errors.append("contract_tail:" + name)
            elif kind == "error" and got.get("message") != value:
                errors.append("contract_error:" + name)

    checks_journal, _ = _check_journal(raw, root, errors)
    checks += checks_journal
    supervisor_path = root.parent / (root.name + ".SUPERVISOR.json")
    checks += 1
    if not supervisor_path.exists():
        errors.append("supervisor_manifest_missing")
    else:
        supervisor = json.loads(supervisor_path.read_text(encoding="utf-8"))
        if supervisor.get("return_code") != 0 or supervisor.get("image_id") != raw.get("environment", {}).get("image_id"):
            errors.append("supervisor_manifest")

    decision = "FAIL"
    if not errors:
        decision = "PASS_CONSTRUCTION" if raw.get("phase") == "construction" else "PASS_READER_MEMORYVIEW_HASH_SCOPED"
    return {"schema": "reader-memoryview-audit-v2", "checks": checks, "errors": errors, "metrics": metrics, "decision": decision}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("raw")
    args = parser.parse_args()
    report = audit(args.raw)
    print(json.dumps(report, sort_keys=True, indent=2))
    raise SystemExit(0 if not report["errors"] else 1)
