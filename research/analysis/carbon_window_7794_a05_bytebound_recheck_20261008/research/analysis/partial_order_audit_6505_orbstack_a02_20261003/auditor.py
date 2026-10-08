#!/usr/bin/env python3
"""Fresh audit-only reconstruction for Issue #6505; never runs predecessor code."""
from __future__ import annotations

import base64
import hashlib
import io
import itertools
import json
import os
import platform
import sys
import zipfile
from collections import deque
from pathlib import Path


PREDECESSOR = "research/analysis/partial_order_replay_4889_v1"
FROZEN_EVENTS = ("OBS0", "OBS1", "PLAN0", "PLAN1", "TOOL0", "TOOL1", "OPEN", "CLOSE", "TICK", "REQUEST")
FIELDS = ("observation", "observation_revision", "plan", "plan_revision", "tool_result",
          "authority_open", "authority_generation", "logical_time", "lease_expiry")
ORIGIN = (-1, 0, -1, -1, -1, 0, 0, 0, 0)
WORDS = 11111
RAW_BYTES = 3241590
RAW_SHA256 = "a25bc4a9e6cf845fb5b446b1d2d5071bd26909679efcc535372fdf77b58b4eb8"
ARCHIVE_BYTES = 104640
ARCHIVE_SHA256 = "a127e04d2fcce672f3ce5cc6f20d2af0e1f85b34ac16116e9e5a518e7c358f6b"


class AuditFailure(Exception):
    pass


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def git_blob_id(data: bytes) -> str:
    header = b"blob " + str(len(data)).encode("ascii") + b"\0"
    return hashlib.sha1(header + data).hexdigest()


def unpack(state: tuple[int, ...]) -> dict[str, int]:
    return dict(zip(FIELDS, state, strict=True))


def repack(state: dict[str, int]) -> tuple[int, ...]:
    return tuple(state[name] for name in FIELDS)


def transition(snapshot: tuple[int, ...], operation: str) -> tuple[tuple[int, ...], str]:
    """Apply one declared event using a named-field representation independent of #4889 code."""
    s = unpack(snapshot)
    response = "APPLIED"
    if operation in ("OBS0", "OBS1"):
        s["observation"] = int(operation[-1])
        s["observation_revision"] = min(2, s["observation_revision"] + 1)
    elif operation in ("PLAN0", "PLAN1"):
        s["plan"] = int(operation[-1])
        s["plan_revision"] = s["observation_revision"]
        response = "BOUND_WITHOUT_OBSERVATION" if s["observation"] < 0 else "BOUND_CURRENT"
    elif operation in ("TOOL0", "TOOL1"):
        s["tool_result"] = int(operation[-1])
    elif operation == "OPEN":
        s["authority_open"] = 1
        s["authority_generation"] = min(2, s["authority_generation"] + 1)
        s["lease_expiry"] = min(2, s["logical_time"] + 1)
        response = "OPENED"
    elif operation == "CLOSE":
        s["authority_open"] = 0
        s["authority_generation"] = min(2, s["authority_generation"] + 1)
        s["lease_expiry"] = s["logical_time"]
        response = "CLOSED"
    elif operation == "TICK":
        s["logical_time"] = min(2, s["logical_time"] + 1)
        response = "TICKED"
    elif operation == "REQUEST":
        if s["authority_open"] == 0:
            response = "REFUSED_CLOSED"
        elif s["logical_time"] >= s["lease_expiry"]:
            response = "REFUSED_EXPIRED"
        elif (s["plan"] < 0 or s["plan_revision"] != s["observation_revision"]
              or s["plan"] != s["observation"]):
            response = "REFUSED_STALE_OR_MISSING_PLAN"
        elif s["tool_result"] != 1:
            response = "REFUSED_TOOL_RESULT"
        else:
            response = "ADMITTED"
    else:
        raise AuditFailure(f"unknown frozen operation: {operation}")
    return repack(s), response


def enumerate_reachable() -> tuple[tuple[int, ...], ...]:
    seen = {ORIGIN}
    queue = deque([ORIGIN])
    while queue:
        current = queue.popleft()
        for operation in FROZEN_EVENTS:
            target, _ = transition(current, operation)
            if target not in seen:
                seen.add(target)
                queue.append(target)
    return tuple(sorted(seen))


def pair_is_independent(left: str, right: str, universe: tuple[tuple[int, ...], ...]) -> bool:
    for start in universe:
        after_left, out_left_first = transition(start, left)
        left_then_right, out_right_second = transition(after_left, right)
        after_right, out_right_first = transition(start, right)
        right_then_left, out_left_second = transition(after_right, left)
        if left_then_right != right_then_left:
            return False
        if out_left_first != out_left_second or out_right_second != out_right_first:
            return False
    return True


