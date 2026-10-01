"""Read-only auditor correction: enforce transport binding even on a clean base gate."""
import json

import auditor_effect_v3 as prior


def errors(bundle):
    found = prior.parent.errors(bundle)
    if not retained_binding_valid(bundle):
        if "retained-reads" not in found:
            found.append("retained-transport-binding")
    elif "retained-reads" in found:
        found.remove("retained-reads")
    return found


def retained_binding_valid(bundle):
    return prior.retained_reads_valid(bundle)


def audit(bundle):
    report = prior.parent.base.audit(bundle)
    problems = errors(bundle)
    controls = dict(report.get("corruption_controls_rejected", {}))

    candidate = json.loads(json.dumps(bundle))
    candidate["trace"]["effect_receipt"]["matched"] = False
    controls["persisted-effect-mutation"] = bool(errors(candidate))

    candidate = json.loads(json.dumps(bundle))
    candidate["trace"]["retained_transport"]["same_client_context"] = False
    controls["split-retained-transport"] = bool(errors(candidate))

    candidate = json.loads(json.dumps(bundle))
    candidate["trace"]["calls"][0]["payload"]["call_id"] = "mutated-call-id"
    controls["retained-call-id-mismatch"] = bool(errors(candidate))

    report.update(decision="PASS_RAW_AUDIT" if not problems and all(controls.values()) else "HOLD_RAW_AUDIT",
                  errors=problems, corruption_controls_rejected=controls,
                  corruption_control_count=len(controls),
                  scope="independent offline raw audit; retained reads bound by call ID and one stdio transport")
    return report


def main():
    import argparse
    import hashlib
    from pathlib import Path
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

