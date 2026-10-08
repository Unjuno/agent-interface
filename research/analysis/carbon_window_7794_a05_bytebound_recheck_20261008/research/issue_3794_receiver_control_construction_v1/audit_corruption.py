from __future__ import annotations

import hashlib
import json
import shutil
import sys
from pathlib import Path

from audit_formal import audit


def digest_tree(root: Path) -> str:
    h = hashlib.sha256()
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        h.update(path.relative_to(root).as_posix().encode() + b"\0")
        h.update(path.read_bytes())
    return h.hexdigest()


def main() -> int:
    source, output = Path(sys.argv[1]), Path(sys.argv[2])
    output.mkdir(parents=True, exist_ok=True)
    before = digest_tree(source)
    cases = []
    for name in ("wrong_decision", "missing_case", "changed_receiver_log"):
        target = output / name
        shutil.copytree(source, target)
        raw_path = target / "formal_raw.json"
        raw = json.loads(raw_path.read_text())
        if name == "wrong_decision":
            raw["decision"] = "FAIL_XKB_DELIVERY"
            raw_path.write_text(json.dumps(raw, indent=2, sort_keys=True, ensure_ascii=False) + "\n")
        elif name == "missing_case":
            raw["rows"].pop()
            raw_path.write_text(json.dumps(raw, indent=2, sort_keys=True, ensure_ascii=False) + "\n")
        else:
            log = target / "cases" / "de-00" / "xev.log"
            log.write_bytes(log.read_bytes() + b"\nCORRUPTED\n")
        result = audit(target)
        rejected = result["decision"] == "FAIL_INDEPENDENT_AUDIT" and bool(result["errors"])
        cases.append({"mutant": name, "rejected": rejected, "audit_errors": result["errors"]})
    after = digest_tree(source)
    unchanged = before == after
    report = {"decision": "PASS_AUDITOR_CORRUPTION_CONTROLS" if all(c["rejected"] for c in cases) and unchanged else "FAIL_AUDITOR_CORRUPTION_CONTROLS",
              "controls": cases, "raw_unchanged": unchanged, "raw_tree_sha256_before": before,
              "raw_tree_sha256_after": after}
    (output / "corruption_controls.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, sort_keys=True))
    return 0 if report["decision"] == "PASS_AUDITOR_CORRUPTION_CONTROLS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
