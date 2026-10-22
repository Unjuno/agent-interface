#!/usr/bin/env python3
"""Independent raw-only audit; shares no candidate or spec implementation."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
from pathlib import Path

PACKAGE = Path(__file__).resolve().parent


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def u(seed: int, salt: str) -> float:
    value = hashlib.sha256((str(seed) + "|" + salt).encode("ascii")).digest()
    return int.from_bytes(value[:8], "big") / 2**64


def replay(events: list[str], seed: int, window: dict, fixture: dict) -> dict:
    present = set(events)
    allowed = set(fixture["base_trace"])
    if len(present) != len(events) or not present <= allowed:
        return {"fingerprint": "INVALID_AUTHORITY_OR_DEPENDENCY", "exit_code": fixture["same_exit_code"]}
    if events != [event for event in fixture["base_trace"] if event in present]:
        return {"fingerprint": "INVALID_AUTHORITY_OR_DEPENDENCY", "exit_code": fixture["same_exit_code"]}
    if not set(fixture["mandatory_events"]) <= present:
        return {"fingerprint": "INVALID_AUTHORITY_OR_DEPENDENCY", "exit_code": fixture["same_exit_code"]}
    for event, parents in fixture["dependencies"].items():
        if event in present and not set(parents) <= present:
            return {"fingerprint": "INVALID_AUTHORITY_OR_DEPENDENCY", "exit_code": fixture["same_exit_code"]}
    if "competing_fault" in present and u(seed, fixture["competing_salt"]) < fixture["competing_rate"]:
        return {"fingerprint": fixture["competing_fingerprint"], "exit_code": fixture["same_exit_code"]}
    rate = window["base_rate"] if "warmup" in present else window["reduced_rate"]
    if u(seed, fixture["target_salt"]) < rate:
        return {"fingerprint": fixture["target_fingerprint"], "exit_code": fixture["same_exit_code"]}
    return {"fingerprint": fixture["no_failure_fingerprint"], "exit_code": 0}


def lower_tail(k: int, n: int, p: float) -> float:
    if p <= 0:
        return 1.0 if k == 0 else 0.0
    if p >= 1:
        return 1.0 if k >= n else 0.0
    term = math.comb(n, k) * p**k * (1-p)**(n-k)
    total = term
    for index in range(k, 0, -1):
        term *= (index/(n-index+1)) * ((1-p)/p)
        total += term
    return min(1.0, total)


def upper_tail(k: int, n: int, p: float) -> float:
    if p <= 0:
        return 1.0 if k <= 0 else 0.0
    if p >= 1:
        return 1.0
    term = math.comb(n, k) * p**k * (1-p)**(n-k)
    total = term
    for index in range(k, n):
        term *= ((n-index)/(index+1)) * (p/(1-p))
        total += term
    return min(1.0, total)


def exact_lower(k: int, n: int, alpha: float) -> float:
    if n <= 0 or k <= 0:
        return 0.0
    lo, hi = 0.0, k/n
    for _ in range(64):
        mid = (lo+hi)/2
        if upper_tail(k, n, mid) > alpha:
            hi = mid
        else:
            lo = mid
    return lo


def exact_upper(k: int, n: int, alpha: float) -> float:
    if n <= 0 or k >= n:
        return 1.0
    lo, hi = k/n, 1.0
    for _ in range(64):
        mid = (lo+hi)/2
        if lower_tail(k, n, mid) > alpha:
            lo = mid
        else:
            hi = mid
    return hi


def counts(rows: list[dict], fixture: dict) -> dict:
    n = len(rows)
    base = reduced = gains = losses = competitor = 0
    for row in rows:
        b = row["base"]["fingerprint"] == fixture["target_fingerprint"]
        r = row["reduced"]["fingerprint"] == fixture["target_fingerprint"]
        base += int(b); reduced += int(r)
        gains += int(r and not b); losses += int(b and not r)
        competitor += int(row["base"]["fingerprint"] == fixture["competing_fingerprint"])
    return {"n": n, "base_target": base, "reduced_target": reduced,
            "gains": gains, "losses": losses, "competitor_rows": competitor}


def interval(c: dict, alpha: float) -> dict:
    n = c["n"]
    if n == 0:
        return {"delta": None, "lower": None, "upper": None}
    return {"delta": (c["reduced_target"]-c["base_target"])/n,
            "lower": exact_lower(c["gains"], n, alpha)-exact_upper(c["losses"], n, alpha),
            "upper": exact_upper(c["gains"], n, alpha)-exact_lower(c["losses"], n, alpha)}


def classify(i: dict, margin: float) -> str:
    if i["lower"] >= -margin:
        return "PASS_NONINFERIOR"
    if i["upper"] < -margin:
        return "FAIL_NONINFERIORITY"
    return "UNKNOWN_INTERVAL_OVERLAPS_MARGIN"


def expected_schedule(fixture: dict) -> list[dict]:
    schedule = []
    for case in fixture["cases"]:
        for window in case["windows"]:
            for offset in range(window["n"]):
                schedule.append({"case_id": case["id"], "window_id": window["id"],
                                 "window_kind": window["kind"], "slot": window["start"]+offset,
                                 "seed": window["seed_start"]+offset,
                                 "base_events": fixture["base_trace"],
                                 "reduced_events": fixture["reduced_trace"]})
    return schedule


def expected_summary(rows: list[dict], case: dict, fixture: dict) -> dict:
    alpha = fixture["familywise_alpha"]/(4*fixture["familywise_contrasts"])
    pooled_counts = counts(rows, fixture)
    pooled_interval = interval(pooled_counts, alpha)
    block_items = []
    for window in case["windows"]:
        group = [r for r in rows if r["window_id"] == window["id"]]
        c = counts(group, fixture)
        i = interval(c, alpha)
        block_items.append({"window_id": window["id"], "kind": window["kind"],
                            "counts": c, "interval": i, "decision": classify(i, fixture["noninferiority_margin"])})
    if any(item["kind"] == "ambiguous" for item in block_items):
        block_decision = "UNKNOWN_TRANSITION_WINDOW"
    elif any(item["counts"]["n"] < fixture["minimum_block_support"] for item in block_items):
        block_decision = "UNKNOWN_INSUFFICIENT_BLOCK_SUPPORT"
    elif any(item["decision"] == "FAIL_NONINFERIORITY" for item in block_items):
        block_decision = "FAIL_BLOCK_NONINFERIORITY"
    elif all(item["decision"] == "PASS_NONINFERIOR" for item in block_items):
        block_decision = "PASS_ALL_BLOCKS_NONINFERIOR"
    else:
        block_decision = "UNKNOWN_BLOCK_INTERVAL"
    return {"pooled": {"counts": pooled_counts, "interval": pooled_interval,
                       "decision": classify(pooled_interval, fixture["noninferiority_margin"])},
            "blocks": block_items, "block_decision": block_decision}


def audit(raw: dict, fixture: dict, fixture_digest: str) -> dict:
    errors = []
    if raw.get("schema") != "unjuno.issue8493.candidate.raw.v1":
        errors.append("raw_schema_mismatch")
    if raw.get("fixture_sha256") != fixture_digest or raw.get("expected_fixture_sha256") != fixture_digest:
        errors.append("fixture_digest_mismatch")
    expected = expected_schedule(fixture)
    cases = raw.get("cases", [])
    if [c.get("case_id") for c in cases] != [c["id"] for c in fixture["cases"]]:
        errors.append("case_matrix_mismatch")
    flat = [row for case in cases for row in case.get("rows", [])]
    if len(flat) != len(expected):
        errors.append("row_count_mismatch")
    if len(flat) == len(expected):
        for index, (row, schedule) in enumerate(zip(flat, expected)):
            if any(row.get(key) != value for key, value in schedule.items()):
                errors.append("schedule_or_trace_mismatch:"+str(index))
            case = next(c for c in fixture["cases"] if c["id"] == row.get("case_id"))
            window = next((w for w in case["windows"] if w["id"] == row.get("window_id")), None)
            if window is None:
                errors.append("unknown_window:"+str(index)); continue
            if row.get("base") != replay(row["base_events"], row["seed"], window, fixture):
                errors.append("base_oracle_mismatch:"+str(index))
            if row.get("reduced") != replay(row["reduced_events"], row["seed"], window, fixture):
                errors.append("reduced_oracle_mismatch:"+str(index))
        seeds = [row.get("seed") for row in flat]
        if len(seeds) != len(set(seeds)):
            errors.append("seed_reuse")
    result_cases = []
    for case_data, case_spec in zip(cases, fixture["cases"]):
        expected_result = expected_summary(case_data.get("rows", []), case_spec, fixture)
        if case_data.get("summary") != expected_result:
            errors.append("summary_mismatch:"+case_spec["id"])
        result_cases.append({"case_id": case_spec["id"], "role": case_spec["role"], **expected_result})
    if fixture["base_trace"] == fixture["reduced_trace"]:
        errors.append("reduction_not_applied")
    for trace_name in ("base_trace", "reduced_trace"):
        trace = fixture[trace_name]
        present = set(trace)
        if not set(fixture["mandatory_events"]) <= present:
            errors.append("mandatory_event_missing:"+trace_name)
        for event, parents in fixture["dependencies"].items():
            if event in present and not set(parents) <= present:
                errors.append("dependency_violation:"+trace_name+":"+event)
    competitors = sum(c["summary"]["pooled"]["counts"]["competitor_rows"] for c in cases) if cases else 0
    if competitors <= 0:
        errors.append("competing_fingerprint_control_not_observed")
    competing_case = next((c for c in result_cases if c["role"] == "fingerprint_identity_control"), None)
    if competing_case is None or competing_case["pooled"]["counts"]["competitor_rows"] <= 0:
        errors.append("identity_control_has_no_competing_fingerprint")
    harmful = [c for c in result_cases if c["role"] == "planted_harmful_regime"]
    false_accepts = [c["case_id"] for c in harmful if c["pooled"]["decision"] == "PASS_NONINFERIOR"
                     and c["block_decision"] == "FAIL_BLOCK_NONINFERIORITY"]
    stable = next((c for c in result_cases if c["role"] == "negative_control"), None)
    if not false_accepts:
        errors.append("no_pooled_false_assurance_counterexample")
    if stable is None or stable["block_decision"] != "PASS_ALL_BLOCKS_NONINFERIOR":
        errors.append("stable_negative_control_failed")
    sparse = next((c for c in result_cases if c["role"] == "insufficient_support_control"), None)
    if sparse is None or sparse["block_decision"] != "UNKNOWN_INSUFFICIENT_BLOCK_SUPPORT":
        errors.append("sparse_block_not_unknown")
    ambiguous = next((c for c in result_cases if c["role"] == "transition_ambiguity_control"), None)
    if ambiguous is None or ambiguous["block_decision"] != "UNKNOWN_TRANSITION_WINDOW":
        errors.append("transition_window_not_unknown")
    return {"schema": "unjuno.issue8493.independent-audit.v1", "valid": not errors,
            "errors": errors, "fixture_sha256": fixture_digest,
            "rows_reconstructed": len(flat), "competing_fingerprint_rows": competitors,
            "pooled_false_assurance_cases": false_accepts,
            "cases": result_cases}


def mutations(raw: dict, fixture: dict, fixture_digest: str) -> dict:
    probes = []
    def probe(name: str, mutate) -> None:
        candidate = copy.deepcopy(raw); mutate(candidate)
        rejected = not audit(candidate, fixture, fixture_digest)["valid"]
        probes.append({"name": name, "rejected": rejected})
    probe("drop_raw_row", lambda x: x["cases"][0]["rows"].pop())
    probe("relabel_temporal_window", lambda x: x["cases"][1]["rows"][0].__setitem__("window_id", "late"))
    probe("remove_mandatory_release", lambda x: x["cases"][0]["rows"][0]["reduced_events"].remove("release"))
    probe("forge_target_fingerprint", lambda x: x["cases"][0]["rows"][0]["reduced"].__setitem__("fingerprint", fixture["competing_fingerprint"]))
    probe("accept_sparse_block", lambda x: x["cases"][3]["summary"].__setitem__("block_decision", "PASS_ALL_BLOCKS_NONINFERIOR"))
    probe("erase_competing_identity", lambda x: x["cases"][5]["rows"][0]["base"].__setitem__("fingerprint", fixture["target_fingerprint"]))
    return {"controls": probes, "rejected": sum(p["rejected"] for p in probes), "total": len(probes)}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--freeze-digest", required=True)
    args = parser.parse_args()
    freeze_path = PACKAGE / "FREEZE.json"
    freeze = json.loads(freeze_path.read_text(encoding="utf-8"))
    if sha(freeze_path) != args.freeze_digest:
        raise SystemExit("FREEZE_DIGEST_MISMATCH")
    for rel, expected_sha in freeze["files"].items():
        if sha(PACKAGE/rel) != expected_sha:
            raise SystemExit("FROZEN_SOURCE_MISMATCH:"+rel)
    fixture_path = PACKAGE / "fixture.json"
    fixture_digest = sha(fixture_path)
    if fixture_digest != freeze["fixture_sha256"]:
        raise SystemExit("FIXTURE_DIGEST_MISMATCH")
    raw_path = Path(args.raw)
    raw = json.loads(raw_path.read_text(encoding="utf-8"))
    result = audit(raw, json.loads(fixture_path.read_text(encoding="utf-8")), fixture_digest)
    mutation_report = mutations(raw, json.loads(fixture_path.read_text(encoding="utf-8")), fixture_digest)
    result["mutation_controls"] = mutation_report
    if mutation_report["rejected"] != mutation_report["total"]:
        result["errors"].append("mutation_control_false_accept")
        result["valid"] = False
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, sort_keys=True, indent=2)+"\n", encoding="utf-8")
    print(json.dumps({"audit": "PASS" if result["valid"] else "FAIL",
                      "rows_reconstructed": result["rows_reconstructed"],
                      "mutations_rejected": mutation_report["rejected"],
                      "pooled_false_assurance_cases": result["pooled_false_assurance_cases"]}, sort_keys=True))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
