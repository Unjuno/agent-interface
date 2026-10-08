"""Independent audit with call-ID-bound retained reads and transport scope."""
import json
from pathlib import Path

import auditor_effect_v2 as parent


def errors(bundle):
    found = parent.errors(bundle)
    if "retained-reads" in found:
        if retained_reads_valid(bundle):
            found.remove("retained-reads")
    return found


def retained_reads_valid(bundle):
    trace = bundle.get("trace", {})
    calls = trace.get("calls", [])
    transport = trace.get("retained_transport", {})
    read_rows = {row.get("source_label"): row for row in trace.get("retained_reads", [])}
    root = Path(bundle.get("bundle_path", ""))
    valid = (transport.get("scope") == "single-public-stdio-client-session"
             and transport.get("same_client_context") is True
             and transport.get("session_id") == trace.get("session_id")
             and transport.get("read_count") == len(parent.base.EXPECTED)
             and len(calls) == len(parent.base.EXPECTED))
    try:
        for call in calls:
            raw_path = root / "mcp-responses" / call["retained_response_file"]
            outer = json.loads(raw_path.read_bytes())
            texts = [row.get("text") for row in outer.get("content", [])
                     if row.get("type") == "text"]
            if len(texts) != 1:
                valid = False
                continue
            receipt = json.loads(texts[0])
            valid = valid and receipt.get("call_id") == call.get("payload", {}).get("call_id")
            valid = valid and receipt.get("retained_call", {}).get("state") == "finished"
            valid = valid and receipt.get("operation_invoked") is False
            retained = read_rows.get(call.get("label"), {})
            valid = valid and retained.get("session_id") == trace.get("session_id")
            valid = valid and retained.get("state") == receipt.get("retained_call", {}).get("state")
    except (OSError, KeyError, ValueError, TypeError):
        return False
    return valid


def audit(bundle):
    report = parent.base.audit(bundle)
    problems = errors(bundle)
    controls = dict(report.get("corruption_controls_rejected", {}))
    candidate = json.loads(json.dumps(bundle))
    candidate["trace"]["retained_transport"]["same_client_context"] = False
    controls["split-retained-transport"] = bool(errors(candidate))
    report.update(decision="PASS_RAW_AUDIT" if not problems and all(controls.values()) else "HOLD_RAW_AUDIT",
                  errors=problems, corruption_controls_rejected=controls,
                  corruption_control_count=len(controls),
                  scope="independent raw response and call-ID audit; retained reads bound to one stdio ClientSession")
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

