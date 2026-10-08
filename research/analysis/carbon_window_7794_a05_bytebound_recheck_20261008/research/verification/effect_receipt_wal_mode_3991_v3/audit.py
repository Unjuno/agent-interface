"""Independent raw/evidence-only audit; imports no runner code."""
import copy
import hashlib
import json
import sqlite3
import sys
from pathlib import Path, PurePosixPath

ALLOCATION = "effect-receipt-wal-vs-delete-3991-20260928-03"
MODES = ("DELETE", "WAL")
PROTOCOLS = ("EFFECT_FIRST", "RECEIPT_FIRST", "ATOMIC_LOCAL", "ATOMIC_EXTERNAL")
CUTS = ("BEFORE", "AFTER_FIRST", "AFTER_SECOND", "AFTER_COMMIT", "NORMAL")
INVALIDS = ("ALTERED_CONTENT", "WRONG_SESSION", "WRONG_RESOURCE", "WRONG_EPOCH", "BOOL_DELTA")
REPEATS = {"formal": 3, "construction": 1}
IMAGE = "sha256:4c2cf9917bd1cbacc5e9b07320025bdb7cdf2df7b0ceaccb55e9dd7e30987419"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def unique_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate_json_key:" + key)
        result[key] = value
    return result


def expected_initial(protocol, cut):
    if cut in ("BEFORE",):
        return {"effect_total": 0, "effect_rows": 0, "receipt_rows": 0}, "NOT_FOUND"
    if cut == "AFTER_FIRST":
        if protocol in ("EFFECT_FIRST", "ATOMIC_EXTERNAL"):
            return {"effect_total": 1, "effect_rows": 1, "receipt_rows": 0}, "NOT_FOUND"
        if protocol == "RECEIPT_FIRST":
            return {"effect_total": 0, "effect_rows": 0, "receipt_rows": 1}, "COMPLETED"
        return {"effect_total": 0, "effect_rows": 0, "receipt_rows": 0}, "NOT_FOUND"
    if cut == "AFTER_SECOND" and protocol == "ATOMIC_LOCAL":
        return {"effect_total": 0, "effect_rows": 0, "receipt_rows": 0}, "NOT_FOUND"
    return {"effect_total": 1, "effect_rows": 1, "receipt_rows": 1}, "COMPLETED"


def expected_final(protocol, cut):
    initial, status = expected_initial(protocol, cut)
    if status != "NOT_FOUND":
        return initial, 0, status
    extra = 1
    if (protocol in ("EFFECT_FIRST", "ATOMIC_EXTERNAL")
            and initial["effect_rows"] == 1):
        extra = 2
    return {"effect_total": extra, "effect_rows": extra, "receipt_rows": 1}, 1, "COMPLETED"


def safe_file(evidence, relative):
    rel = PurePosixPath(relative)
    if rel.is_absolute() or ".." in rel.parts:
        raise ValueError("unsafe_artifact_path")
    path = evidence.joinpath(*rel.parts).resolve()
    if not path.is_relative_to(evidence.resolve()) or not path.is_file():
        raise ValueError("artifact_missing_or_outside")
    return path


def verify_snapshots(evidence, row, errors):
    for stage in ("pre_recovery", "post_recovery", "final"):
        inventory = row.get("snapshot_" + stage, {})
        for relative, binding in inventory.items():
            try:
                data = safe_file(evidence, relative).read_bytes()
                if len(data) != binding.get("bytes") or sha(data) != binding.get("sha256"):
                    errors.append(row.get("case_id", "?") + ":snapshot_hash:" + stage)
            except (OSError, ValueError):
                errors.append(row.get("case_id", "?") + ":snapshot_path:" + stage)