def execute(events: tuple[str, ...], order: tuple[int, ...]) -> tuple[tuple[int, ...], dict[str, str]]:
    current = ORIGIN
    receipts: dict[str, str] = {}
    for occurrence in order:
        current, answer = transition(current, events[occurrence])
        receipts[str(occurrence)] = answer
    return current, receipts


def all_linearizations(size: int, precedes: list[tuple[int, int]]) -> list[tuple[int, ...]]:
    before = [set() for _ in range(size)]
    for earlier, later in precedes:
        before[later].add(earlier)
    output: list[tuple[int, ...]] = []

    def grow(done: tuple[int, ...]) -> None:
        if len(done) == size:
            output.append(done)
            return
        used = set(done)
        for candidate in range(size):
            if candidate not in used and before[candidate] <= used:
                grow(done + (candidate,))

    grow(())
    return output


def expected_record(events: tuple[str, ...], relation: dict[str, dict[str, bool]]) -> dict:
    required = [(i, j) for i in range(len(events)) for j in range(i + 1, len(events))
                if not relation[events[i]][events[j]]]
    orders = all_linearizations(len(events), required)
    reference = execute(events, tuple(range(len(events))))
    different = [list(order) for order in orders if execute(events, order) != reference]
    return {
        "events": list(events),
        "dependent_edges": [list(edge) for edge in required],
        "edge_count": len(required),
        "total_order_edges": len(events) * (len(events) - 1) // 2,
        "linearizations": len(orders),
        "mismatches": len(different),
        "first_mismatch": different[0] if different else None,
        "final_state": list(reference[0]),
        "event_outputs": reference[1],
    }


def row_matches(received: dict, reconstructed: dict) -> bool:
    return received == reconstructed


def required_input_files(root: Path, freeze: dict) -> dict[str, bytes]:
    files: dict[str, bytes] = {}
    for relative, expected_id in freeze["original_input_git_blobs"].items():
        content = (root / relative).read_bytes()
        actual_id = git_blob_id(content)
        if actual_id != expected_id:
            raise AuditFailure(f"Git blob identity mismatch: {relative}: {actual_id}")
        expected_sha = freeze.get("original_source_sha256", {}).get(relative)
        if expected_sha is not None and digest(content) != expected_sha:
            raise AuditFailure(f"original source SHA-256 mismatch: {relative}")
        files[relative] = content
    return files


def reconstruct_raw(files: dict[str, bytes]) -> tuple[bytes, int, dict, list[dict]]:
    prefix = PREDECESSOR + "/"
    manifest = json.loads(files[prefix + "RAW_ARCHIVE_MANIFEST.json"])
    if manifest["archive_sha256"] != ARCHIVE_SHA256 or manifest["raw_sha256"] != RAW_SHA256:
        raise AuditFailure("manifest digest declarations differ from frozen values")
    b64_paths = [prefix + item["path"] for item in manifest["parts"]]
    text_parts = [files[path].decode("ascii") for path in b64_paths]
    if [len(piece) for piece in text_parts] != [item["characters"] for item in manifest["parts"]]:
        raise AuditFailure("base64 part character count mismatch")
    packed = base64.b64decode("".join(text_parts), validate=True)
    if len(packed) != ARCHIVE_BYTES or digest(packed) != ARCHIVE_SHA256:
        raise AuditFailure("reconstructed ZIP digest/length mismatch")
    with zipfile.ZipFile(io.BytesIO(packed), "r") as archive:
        names = archive.namelist()
        if names != ["RAW.jsonl"]:
            raise AuditFailure(f"unexpected ZIP member list: {names!r}")
        raw = archive.read("RAW.jsonl")
    if len(raw) != RAW_BYTES or digest(raw) != RAW_SHA256:
        raise AuditFailure("reconstructed JSONL digest/length mismatch")
    parsed = [json.loads(line) for line in raw.splitlines()]
    if len(parsed) != WORDS:
        raise AuditFailure(f"unexpected JSONL row count: {len(parsed)}")
    return raw, len(packed), manifest, parsed


def mutations_for(row: dict) -> dict[str, dict]:
    mutations: dict[str, dict] = {}
    def changed(name: str, value) -> None:
        copy = json.loads(json.dumps(row))
        copy[name] = value
        mutations[name] = copy

    changed("events", ["CLOSE", "OPEN"])
    changed("dependent_edges", [])
    changed("edge_count", 0)
    changed("linearizations", 0)
    changed("mismatches", 1)
    changed("first_mismatch", [1, 0])
    changed("final_state", list(ORIGIN))
    changed("event_outputs", {"0": "ADMITTED", "1": "APPLIED"})
    return mutations


