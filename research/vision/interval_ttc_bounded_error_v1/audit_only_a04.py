"""A04 independent raw-only prefix audit for #8157; never runs a candidate."""

from __future__ import annotations

import hashlib
import json
import math
import pathlib
import copy
import re
import sys
from collections import Counter


EXPECTED_IDS = 200
EXPECTED_PREFIXES = 2400
EXPECTED_PROFILES = {
    "approach", "passby", "stationary", "iid", "correlated",
    "irregular_dropout", "acceleration", "occlusion", "identity_swap",
    "understated_bound",
}
IN_MODEL = {"approach", "iid", "correlated", "irregular_dropout"}
MISMATCH_KINDS = {"point_mismatch", "interval_mismatch"}


def finite_number(value: object) -> bool:
    return type(value) in (int, float) and math.isfinite(value)


def estimate_prefix(history: list[dict]) -> tuple[float | None, list[float] | None]:
    """Independent causal reconstruction using only the supplied prefix."""
    if any(not finite_number(item.get("t_s")) for item in history):
        return None, None
    if any(history[i]["t_s"] >= history[i + 1]["t_s"]
           for i in range(len(history) - 1)):
        return None, None
    if any(history[i].get("radius_px") is None
           and history[i + 1].get("radius_px") is None
           for i in range(len(history) - 1)):
        return None, None
    seen = [item for item in history if item.get("radius_px") is not None]
    if len(seen) < 2:
        return None, None
    for item in seen:
        if (not finite_number(item.get("t_s"))
                or not finite_number(item.get("radius_px"))
                or not finite_number(item.get("bound_px"))
                or item["bound_px"] < 0):
            return None, None
    if len({item.get("track_id") for item in seen}) != 1:
        return None, None
    if any(seen[i]["t_s"] >= seen[i + 1]["t_s"]
           for i in range(len(seen) - 1)):
        return None, None

    slope_intervals = []
    for left, right in zip(seen, seen[1:]):
        dt = right["t_s"] - left["t_s"]
        left_low = left["radius_px"] - left["bound_px"]
        left_high = left["radius_px"] + left["bound_px"]
        right_low = right["radius_px"] - right["bound_px"]
        right_high = right["radius_px"] + right["bound_px"]
        if left_low <= 0 or right_low <= 0:
            return None, None
        slope_intervals.append(((right_low - left_high) / dt,
                                (right_high - left_low) / dt))
    velocity_low = max(pair[0] for pair in slope_intervals)
    velocity_high = min(pair[1] for pair in slope_intervals)
    if velocity_low <= 0 or velocity_high < velocity_low:
        return None, None
    last = seen[-1]
    radius_low = last["radius_px"] - last["bound_px"]
    radius_high = last["radius_px"] + last["bound_px"]
    if radius_low <= 0:
        return None, None
    point = None
    previous, current = seen[-2:]
    delta = current["radius_px"] - previous["radius_px"]
    if delta > 0:
        point = current["radius_px"] * (current["t_s"] - previous["t_s"]) / delta
    return point, [radius_low / velocity_high, radius_high / velocity_low]


def _near(left: object, right: object) -> bool:
    if left is None or right is None:
        return left is None and right is None
    return (finite_number(left) and finite_number(right)
            and math.isclose(float(left), float(right), rel_tol=1e-10, abs_tol=1e-12))


def _same_interval(left: object, right: object) -> bool:
    return (left is None and right is None) or (
        type(left) is list and type(right) is list and len(left) == 2 and len(right) == 2
        and _near(left[0], right[0]) and _near(left[1], right[1]))


