from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

RETAINED = Path("research/live_control/results/integrated-efficiency-live-01")
DIRECT = ("preregistration.json", "report.json", "audit.json")
RESEARCH = Path("research/live_control")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inspect(root: Path) -> dict:
    root = root.resolve()
    result = {
        "schema": "golden-artifact-closure-check-v1",
        "root": str(root),
        "passed": False,
        "missing_direct_result_files": [],
        "missing_sources": [],
        "source_hash_mismatches": [],
        "source_matches": 0,
        "source_total": None,
    }
    for name in DIRECT:
        path = root / RETAINED / name
        if not path.is_file():
            result["missing_direct_result_files"].append(str(RETAINED / name))

    preregistration = root / RETAINED / "preregistration.json"
    if not preregistration.is_file():
        result["status"] = "FAIL_MISSING_PREREGISTRATION"
        return result
    try:
        plan = json.loads(preregistration.read_text(encoding="utf-8"))
        sources = plan["sources"]
        if not isinstance(sources, dict) or not sources:
            raise ValueError("nonempty sources mapping required")
    except Exception as error:
        result["status"] = "FAIL_INVALID_PREREGISTRATION"
        result["error"] = f"{type(error).__name__}: {error}"
        return result

    result["source_total"] = len(sources)
    for name, expected in sources.items():
        path = root / RESEARCH / name
        if not path.is_file():
            result["missing_sources"].append(str(RESEARCH / name))
            continue
        actual = sha256(path)
        if actual != expected:
            result["source_hash_mismatches"].append(
                {"path": str(RESEARCH / name), "expected": expected, "actual": actual}
            )
        else:
            result["source_matches"] += 1

    result["passed"] = not (
        result["missing_direct_result_files"]
        or result["missing_sources"]
        or result["source_hash_mismatches"]
    )
    result["status"] = (
        "PASS_GOLDEN_ARTIFACT_CLOSURE"
        if result["passed"]
        else "FAIL_GOLDEN_ARTIFACT_CLOSURE"
    )
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    result = inspect(args.root)
    encoded = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        with args.out.open("x", encoding="utf-8") as stream:
            stream.write(encoded)
    print(encoded, end="")
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
