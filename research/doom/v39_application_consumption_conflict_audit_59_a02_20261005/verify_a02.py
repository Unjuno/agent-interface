import hashlib
import json
from pathlib import Path

EXPECTED = "3f664d52a492ad9d0cbbbdb70880ffe16a4909d4bf2c2880d51891d523652363"
IMPLEMENTATIONS = ("baseline", "candidate")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_cases(cases):
    errors = []
    counts = {"ordered": 0, "incomplete": 0}
    mismatches = 0
    if type(cases) is not list or len(cases) != 100:
        return ["case count != 100"], counts, 0
    for index, row in enumerate(cases):
        down, up = row.get("down"), row.get("up")
        if (type(down) is not list or type(up) is not list or
                len(down) != 2 or len(up) != 2 or
                any(type(v) is not int for v in down + up) or
                down[0] > down[1] or up[0] > up[1]):
            errors.append(f"{index}: malformed interval")
            continue
        ordered = down[1] < up[0]
        if row.get("expected_ordered") is not ordered:
            mismatches += 1
            errors.append(f"{index}: expected_ordered contradicts interval order")
        status = "adapter_edge_brackets_paired" if ordered else "adapter_edge_receipt_incomplete"
        if row.get("status") != status:
            errors.append(f"{index}: status contradicts interval order")
        if ordered:
            counts["ordered"] += 1
            if row.get("down_edge_interval_ns") != down or row.get("up_edge_interval_ns") != up:
                errors.append(f"{index}: paired interval output differs")
        else:
            counts["incomplete"] += 1
            if row.get("down_edge_interval_ns") is not None or row.get("up_edge_interval_ns") is not None:
                errors.append(f"{index}: incomplete row exposes an interval")
    if counts != {"ordered": 15, "incomplete": 85}:
        errors.append(f"counts are {counts}, expected 15/85")
    return errors, counts, mismatches


def main():
    root = Path(__file__).resolve().parent
    source = root / "formal" / "source-A01.json"
    mutated = root / "formal" / "mutated-A01.json"
    candidate = json.loads((root / "formal" / "AUDIT_A02.json").read_text())
    errors = []
    observed = sha(source)
    if observed != EXPECTED:
        errors.append("source A01 SHA-256 mismatch")
    original_raw = json.loads(source.read_text())
    mutated_raw = json.loads(mutated.read_text())
    totals = {}
    mismatch_total = 0
    for name in IMPLEMENTATIONS:
        base_cases = original_raw["interval_sweep"][name]["cases"]
        changed_cases = mutated_raw["interval_sweep"][name]["cases"]
        base_errors, base_counts, _ = verify_cases(base_cases)
        changed_errors, changed_counts, changed_mismatches = verify_cases(changed_cases)
        if base_errors:
            errors.extend(f"original {name}: {x}" for x in base_errors)
        if not changed_errors:
            errors.append(f"mutation {name}: corruption was not detected")
        if changed_mismatches != 2:
            errors.append(f"mutation {name}: expected 2 chronology mismatches, got {changed_mismatches}")
        if base_counts != changed_counts:
            errors.append(f"mutation {name}: derived counts changed")
        totals[name] = {"original": base_counts, "mutated": changed_counts,
                        "mutation_mismatches": changed_mismatches}
        mismatch_total += changed_mismatches
    if candidate.get("status") != "PASS_RAW_CHRONOLOGY_MUTATION_REJECTED":
        errors.append("candidate disposition is not PASS")
    if candidate.get("original", {}).get("status") != "PASS":
        errors.append("candidate did not pass untouched source")
    if candidate.get("mutated", {}).get("chronology_mismatches") != mismatch_total:
        errors.append("candidate mismatch summary disagrees with independent reconstruction")
    report = {
        "schema": "v39-application-consumption-audit-a02-independent-v1",
        "status": "PASS_INDEPENDENT_RAW_AUDIT" if not errors else "FAIL_INDEPENDENT_RAW_AUDIT",
        "source_a01_sha256": observed,
        "chronology_mismatches_recomputed": mismatch_total,
        "implementations": totals,
        "errors": errors,
        "scope": "Independent deterministic JSON chronology audit only; no runtime, GUI, game, model, or input execution.",
    }
    (root / "formal" / "INDEPENDENT_AUDIT.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