def audit(root: Path, freeze_path: Path) -> tuple[dict, dict]:
    freeze = json.loads(freeze_path.read_text(encoding="utf-8"))
    evidence = required_input_files(root, freeze)
    raw_bytes, archive_size, manifest, rows = reconstruct_raw(evidence)
    universe = enumerate_reachable()
    relation = {left: {right: pair_is_independent(left, right, universe) for right in FROZEN_EVENTS}
                for left in FROZEN_EVENTS}
    table = [{"left": left, "right": right, "independent": relation[left][right]}
             for left in FROZEN_EVENTS for right in FROZEN_EVENTS]

    mismatch_rows = 0
    first_difference = None
    total_extensions = reduced = removed = 0
    words_with_mismatch = 0
    target_expected = expected_record(("OPEN", "CLOSE"), relation)
    target_actual = None
    control_orders = all_linearizations(2, [])
    control_reference = execute(("OPEN", "CLOSE"), (0, 1))
    control_divergences = sum(execute(("OPEN", "CLOSE"), order) != control_reference for order in control_orders)
    cursor = 0
    for length in range(5):
        for event_word in itertools.product(FROZEN_EVENTS, repeat=length):
            expected = expected_record(event_word, relation)
            actual = rows[cursor]
            if not row_matches(actual, expected):
                mismatch_rows += 1
                if first_difference is None:
                    first_difference = {"row_index": cursor, "expected": expected, "actual": actual}
            if tuple(event_word) == ("OPEN", "CLOSE"):
                target_actual = actual
            cursor += 1
            total_extensions += expected["linearizations"]
            reduced += int(expected["edge_count"] < expected["total_order_edges"])
            removed += expected["total_order_edges"] - expected["edge_count"]
            words_with_mismatch += int(expected["mismatches"] != 0)
    if cursor != WORDS:
        raise AuditFailure(f"enumerator generated {cursor} rows instead of {WORDS}")

    result_relative = PREDECESSOR + "/evidence/RESULT.json"
    original_result = json.loads(evidence[result_relative])
    expected_summary = {
        "status": "PASS_PARTIAL_ORDER_REPLAY_SCOPED",
        "event_alphabet": list(FROZEN_EVENTS),
        "reachable_state_count": len(universe),
        "pair_checks": len(FROZEN_EVENTS) ** 2 * len(universe),
        "independent_pair_count": sum(sum(int(value) for value in row.values()) for row in relation.values()),
        "event_words": WORDS,
        "topological_linearizations": total_extensions,
        "words_with_strict_constraint_reduction": reduced,
        "ordering_constraints_removed": removed,
        "words_with_mismatch": words_with_mismatch,
        "dependent_edge_omission_control_divergences": control_divergences,
        "formal_invocations": 1,
        "reruns": 0,
        "replacements": 0,
        "post_result_tuning": 0,
        "raw_sha256": digest(raw_bytes),
        "independence_table": table,
    }
    summary_mismatches = {name: {"expected": value, "actual": original_result.get(name)}
                          for name, value in expected_summary.items() if original_result.get(name) != value}

    neg_relative = PREDECESSOR + "/evidence/NEGATIVE_CONTROL.json"
    historic_audit = json.loads(evidence[PREDECESSOR + "/evidence/AUDIT.json"])
    historic_controls = json.loads(evidence[PREDECESSOR + "/evidence/CONTROLS.json"])
    historic_negative = json.loads(evidence[neg_relative])
    expected_negative = {
        "events": ["OPEN", "CLOSE"],
        "omitted_constraints": [[0, 1]],
        "linearizations": [list(order) for order in control_orders],
        "divergent_linearizations": control_divergences,
    }
    historic_record = {
        "audit_status": historic_audit.get("status"),
        "audit_errors": historic_audit.get("errors"),
        "control_status": historic_controls.get("status"),
        "rejected": historic_controls.get("rejected"),
        "total": historic_controls.get("total"),
        "linearizations_control_rejected": next((item.get("rejected") for item in historic_controls.get("controls", [])
                                                   if item.get("name") == "linearizations"), None),
        "negative_control_divergences": historic_negative.get("divergent_linearizations"),
    }
    historical_negative_matches = historic_negative == expected_negative

    new_controls = []
    if target_actual != target_expected:
        controls_considered = False
        controls_ok = False
    else:
        controls_considered = True
        for field, damaged in mutations_for(target_actual).items():
            effective = damaged[field] != target_actual[field]
            rejected = not row_matches(damaged, target_expected)
            new_controls.append({"field": field, "effective": effective, "rejected": rejected})
        controls_ok = len(new_controls) == 8 and all(x["effective"] and x["rejected"] for x in new_controls)

    archive_ok = (len(raw_bytes) == RAW_BYTES and digest(raw_bytes) == RAW_SHA256
                  and len(manifest["parts"]) == 2 and len(rows) == WORDS)
    summary_ok = not summary_mismatches
    predecessor_failure_preserved = (
        historic_record["audit_status"] == "FAIL_RAW_AUDIT"
        and historic_record["audit_errors"] == []
        and historic_record["control_status"] == "FAIL_CONTROLS"
        and historic_record["rejected"] == 7 and historic_record["total"] == 8
        and historic_record["linearizations_control_rejected"] is False
        and historical_negative_matches
    )
    pass_gate = (archive_ok and mismatch_rows == 0 and summary_ok and controls_ok
                 and predecessor_failure_preserved and words_with_mismatch == 0 and reduced > 0)
    audit_receipt = {
        "allocation": freeze["allocation"],
        "status": "PASS_INDEPENDENT_AUDIT_SCOPED" if pass_gate else "FAIL_AUDIT",
        "errors": [] if pass_gate else [
            *([{"raw_row_mismatches": mismatch_rows, "first_difference": first_difference}] if mismatch_rows else []),
            *([{"summary_mismatches": summary_mismatches}] if not summary_ok else []),
            *([{"mutation_controls": new_controls}] if not controls_ok else []),
            *([{"historical_hold_not_reconciled": historic_record}] if not predecessor_failure_preserved else []),
        ],
        "frozen_inputs": {
            "base_commit": freeze["base_commit"],
            "git_blobs_verified": len(evidence),
            "archive_bytes": archive_size,
            "archive_sha256": ARCHIVE_SHA256,
            "raw_bytes": len(raw_bytes),
            "raw_sha256": digest(raw_bytes),
            "raw_rows": len(rows),
        },
        "independent_reconstruction": {
            "reachable_states": len(universe),
            "pair_state_checks": len(FROZEN_EVENTS) ** 2 * len(universe),
            "event_words": cursor,
            "legal_linearizations": total_extensions,
            "row_mismatches": mismatch_rows,
            "summary_matches": summary_ok,
            "words_with_strict_constraint_reduction": reduced,
            "ordering_constraints_removed": removed,
        },
        "historical_4889_failure_preserved": historic_record,
        "historical_negative_control_matches": historical_negative_matches,
        "predecessor_candidate_invocations_by_successor": 0,
        "predecessor_auditor_invocations_by_successor": 0,
        "successor_audit_invocations": 1,
        "retries": 0,
    }
    control_receipt = {
        "allocation": freeze["allocation"],
        "status": "PASS_CONTROLS" if controls_ok else "FAIL_CONTROLS",
        "rejected": sum(int(item["rejected"]) for item in new_controls),
        "total": 8,
        "all_mutations_change_target_field": all(item["effective"] for item in new_controls),
        "controls": new_controls,
        "scope": "copied expected two-occurrence OPEN/CLOSE row; predecessor formal raw is never modified",
    }
    return audit_receipt, control_receipt