def verify_processes(row, errors):
    processes = row.get("processes", [])
    expected_count = 1 if row.get("invalid") else None
    if row.get("kind") and row.get("cut") is None:
        expected_count = 1
    for ix, event in enumerate(processes):
        prefix = row.get("case_id", "?") + f":process{ix}"
        stdout = event.get("stdout", "").encode()
        stderr = event.get("stderr", "").encode()
        if event.get("pid", 0) <= 0 or event.get("elapsed_ns", 0) < 0:
            errors.append(prefix + ":process_identity")
        if sha(stdout) != event.get("stdout_sha256") or sha(stderr) != event.get("stderr_sha256"):
            errors.append(prefix + ":log_hash")
        if ix > 0 and event.get("exit_code") != 0:
            errors.append(prefix + ":child_exit")
    if expected_count == 1 and len(processes) != 1:
        errors.append(row.get("case_id", "?") + ":invalid_process_count")
    if expected_count is None and len(processes) not in (4, 5):
        errors.append(row.get("case_id", "?") + ":process_count")
    if processes and row.get("cut") is not None:
        expected_exit = 0 if row["cut"] == "NORMAL" else 73
        if processes[0].get("exit_code") != expected_exit:
            errors.append(row["case_id"] + ":actor_exit")
        if row["cut"] != "BEFORE" and processes:
            try:
                actor = json.loads(processes[0].get("stdout", "").splitlines()[0])
                settings = actor["actor_settings"]
                for entry in settings.values():
                    if entry.get("journal_mode") != row.get("mode") or entry.get("synchronous") != 2:
                        errors.append(row["case_id"] + ":actor_journal_settings")
                    if row.get("mode") == "WAL" and entry.get("wal_autocheckpoint") != 0:
                        errors.append(row["case_id"] + ":actor_checkpoint_setting")
            except (ValueError, IndexError, KeyError, TypeError):
                errors.append(row["case_id"] + ":actor_settings_missing")


def verify_source_and_invocation(source, evidence, kind):
    errors = []
    try:
        manifest_bytes = (source / "SOURCE_MANIFEST.json").read_bytes()
        manifest = json.loads(manifest_bytes)
        if manifest.get("allocation") != ALLOCATION or manifest.get("docker_image_id") != IMAGE:
            errors.append("source_manifest_identity")
        for name, expected in manifest.get("source_sha256", {}).items():
            if sha((source / name).read_bytes()) != expected:
                errors.append("source_hash:" + name)
        freeze = (source / "FREEZE.json").read_bytes()
        if sha(freeze) != manifest.get("freeze_sha256"):
            errors.append("freeze_hash")
    except (OSError, ValueError, KeyError, TypeError):
        return ["source_manifest_missing_or_invalid"]
    try:
        environment = json.loads((evidence / "ENVIRONMENT.json").read_text(encoding="utf-8"))
        if (environment.get("allocation") != ALLOCATION or environment.get("image_id") != IMAGE
                or environment.get("kind") != kind
                or environment.get("source_manifest_sha256") != sha(manifest_bytes)):
            errors.append("environment_binding")
        if environment.get("sqlite") != "3.40.1" or environment.get("python") is None:
            errors.append("environment_runtime")
    except (OSError, ValueError):
        errors.append("environment_missing_or_invalid")
    try:
        inv_bytes = (evidence / "INVOCATION.json").read_bytes()
        invocation = json.loads(inv_bytes)
        stdout = (evidence / "DOCKER.stdout.bin").read_bytes()
        stderr = (evidence / "DOCKER.stderr.bin").read_bytes()
        argv = invocation.get("command_argv", [])
        required = ("run", "--rm", "--pull=never", "--platform=linux/amd64", "--network=none",
                    "--read-only", "--cpus=1", "--memory=1g", "--pids-limit=32", IMAGE)
        if any(item not in argv for item in required):
            errors.append("docker_argv")
        expected_stage = kind if kind in ("formal", "construction") else "audit-" + kind
        if invocation.get("stage") != expected_stage or invocation.get("image_id") != IMAGE:
            errors.append("invocation_identity")
        if (invocation.get("exit_code") != 0 or invocation.get("pid", 0) <= 0
                or invocation.get("stdout_bytes") != len(stdout)
                or invocation.get("stdout_sha256") != sha(stdout)
                or invocation.get("stderr_bytes") != len(stderr)
                or invocation.get("stderr_sha256") != sha(stderr)):
            errors.append("invocation_receipt")
    except (OSError, ValueError, TypeError):
        errors.append("invocation_missing_or_invalid")
    return errors


