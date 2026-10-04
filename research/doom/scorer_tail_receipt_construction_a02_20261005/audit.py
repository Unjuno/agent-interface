"""Independent hash, receipt-count, and strict-result audit for A02."""
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DOOM = ROOT.parent


def audit():
    freeze = json.loads((ROOT / "FREEZE.json").read_text(encoding="utf-8"))
    errors = []
    for pin in freeze["sources"]:
        path = DOOM / Path(pin["path"]).name
        if not path.is_file():
            errors.append("missing_source:" + pin["path"])
            continue
        payload = path.read_bytes()
        blob = subprocess.run(["git", "hash-object", str(path)], capture_output=True,
                              text=True).stdout.strip()
        if blob != pin["git_blob"] or hashlib.sha256(payload).hexdigest() != pin["sha256"]:
            errors.append("source_pin:" + pin["path"])

    counts = {}
    for item in freeze["event_inputs"]:
        raw = subprocess.run(["git", "cat-file", "blob", item["git_blob"]],
                             capture_output=True, check=False).stdout
        if hashlib.sha256(raw).hexdigest() != item["sha256"]:
            errors.append("event_hash:" + item["cell"])
            continue
        events = [json.loads(line) for line in raw.decode("utf-8").splitlines()]
        counts[item["cell"]] = sum(
            row.get("event") == "input_release_transition" and row.get("key") == "d"
            for row in events)

    result = json.loads((ROOT / "RESULT.json").read_text(encoding="utf-8"))
    expected_counts = {"00-coast": 0, "01-pulse": 2, "02-pulse": 2,
                       "03-coast": 0, "04-coast": 0, "05-pulse": 2}
    if counts != expected_counts or result.get("release_counts") != expected_counts:
        errors.append("release_cardinality")
    if (result.get("verified_d_receipts_accepted") != 6 or
            result.get("zero_duration_tail_samples") != 0 or
            result.get("result") != "STRICT_RECEIPT_IDENTITY_COMPATIBLE_ZERO_SAMPLES"):
        errors.append("result_contract")
    if not all(result.get("negative_identity_controls_rejected", {}).values()):
        errors.append("negative_controls")
    if any(row.get("samples") != 0 or row.get("termination") != "deadline"
           or row.get("disposition") != "CENSORED"
           for row in result.get("receipts", [])):
        errors.append("censoring_contract")
    report = {
        "schema": "map01-scorer-tail-receipt-construction-audit-v2",
        "pass": not errors, "errors": errors,
        "cell_count": len(freeze["event_inputs"]),
        "accepted_receipts": result.get("verified_d_receipts_accepted"),
        "negative_controls_rejected": sum(result.get("negative_identity_controls_rejected", {}).values()),
        "scope": "pinned source/input and result accounting only; no live runtime audit",
    }
    (ROOT / "AUDIT.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n",
                                       encoding="utf-8")
    return report


if __name__ == "__main__":
    outcome = audit()
    print(json.dumps(outcome, indent=2, sort_keys=True))
    raise SystemExit(0 if outcome["pass"] else 1)