def audit_rows(public_rows: list[dict], oracle_rows: list[dict],
               candidate_rows: list[dict]) -> list[str]:
    errors: list[str] = []
    if not (len(public_rows) == len(oracle_rows) == len(candidate_rows) == EXPECTED_IDS):
        errors.append("sequence_count")
    public = {row.get("id"): row for row in public_rows}
    oracle = {row.get("id"): row for row in oracle_rows}
    candidate = {row.get("id"): row for row in candidate_rows}
    if (len(public) != len(public_rows) or len(oracle) != len(oracle_rows)
            or len(candidate) != len(candidate_rows)):
        errors.append("duplicate_id")
    if set(public) != set(oracle) or set(public) != set(candidate):
        errors.append("id_join")

    profile_rows: dict[str, list[dict]] = {}
    for truth in oracle_rows:
        profile_rows.setdefault(truth.get("profile"), []).append(truth)
    if set(profile_rows) != EXPECTED_PROFILES:
        errors.append("profile_set")
    for profile, rows in profile_rows.items():
        if len(rows) != 20 or sum(row.get("hazard") is True for row in rows) != 10:
            errors.append("profile_hazard_balance:" + str(profile))
        for split in ("calibration", "evaluation"):
            group = [row for row in rows if row.get("split") == split]
            if (len(group) != 10
                    or sum(row.get("hazard") is True for row in group) != 5
                    or sum(row.get("hazard") is False for row in group) != 5):
                errors.append("split_hazard_balance:" + str(profile) + ":" + split)

    reconstructed = 0
    numeric_eligible_intervals = 0
    containment_misses = 0
    profile_observed_prefixes: Counter[str] = Counter()
    profile_numeric_intervals: Counter[str] = Counter()
    for sequence_id in sorted(set(public) & set(oracle) & set(candidate)):
        pub = public[sequence_id]
        truth = oracle[sequence_id]
        output = candidate[sequence_id]
        history = pub.get("history")
        truth_rows = truth.get("truth")
        estimates = output.get("estimates")
        if not (type(history) is list and type(truth_rows) is list
                and type(estimates) is list and len(history) == len(truth_rows) == len(estimates) == 12):
            errors.append("prefix_count:" + str(sequence_id))
            continue
        if pub.get("id") != truth.get("id") or output.get("id") != sequence_id:
            errors.append("id_binding:" + str(sequence_id))
        for index, observation in enumerate(history):
            expected_point, expected_interval = estimate_prefix(history[:index + 1])
            actual = estimates[index]
            oracle_step = truth_rows[index]
            profile = str(truth.get("profile"))
            profile_observed_prefixes[profile] += 1
            reconstructed += 1
            if not _near(actual.get("t_s"), observation.get("t_s")):
                errors.append(f"timestamp_mismatch:{sequence_id}:{index}")
            if not _near(oracle_step.get("t_s"), observation.get("t_s")):
                errors.append(f"oracle_time_mismatch:{sequence_id}:{index}")
            if not _near(actual.get("point_ttc_s"), expected_point):
                errors.append(f"point_mismatch:{sequence_id}:{index}")
            if not _same_interval(actual.get("interval_s"), expected_interval):
                errors.append(f"interval_mismatch:{sequence_id}:{index}")

            valid = [item for item in history[:index + 1]
                     if item.get("radius_px") is not None]
            expected_pixel = expected_area = None
            if (len(valid) >= 2 and valid[-2]["radius_px"] > 0
                    and valid[-1]["radius_px"] > 0):
                r0, r1 = valid[-2]["radius_px"], valid[-1]["radius_px"]
                expected_pixel = abs(r1 - r0)
                expected_area = abs((r1 * r1) / (r0 * r0) - 1.0)
            if not _near(actual.get("pixel_change_px"), expected_pixel):
                errors.append(f"pixel_mismatch:{sequence_id}:{index}")
            if not _near(actual.get("relative_area_change"), expected_area):
                errors.append(f"area_mismatch:{sequence_id}:{index}")

            if truth.get("eligible_in_model") is True and truth.get("hazard") is True:
                interval = actual.get("interval_s")
                oracle_ttc = oracle_step.get("true_ttc_s")
                if type(interval) is list and len(interval) == 2:
                    numeric_eligible_intervals += 1
                    profile_numeric_intervals[profile] += 1
                    if (not finite_number(oracle_ttc) or interval[0] > oracle_ttc + 1e-10
                            or interval[1] < oracle_ttc - 1e-10):
                        containment_misses += 1
                        errors.append(f"oracle_containment:{sequence_id}:{index}")

    if reconstructed != EXPECTED_PREFIXES:
        errors.append("reconstructed_prefix_count")
    if containment_misses:
        errors.append("eligible_oracle_containment")
    return errors


def read_jsonl(path: pathlib.Path) -> list[dict]:
    with path.open(encoding="utf-8") as stream:
        return [json.loads(line) for line in stream if line.strip()]