def read_final_database_state(evidence, row):
    case = evidence / "cases" / row["case_id"]
    effect_path = case / "effect.sqlite"
    receipt_path = case / ("receipt.sqlite" if row["protocol"] == "ATOMIC_EXTERNAL" else "effect.sqlite")
    op = "op-" + row["case_id"]
    econn = sqlite3.connect(effect_path.resolve().as_uri() + "?mode=ro", uri=True)
    effects = econn.execute("SELECT COALESCE(SUM(delta),0),COUNT(*) FROM effects WHERE operation_id=?", (op,)).fetchone()
    econn.close()
    rconn = sqlite3.connect(receipt_path.resolve().as_uri() + "?mode=ro", uri=True)
    receipts = rconn.execute("SELECT COUNT(*) FROM receipts WHERE operation_id=?", (op,)).fetchone()[0]
    rconn.close()
    return {"effect_total": effects[0], "effect_rows": effects[1], "receipt_rows": receipts}


def validate_row(evidence, row):
    errors = []
    case_id = row.get("case_id", "?")
    if row.get("allocation") != ALLOCATION:
        errors.append(case_id + ":allocation")
    if row.get("mode") not in MODES:
        errors.append(case_id + ":mode")
    if row.get("protocol") not in PROTOCOLS:
        errors.append(case_id + ":protocol")
    mode = row.get("mode")
    protocol = row.get("protocol")
    for info in row.get("journal_settings", {}).values():
        if info.get("journal_mode") != mode or info.get("synchronous") != 2:
            errors.append(case_id + ":journal_settings")
        if mode == "WAL" and info.get("wal_autocheckpoint") != 0:
            errors.append(case_id + ":wal_autocheckpoint")

    verify_processes(row, errors)
    verify_snapshots(evidence, row, errors)
    required_snapshots = ("snapshot_final",) if row.get("cut") is None else (
        "snapshot_pre_recovery", "snapshot_post_recovery", "snapshot_final")
    if any(not row.get(name) for name in required_snapshots):
        errors.append(case_id + ":snapshot_inventory_missing")

    if row.get("cut") is None:
        if row.get("invalid_control") not in INVALIDS:
            errors.append(case_id + ":invalid_control")
        if row.get("invalid_result", {}).get("decision") != "REFUSED":
            errors.append(case_id + ":invalid_accepted")
        if row.get("extra_effect_rows") != 0:
            errors.append(case_id + ":invalid_extra_effect")
        if row.get("before_invalid") != row.get("after_invalid"):
            errors.append(case_id + ":invalid_state_changed")
        if row.get("before_invalid") != {"effect_total": 1, "effect_rows": 1, "receipt_rows": 1}:
            errors.append(case_id + ":invalid_baseline")
        expected_final_state = row.get("before_invalid")
    else:
        cut = row.get("cut")
        if cut not in CUTS:
            errors.append(case_id + ":cut")
            return errors
        initial, status = expected_initial(protocol, cut)
        final, retry_count, final_status = expected_final(protocol, cut)
        query = row.get("status", {})
        activity = query.get("query_activity", {})
        if (query.get("status") != status or query.get("query_only") is not True
                or query.get("readonly_uri") is not True
                or set(activity.get("read_tables", [])) - {"receipts", "sqlite_master", "sqlite_schema"}
                or activity.get("denied_reads") or activity.get("denied_writes")):
            errors.append(case_id + ":receipt_query_contract")
        if row.get("before_query") != initial or row.get("after_query") != initial:
            errors.append(case_id + ":pre_retry_state")
        if row.get("query_state_unchanged") is not True:
            errors.append(case_id + ":query_mutation")
        if row.get("retry_count") != retry_count:
            errors.append(case_id + ":retry_count")
        if row.get("final_status", {}).get("status") != final_status:
            errors.append(case_id + ":final_status")
        if row.get("final") != final:
            errors.append(case_id + ":final_state")
        expected_final_state = final
        if "mode_mismatch" in row:
            errors.append(case_id + ":mode_mismatch")

    try:
        independent = read_final_database_state(evidence, row)
        if independent != expected_final_state:
            errors.append(case_id + ":independent_database_state")
    except (OSError, sqlite3.Error, KeyError, ValueError) as exc:
        errors.append(case_id + ":independent_database_read:" + type(exc).__name__)
    return errors


