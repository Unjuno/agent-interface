"""Schema projection wrapper over the unchanged frozen raw auditor."""
import argparse
import json
from pathlib import Path

import auditor as frozen_auditor


def normalize_receipts(bundle):
    for record in bundle["messages"].values():
        response = record["json"]
        content = response.get("content", [])
        for block in content:
            if block.get("type") != "text":
                continue
            payload = json.loads(block["text"])
            if payload.get("schema") == "agent-interface/review-v1":
                receipt = payload.get("receipt", {})
                if receipt.get("schema") != "agent-interface/receipt-view-v1":
                    raise ValueError("PUBLIC_RECEIPT_V1_SCHEMA_MISMATCH")
                raw = receipt.get("source", {}).get("raw_report", {})
                if not isinstance(raw, dict):
                    raise ValueError("PUBLIC_RECEIPT_V1_RAW_REPORT_MISSING")
                payload["status"] = raw.get("status")
                payload["observation"] = raw
                payload["input_dispatched"] = raw.get("input_dispatched")
                payload["side_effect_authority"] = raw.get("side_effect_authority")
                payload["session"] = payload.get("session") or raw.get("session")
                block["text"] = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    for report in bundle["reports"].values():
        capture = report.get("observation")
        if (report.get("status") == "returned" and isinstance(capture, dict)
                and "target" in capture and "observation" not in capture):
            report["observation"] = {"status": report["status"], "observation": capture}
    return bundle


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--bundle", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    bundle = normalize_receipts(frozen_auditor.load_bundle(args.bundle))
    errors = frozen_auditor.audit_bundle(bundle)
    controls = {}
    for name, mutate in [
        ("divergent-session", lambda b: b["trace"]["calls"][1]["session"].update(session_id="tampered")),
        ("nonzero-input", lambda b: b["result"].update(input_operations=1)),
        ("missing-report", lambda b: b["reports"].pop(b["trace"]["calls"][0]["call_id"], None)),
        ("corrupt-image-payload", lambda b: b["messages"][b["trace"]["calls"][0]["response_file"]]["json"]["content"].__setitem__(1, {"type": "image", "data": "%%%"})),
    ]:
        import copy
        candidate = copy.deepcopy(bundle)
        mutate(candidate)
        controls[name] = bool(frozen_auditor.audit_bundle(candidate))
    output = {"decision": "PASS_RAW_AUDIT" if not errors and all(controls.values()) else "HOLD_RAW_AUDIT",
              "errors": errors, "corruption_controls_rejected": controls,
              "corruption_control_count": len(controls),
              "formal_allocation_decision": bundle["result"].get("decision"),
              "scope": "separate raw-only audit of formal02; never a formal input or dispatch"}
    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=False)
    raw = json.dumps(output, sort_keys=True, indent=2).encode() + b"\n"
    (out / "audit.json").write_bytes(raw)
    (out / "sha256.txt").write_text(frozen_auditor.hashlib.sha256(raw).hexdigest() + "  audit.json\n")
    print(json.dumps(output, sort_keys=True))
    return 0 if output["decision"] == "PASS_RAW_AUDIT" else 1


if __name__ == "__main__":
    raise SystemExit(main())
