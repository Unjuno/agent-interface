from __future__ import annotations

import ast
import hashlib
import json
import sys
from pathlib import Path

PACKET = Path(__file__).resolve().parent
FILES = (
    "run_cohort.py",
    "task_oracle_server.py",
    "source/fixture_app.py",
    "source/foreground_probe.py",
    "source/handshake_smoke.py",
    "source/scorer.py",
)


def main() -> int:
    conditions = json.loads((PACKET / "conditions.json").read_text(encoding="utf-8"))
    results = []
    for rel in FILES:
        path = PACKET / rel
        data = path.read_bytes()
        expected = conditions["source_hashes"][rel]
        actual = hashlib.sha256(data).hexdigest()
        if actual != expected:
            raise SystemExit(f"source hash mismatch: {rel}")
        ast.parse(data.decode("utf-8-sig"), filename=rel)
        compile(data, rel, "exec", optimize=sys.flags.optimize)
        results.append({"path": rel, "sha256": actual, "ast": "PASS", "compile": "PASS"})
    if len(conditions["trials"]) != 5 or [x["ordinal"] for x in conditions["trials"]] != [1, 2, 3, 4, 5]:
        raise SystemExit("frozen trial denominator/order invalid")
    if conditions["trial"] != conditions["trials"][0] or conditions["window_title"] != conditions["trials"][0]["window_title"]:
        raise SystemExit("top-level title/trial differs from first frozen attempt")
    mode = "optimized" if sys.flags.optimize else "normal"
    result = {"mode": mode, "optimize": sys.flags.optimize, "status": "PASS_R43_STATIC_PREFLIGHT", "files": results, "frozen_trials": 5}
    (PACKET / "raw" / f"static-preflight-{mode}.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
