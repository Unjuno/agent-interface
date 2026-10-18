"""Independent audit of the frozen sample-layer mutation result."""
import hashlib
import itertools
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    freeze = json.loads((ROOT / "FREEZE.json").read_text(encoding="utf-8"))
    raw = json.loads((ROOT / "raw" / "A01.json").read_text(encoding="utf-8"))
    errors = []
    for name, relative in freeze["files"].items():
        if sha256(ROOT / relative) != freeze["sha256"][name]:
            errors.append(f"{name} hash mismatch")
    manifest = ROOT / "SHA256SUMS"
    if not manifest.exists():
        errors.append("SHA256SUMS is missing")
    else:
        for line in manifest.read_text(encoding="utf-8").splitlines():
            try:
                expected_hash, relative = line.split("  ", 1)
                path = ROOT / relative
                if not path.is_file() or sha256(path) != expected_hash:
                    errors.append(f"manifest hash mismatch: {relative}")
            except ValueError:
                errors.append("malformed SHA256SUMS row")

    expected_layers = ("event", "measurement", "adapter_edge", "bracket",
                       "pre_sample", "post_sample")
    expected_values = ("true", "int_one", "int_zero", "null", "string_false")
    expected = list(itertools.product(range(2), expected_layers, expected_values))
    observed = [(row.get("row_index"), row.get("layer"), row.get("value"))
                for row in raw.get("mutations", [])]
    if observed != expected:
        errors.append("mutation matrix identity/order mismatch")

    baseline_false_accepts = [row for row in raw.get("mutations", [])
                              if row.get("baseline", {}).get("status") ==
                              "adapter_edge_brackets_paired"]
    expected_sample_accepts = [
        (row, layer, value)
        for row, layer, value in expected
        if layer in ("pre_sample", "post_sample")]
    observed_sample_accepts = [
        (row.get("row_index"), row.get("layer"), row.get("value"))
        for row in baseline_false_accepts]
    if observed_sample_accepts != expected_sample_accepts:
        errors.append("parent false accepts are not exactly the sample-layer cases")

    for mutation in raw.get("mutations", []):
        candidate = mutation.get("candidate", {})
        if candidate.get("status") != "adapter_edge_receipt_incomplete":
            errors.append("candidate paired a contradictory/nonboolean claim")
        if (candidate.get("down_edge_interval_ns") is not None or
                candidate.get("up_edge_interval_ns") is not None):
            errors.append("candidate exposed an interval for a rejected claim")
    for revision in ("baseline", "candidate"):
        if raw.get("valid_control", {}).get(revision, {}).get("status") != \
                "adapter_edge_brackets_paired":
            errors.append(f"{revision} rejected the untouched positive control")
    if raw.get("baseline_false_accept_count") != 20:
        errors.append("baseline false-accept count is not 20")
    if raw.get("candidate_false_accept_count") != 0:
        errors.append("candidate false-accept count is nonzero")

    result = {
        "status": "PASS_SAVED_RESULT_AUDIT" if not errors else
                  "FAIL_SAVED_RESULT_AUDIT",
        "errors": errors,
        "mutation_count": len(observed),
        "baseline_sample_false_accepts": len(baseline_false_accepts),
        "candidate_false_accepts": raw.get("candidate_false_accept_count"),
        "scope": "Saved raw/source consistency only; no runtime input or application effect.",
    }
    output = ROOT / "raw" / "AUDIT.json"
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                      encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
