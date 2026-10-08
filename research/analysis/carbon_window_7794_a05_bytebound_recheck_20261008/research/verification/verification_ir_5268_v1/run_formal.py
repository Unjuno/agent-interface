"""One-shot finite corpus runner for Issue #5268; no task input or external calls."""

import argparse
import hashlib
import json
import platform
from pathlib import Path

from candidate import lower_action


ROOT = Path(__file__).resolve().parent
SOURCES = (
    "candidate.py", "run_formal.py", "audit.py", "cases.json",
    "oracle_expected.json", "test_ir.py", "test_audit.py", "PLAN.md",
)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="FORMAL-01.json")
    args = parser.parse_args()
    output = Path(args.out)
    if output.exists():
        raise SystemExit("refusing to overwrite formal output")
    freeze = json.loads((ROOT / "FREEZE.json").read_text(encoding="utf-8"))
    fixtures = json.loads((ROOT / "cases.json").read_text(encoding="utf-8"))
    ids = [row["case_id"] for row in fixtures]
    if len(ids) != len(set(ids)):
        raise SystemExit("duplicate fixture identity")
    plans = [{"case_id": row["case_id"], "action": row["action"],
              "ir": lower_action(row["action"])} for row in fixtures]
    source_hashes = {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
                     for name in SOURCES}
    if source_hashes != freeze["source_sha256"]:
        raise SystemExit("source changed after freeze")
    result = {
        "allocation": freeze["allocation"],
        "base_sha": freeze["base_sha"],
        "formal_invocation": 1,
        "case_count": len(plans),
        "cases": plans,
        "source_sha256": source_hashes,
        "environment": {
            "python_version": platform.python_version(),
            "implementation": platform.python_implementation(),
            "platform": platform.platform(),
            "container_image": freeze["container_image"],
        },
        "status": "EXECUTED_ONCE_NO_VERDICT_PROMOTION",
    }
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"formal_output": str(output), "cases": len(plans),
                      "source_sha256": source_hashes, "status": result["status"]},
                     sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()
