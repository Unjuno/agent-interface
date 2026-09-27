"""Post-run independent audit of the immutable Issue #4580 evidence."""
import argparse
import json
from pathlib import Path
import shutil
import tempfile

import audit_v3


def audit_saved(root, source, freeze):
    root = Path(root)
    report_path = root / "FORMAL_RUN.json"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    if report.get("image_id") != freeze.get("runtime", {}).get("image_id"):
        raise ValueError("runtime_image_id")
    if report.get("formal_orchestrations") != 1 or report.get("retries") != 0:
        raise ValueError("formal_invocation_or_retry_count")
    if [x.get("seed") for x in report.get("seeds", [])] != audit_v3.SEEDS:
        raise ValueError("seed_schedule")
    with tempfile.TemporaryDirectory(prefix="needle-4580-audit-") as temp:
        audit_root = Path(temp) / "evidence"
        shutil.copytree(root, audit_root, ignore=shutil.ignore_patterns("AUDIT.json"))
        for rec in report["seeds"]:
            rec["run"] = rec["builder"]
        (audit_root / "FORMAL_RUN.json").write_text(
            json.dumps(report, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
        audit_freeze = dict(freeze)
        audit_freeze["image_id"] = freeze["runtime"]["image_id"]
        result = audit_v3.audit(audit_root, source, audit_freeze)
        (root / "AUDIT.json").write_text(
            json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
        return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True)
    parser.add_argument("--source", required=True)
    parser.add_argument("--freeze", required=True)
    args = parser.parse_args()
    result = audit_saved(args.root, args.source, json.loads(Path(args.freeze).read_text(encoding="utf-8")))
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    raise SystemExit(0 if not result["errors"] else 1)