def expected_case_ids(kind):
    repeats = REPEATS[kind]
    ids = []
    for mode in MODES:
        for protocol in PROTOCOLS:
            for cut in CUTS:
                for repeat in range(1, repeats + 1):
                    ids.append(f"{kind}-{mode}-{protocol}-{cut}-r{repeat}")
        for control in INVALIDS:
            for repeat in range(1, repeats + 1):
                ids.append(f"{kind}-{mode}-ATOMIC_LOCAL-{control}-r{repeat}")
    return ids


def audit_records(evidence, rows, kind):
    errors = []
    expected = expected_case_ids(kind)
    actual = [row.get("case_id") for row in rows]
    if len(rows) != len(expected) or actual != expected:
        errors.append("case_denominator_or_order")
    if len(actual) != len(set(actual)):
        errors.append("duplicate_case_id")
    for row in rows:
        errors.extend(validate_row(evidence, row))
    return errors


def corruption_controls(evidence, rows, kind):
    controls = []
    first = copy.deepcopy(rows[0])
    controls.append(("missing_row", rows[1:]))
    duplicated = copy.deepcopy(rows)
    duplicated[1] = copy.deepcopy(duplicated[0])
    controls.append(("duplicate_row", duplicated))
    changed_mode = copy.deepcopy(rows)
    changed_mode[0]["mode"] = "INVALID"
    controls.append(("mode", changed_mode))
    changed_status = copy.deepcopy(rows)
    changed_status[0]["status"]["status"] = "COMPLETED"
    controls.append(("status", changed_status))
    changed_effect = copy.deepcopy(rows)
    changed_effect[0]["final"]["effect_rows"] += 7
    controls.append(("effect_count", changed_effect))
    changed_retry = copy.deepcopy(rows)
    changed_retry[0]["retry_count"] = 2
    controls.append(("retry_count", changed_retry))
    changed_query = copy.deepcopy(rows)
    changed_query[0]["query_state_unchanged"] = False
    controls.append(("query_mutation", changed_query))
    changed_artifact = copy.deepcopy(rows)
    first_snapshot = next(iter(changed_artifact[0]["snapshot_pre_recovery"].values()))
    first_snapshot["sha256"] = "0" * 64
    controls.append(("snapshot_bytes", changed_artifact))
    rejected = []
    for name, candidate in controls:
        if audit_records(evidence, candidate, kind):
            rejected.append(name)
    return rejected


def main(argv):
    if len(argv) != 3 or argv[2] not in REPEATS:
        raise SystemExit("usage: audit.py EVIDENCE_DIR AUDIT_JSON formal|construction")
    evidence, audit_path, kind = Path(argv[0]), Path(argv[1]), argv[2]
    source = Path(__file__).resolve().parent
    raw_path = evidence / ("formal.jsonl" if kind == "formal" else "construction.jsonl")
    raw_bytes = raw_path.read_bytes()
    rows = [json.loads(line, object_pairs_hook=unique_pairs) for line in raw_bytes.splitlines()]
    errors = verify_source_and_invocation(source, evidence, kind)
    errors.extend(audit_records(evidence, rows, kind))
    controls = corruption_controls(evidence, rows, kind)
    required_controls = {"missing_row", "duplicate_row", "mode", "status",
                         "effect_count", "retry_count", "query_mutation", "snapshot_bytes"}
    if set(controls) != required_controls:
        errors.append("corruption_control_denominator")
    if len(controls) != 8:
        errors.append("formal_corruption_controls")
    result = {"allocation": ALLOCATION, "kind": kind,
              "audit": "PASS_AUDIT" if not errors and len(controls) == 8 else "FAIL_AUDIT",
              "errors": errors, "rows": len(rows), "raw_bytes": len(raw_bytes),
              "raw_sha256": sha(raw_bytes), "corruption_controls": controls,
              "corruption_rejected": len(controls)}
    audit_path.parent.mkdir(parents=True, exist_ok=True)
    audit_path.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"audit": result["audit"], "errors": len(errors),
                      "rows": len(rows), "corruption_rejected": len(controls)}, sort_keys=True))
    raise SystemExit(0 if result["audit"] == "PASS_AUDIT" else 2)


if __name__ == "__main__":
    main(sys.argv[1:])