def main() -> None:
    source_root = Path(os.environ.get("SOURCE_ROOT", "/repo"))
    evidence_root = Path(os.environ.get("EVIDENCE_ROOT", "/evidence"))
    if not evidence_root.is_dir() or any(evidence_root.iterdir()):
        raise SystemExit("STOP_OUTPUT_NOT_EMPTY_OR_MISSING")
    allocation_dir = Path(__file__).resolve().parent
    runtime_files = ("/sys/fs/cgroup/memory.max", "/sys/fs/cgroup/cpu.max", "/sys/fs/cgroup/pids.max")
    runtime = {
        "python": sys.version,
        "platform": platform.platform(),
        "machine": platform.machine(),
        "uid": os.getuid(),
        "cgroup_files": {name: Path(name).read_text(encoding="ascii").strip()
                         for name in runtime_files if Path(name).is_file()},
        "effective_limit_claim": False,
    }
    try:
        audit_receipt, control_receipt = audit(source_root, allocation_dir / "FREEZE.json")
    except Exception as exc:  # preserve the first infrastructure/auditor failure as a terminal result
        audit_receipt = {"status": "FAIL_AUDIT", "errors": [{"type": type(exc).__name__, "message": str(exc)}]}
        control_receipt = {"status": "NOT_RUN", "rejected": 0, "total": 8, "controls": []}
    (evidence_root / "AUDIT.json").write_text(json.dumps(audit_receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (evidence_root / "CONTROLS.json").write_text(json.dumps(control_receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (evidence_root / "RUNTIME.json").write_text(json.dumps(runtime, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"audit_status": audit_receipt["status"], "audit_errors": len(audit_receipt.get("errors", [])),
                      "controls_status": control_receipt["status"], "controls_rejected": control_receipt.get("rejected")}, sort_keys=True))
    if audit_receipt["status"] != "PASS_INDEPENDENT_AUDIT_SCOPED":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
