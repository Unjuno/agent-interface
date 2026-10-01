"""Independent raw-only successor gate including persisted effect receipt."""
import json
import hashlib
from pathlib import Path

import auditor_effect as base


def errors(bundle):
    out = base.errors(bundle)
    root = Path(bundle.get("bundle_path", ""))
    for call in bundle.get("trace", {}).get("calls", []):
        retained_name = call.get("retained_response_file")
        if not retained_name:
            continue
        try:
            raw = (root / "mcp-responses" / retained_name).read_bytes()
            outer = json.loads(raw)
            blocks = [item.get("text") for item in outer.get("content", []) if item.get("type") == "text"]
            if (hashlib.sha256(raw).hexdigest() != call.get("retained_response_metadata", {}).get("response_sha256")
                    or len(blocks) != 1
                    or json.loads(blocks[0]) != call.get("retained_payload")):
                out.append("retained-read-raw-byte-binding")
        except (OSError, ValueError, TypeError):
            out.append("retained-read-raw-byte-binding")
    try:
        receipt = json.loads((root / "effect_receipt.json").read_text(encoding="utf-8"))
        trace_receipt = bundle.get("trace", {}).get("effect_receipt", {})
        if receipt != trace_receipt:
            out.append("effect-receipt-disk-binding")
        if receipt.get("matched") is not True:
            out.append("persisted-effect-unmatched")
    except (OSError, ValueError, TypeError):
        out.append("persisted-effect-missing-or-invalid")
    if "retained-reads" in out:
        trace = bundle.get("trace", {})
        calls = trace.get("calls", [])
        raw_rows = []
        try:
            for call in calls:
                path = root / "mcp-responses" / call["retained_response_file"]
                outer = json.loads(path.read_bytes())
                blocks = [row.get("text") for row in outer.get("content", [])
                          if row.get("type") == "text"]
                if len(blocks) != 1:
                    raise ValueError("retained-text-block-count")
                raw_rows.append(json.loads(blocks[0]))
            session_id = trace.get("session_id")
            valid = len(raw_rows) == len(base.EXPECTED)
            for row in raw_rows:
                valid = valid and row.get("retained_call", {}).get("state") == "finished"
                valid = valid and row.get("operation_invoked") is False
                raw_session = (row.get("session_id") or row.get("session", {}).get("session_id")
                               or row.get("report", {}).get("session", {}).get("session_id"))
                valid = valid and raw_session == session_id
            if valid:
                out.remove("retained-reads")
        except (OSError, KeyError, ValueError, TypeError):
            pass
    return out


def audit(bundle):
    report = base.audit(bundle)
    problems = errors(bundle)
    controls = dict(report.get("corruption_controls_rejected", {}))
    candidate = json.loads(json.dumps(bundle))
    candidate["trace"]["effect_receipt"]["matched"] = False
    controls["persisted-effect-mutation"] = bool(errors(candidate))
    report.update(decision="PASS_RAW_AUDIT" if not problems and all(controls.values()) else "HOLD_RAW_AUDIT",
                  errors=problems, corruption_controls_rejected=controls,
                  corruption_control_count=len(controls),
                  scope="independent raw-only reconstruction including persisted effect receipt")
    return report


def main():
    import argparse
    import hashlib
    parser = argparse.ArgumentParser()
    parser.add_argument("--bundle", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    root = Path(args.bundle)
    bundle = {"trace": json.loads((root / "trace.json").read_text(encoding="utf-8")),
              "result": json.loads((root / "result.json").read_text(encoding="utf-8")),
              "app_identities": json.loads((root / "app-identities.json").read_text(encoding="utf-8")),
              "bundle_path": str(root)}
    report = audit(bundle)
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=False)
    raw = json.dumps(report, sort_keys=True, indent=2).encode() + b"\n"
    (output / "audit.json").write_bytes(raw)
    (output / "sha256.txt").write_text(hashlib.sha256(raw).hexdigest() + "  audit.json\n")
    print(json.dumps(report, sort_keys=True))
    return 0 if report["decision"] == "PASS_RAW_AUDIT" else 1


if __name__ == "__main__":
    raise SystemExit(main())

