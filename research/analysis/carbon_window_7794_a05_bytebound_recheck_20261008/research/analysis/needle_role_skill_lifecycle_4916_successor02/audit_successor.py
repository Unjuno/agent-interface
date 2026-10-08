"""Run the predecessor's independent raw auditor with a pinned new allocation label."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

V1 = Path(__file__).resolve().parents[1] / "needle_role_skill_lifecycle_4916_v2"
OLD_ALLOCATION = "needle-role-skill-lifecycle-4916-v2-20260928-01"
NEW_ALLOCATION = "needle-role-skill-lifecycle-4916-v3-20260928-02"


def build_auditor_source() -> bytes:
    source = (V1 / "audit_result.py").read_bytes()
    old = OLD_ALLOCATION.encode()
    if source.count(old) != 1:
        raise ValueError("predecessor_allocation_literal_count")
    return source.replace(old, NEW_ALLOCATION.encode(), 1)


def _arg_path(name: str) -> Path:
    try:
        return Path(sys.argv[sys.argv.index(name) + 1])
    except (ValueError, IndexError) as exc:
        raise ValueError(f"missing_argument:{name}") from exc


def main() -> int:
    source = build_auditor_source()
    namespace = {"__name__": "frozen_independent_auditor", "__file__": str(V1 / "audit_result.py")}
    exec(compile(source, str(V1 / "audit_result.py"), "exec"), namespace)
    status = namespace["main"]()
    out_path = _arg_path("--out")
    report = json.loads(out_path.read_bytes())
    report["successor_auditor_wrapper_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    report["transformed_frozen_auditor_sha256"] = hashlib.sha256(source).hexdigest()
    out_path.write_text(json.dumps(report, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    return status


if __name__ == "__main__":
    raise SystemExit(main())