def sha256(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_manifest(repo_root: pathlib.Path, manifest: pathlib.Path) -> tuple[bool, list[str]]:
    errors = []
    for line_number, line in enumerate(manifest.read_text(encoding="utf-8").splitlines(), 1):
        match = re.fullmatch(r"([0-9a-f]{64})  (.+)", line)
        if not match:
            errors.append(f"manifest_line:{manifest.name}:{line_number}")
            continue
        expected, relative = match.groups()
        path = repo_root / pathlib.PurePosixPath(relative)
        if not path.is_file() or sha256(path) != expected:
            errors.append(f"manifest_hash:{manifest.name}:{relative}")
    return not errors, errors


def mutation_checks(public_rows: list[dict], oracle_rows: list[dict],
                    candidate_rows: list[dict]) -> dict[str, bool]:
    checks: dict[str, bool] = {}

    public = copy.deepcopy(public_rows)
    target = next(row for row in public
                  if row["history"][1].get("radius_px") is not None)
    target["history"][1]["bound_px"] += 0.25
    checks["bound"] = any("interval_mismatch" in error
                          for error in audit_rows(public, oracle_rows, candidate_rows))

    public = copy.deepcopy(public_rows)
    public[0]["history"][1]["t_s"] += 0.005
    checks["timestamp"] = bool(audit_rows(public, oracle_rows, candidate_rows))

    public = copy.deepcopy(public_rows)
    public[0]["history"].pop(3)
    checks["removed_sample"] = any(error.startswith("prefix_count:")
                                   for error in audit_rows(public, oracle_rows, candidate_rows))

    oracle = copy.deepcopy(oracle_rows)
    oracle[0]["hazard"] = not oracle[0]["hazard"]
    checks["oracle_hazard_label"] = any("profile_hazard_balance" in error
                                        for error in audit_rows(public_rows, oracle, candidate_rows))

    candidate = copy.deepcopy(candidate_rows)
    interval = next(item for row in candidate for item in row["estimates"]
                    if item.get("interval_s") is not None)
    interval["interval_s"][1] += 0.1
    checks["interval_endpoint"] = any("interval_mismatch" in error
                                      for error in audit_rows(public_rows, oracle_rows, candidate))
    return checks


def main() -> int:
    if len(sys.argv) != 3:
        raise SystemExit("usage: audit_only_a04.py PACKAGE_ROOT OUTPUT_JSON")
    root, output = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
    a02 = root / "results" / "FORMAL_A02"
    public_path = a02 / "public" / "public.jsonl"
    oracle_path = a02 / "oracle" / "oracle.jsonl"
    candidate_path = a02 / "candidate" / "candidate.jsonl"
    first_report_path = a02 / "audit" / "REPORT.json"
    public_rows = read_jsonl(public_path)
    oracle_rows = read_jsonl(oracle_path)
    candidate_rows = read_jsonl(candidate_path)
    errors = audit_rows(public_rows, oracle_rows, candidate_rows)

    repo_root = root.parents[2]
    freeze = json.loads((root / "FREEZE_A04.json").read_text(encoding="utf-8"))
    frozen_source_hashes = freeze["a02_artifact_sha256"]
    raw_hash_checks = {
        "public": sha256(public_path) == frozen_source_hashes["public"],
        "oracle": sha256(oracle_path) == frozen_source_hashes["oracle"],
        "candidate": sha256(candidate_path) == frozen_source_hashes["candidate"],
        "first_audit": sha256(first_report_path) == frozen_source_hashes["first_audit"],
        "audit_program": sha256(root / "audit_only_a04.py") == freeze["audit_program_sha256"],
        "protocol": sha256(root / "PROTOCOL_A04_AUDIT_ONLY.md") == freeze["protocol_sha256"],
        "construction_tests": sha256(root / "test_audit_only_a04.py") == freeze["test_program_sha256"],
        "a03_stop": sha256(root / "results/FORMAL_A03_AUDIT_ONLY/STOP.md")
                    == freeze["a03_stop_sha256"],
        "a03_run_record": sha256(root / "results/FORMAL_A03_AUDIT_ONLY/RUN_RECORD.json")
                          == freeze["a03_run_record_sha256"],
        "a03_freeze": sha256(root / "FREEZE_A03.json") == freeze["a03_freeze_sha256"],
    }
    source_manifest_pass, source_manifest_errors = verify_manifest(
        repo_root, a02 / "SOURCE_SHA256.txt")
    artifact_manifest_pass, artifact_manifest_errors = verify_manifest(
        repo_root, a02 / "ARTIFACT_SHA256.txt")

    original = json.loads(first_report_path.read_text(encoding="utf-8"))
    mismatch_errors = [item for item in original.get("errors", [])
                       if str(item).split(":", 1)[0] in MISMATCH_KINDS]
    truth_by_id = {row["id"]: row for row in oracle_rows}
    candidate_by_id = {row["id"]: row for row in candidate_rows}
    mismatch_profile_counts: Counter[str] = Counter()
    mismatch_kind_counts: Counter[str] = Counter()
    malformed_mismatches = []
    for item in mismatch_errors:
        parts = str(item).split(":")
        if len(parts) != 3 or parts[0] not in MISMATCH_KINDS or parts[1] not in truth_by_id:
            malformed_mismatches.append(str(item))
            continue
        mismatch_kind_counts[parts[0]] += 1
        mismatch_profile_counts[truth_by_id[parts[1]]["profile"]] += 1
    attribution_pass = (
        len(mismatch_errors) == 98
        and mismatch_kind_counts == Counter({"point_mismatch": 49, "interval_mismatch": 49})
        and mismatch_profile_counts == Counter({"occlusion": 98})
        and not malformed_mismatches
    )
    mutation_results = mutation_checks(public_rows, oracle_rows, candidate_rows)
    integrity_pass = (all(raw_hash_checks.values()) and source_manifest_pass and artifact_manifest_pass
                      and not source_manifest_errors and not artifact_manifest_errors)
    overall_pass = (not errors and attribution_pass and integrity_pass
                    and all(mutation_results.values()))
    profile_prefixes = Counter()
    eligible_numeric = 0
    for row in public_rows:
        truth = truth_by_id.get(row.get("id"), {})
        profile_prefixes[str(truth.get("profile"))] += len(row.get("history", []))
        if truth.get("eligible_in_model") is True and truth.get("hazard") is True:
            eligible_numeric += sum(estimate.get("interval_s") is not None
                                    for estimate in candidate_by_id.get(row.get("id"), {}).get("estimates", []))

    report = {
        "schema": "issue-8157-a04-raw-prefix-audit-v1",
        "scope": "A04 audit-only raw reconciliation; no candidate, generator, original auditor, or A03 auditor invocation",
        "source_main_sha": freeze["source_main_sha"],
        "a02_head_sha": freeze["a02_head_sha"],
        "a02_source_commit": freeze["a02_source_commit"],
        "sequence_count": len(public_rows),
        "prefix_count": sum(len(row.get("history", [])) for row in public_rows),
        "prefixes_by_profile": dict(sorted(profile_prefixes.items())),
        "reconstruction_errors": errors,
        "candidate_reconstruction_pass": not errors,
        "source_manifest_pass": source_manifest_pass,
        "source_manifest_errors": source_manifest_errors,
        "artifact_manifest_pass": artifact_manifest_pass,
        "artifact_manifest_errors": artifact_manifest_errors,
        "frozen_hash_checks": raw_hash_checks,
        "frozen_hashes_pass": all(raw_hash_checks.values()),
        "original_a02_mismatch_count": len(mismatch_errors),
        "original_a02_mismatch_kind_counts": dict(sorted(mismatch_kind_counts.items())),
        "original_a02_mismatch_profile_counts": dict(sorted(mismatch_profile_counts.items())),
        "original_mismatch_attribution_pass": attribution_pass,
        "mutation_checks": mutation_results,
        "mutation_checks_pass": all(mutation_results.values()),
        "eligible_hazard_numeric_intervals": eligible_numeric,
        "disposition": "PASS_RAW_RECONCILIATION_ONLY" if overall_pass
                      else "FAIL_AUDIT_ONLY",
        "a02_disposition": "FAIL_METHOD_PRESERVED_UNSCORABLE",
        "a03_disposition": "STOP_AUDITOR_RUNTIME_ERROR_PRESERVED",
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return 0 if overall_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
