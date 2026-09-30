"""Raw-only decision audit; expected labels come from independent literal oracle."""
import hashlib
import json
from pathlib import Path

from oracle import audit

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    freeze = json.loads((HERE / "FREEZE.json").read_text())
    cases = json.loads((HERE / "cases.json").read_text())
    raw_path = HERE / "results" / "host-construction-01" / "RAW.json"
    raw = json.loads(raw_path.read_text())
    source_binding = all(sha(HERE / name) == expected for name, expected in freeze["formal_source_sha256"].items())
    input_binding = (raw.get("freeze_sha256") == sha(HERE / "FREEZE.json") and
                     raw.get("registry_sha256") == sha(HERE / "registry.json") and
                     raw.get("cases_sha256") == sha(HERE / "cases.json") and
                     raw.get("candidate_sha256") == sha(HERE / "candidate.py"))
    result = audit(cases, raw)
    result.update({
        "source_binding": source_binding,
        "input_binding": input_binding,
        "raw_sha256": sha(raw_path),
        "auditor_sha256": sha(HERE / "audit.py"),
        "disposition": result["disposition"] if source_binding and input_binding else "FAIL_BINDING",
    })
    out = raw_path.parent / "AUDIT.json"
    out.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    print(json.dumps({"disposition": result["disposition"], "case_count": result["case_count"], "errors": len(result["errors"]), "source_binding": source_binding, "input_binding": input_binding, "audit_sha256": sha(out)}, sort_keys=True))


if __name__ == "__main__":
    main()
