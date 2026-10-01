"""Independent raw-only verifier for the Issue #5236 three-row receipt."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from pathlib import Path

EXPECTED_ROWS = ("control_us", "jp_to_us", "us_to_jp")


def verify(raw: dict) -> str:
    server = raw.get("xvfb")
    if (not isinstance(server, dict) or server.get("exit") != 0
            or server.get("cleanup_action") != "terminate" or not server.get("display")):
        raise ValueError("missing private Xvfb lifecycle evidence")
    rows = raw.get("rows")
    if not isinstance(rows, list) or tuple(r.get("row") for r in rows) != EXPECTED_ROWS:
        raise ValueError("row omission/order/identity mismatch")
    effects = []
    for row in rows:
        if row.get("status") != "row_complete":
            raise ValueError("incomplete row")
        receipt = row.get("receipt")
        if not isinstance(receipt, dict):
            raise ValueError("missing dispatch receipt")
        releases = receipt.get("execution", {}).get("releases") or ([receipt["release"]] if isinstance(receipt.get("release"), dict) else [])
        if receipt.get("status") not in ("completed", "refused") or not releases:
            raise ValueError("missing status/release evidence")
        if any(r.get("verified") is not True or r.get("keys_down") != [] or r.get("buttons_down") != [] for r in releases):
            raise ValueError("unverified release")
        if row["row"] == "control_us":
            if row.get("actor_argv") is not None or row.get("actor_exit") is not None or row.get("actor_receipt") is not None:
                raise ValueError("control has remap actor")
        else:
            target = {"jp_to_us": "us", "us_to_jp": "jp"}[row["row"]]
            actor = row.get("actor_argv")
            actor_receipt = row.get("actor_receipt")
            wait = receipt.get("execution", {}).get("waits", [])
            if (not isinstance(actor, list) or row.get("actor_exit") != 0
                    or not isinstance(actor_receipt, dict) or actor_receipt.get("exit") != 0
                    or actor_receipt.get("target_layout") != target or len(wait) != 1
                    or not (wait[0]["started_ns"] <= actor_receipt["started_ns"] <= actor_receipt["ended_ns"] <= wait[0]["ended_ns"])):
                raise ValueError("missing/failed remap actor receipt")
            if row.get("actor_target") != target:
                raise ValueError("actor target does not match row")
        final_layout = {"control_us": "us", "jp_to_us": "us", "us_to_jp": "jp"}[row["row"]]
        if row.get("layout_initial_exit") != 0 or row.get("layout_after_exit") != 0:
            raise ValueError("layout readback command failed")
        if not re.search(rf"(?m)^layout:\s*{re.escape(row.get('initial_layout', ''))}\s*$", row.get("layout_initial_stdout", "")):
            raise ValueError("initial layout readback mismatch")
        if not re.search(rf"(?m)^layout:\s*{final_layout}\s*$", row.get("layout_after_stdout", "")):
            raise ValueError("final layout readback mismatch")
        expected = row.get("expected_effect_hex")
        actual = row.get("saved_effect_hex")
        if receipt["status"] == "refused":
            if actual is not None:
                raise ValueError("refused row has saved effect")
            effects.append("refused")
        elif actual != expected:
            return "FAIL_STALE_MAP_EFFECT" if row["row"] != "control_us" else "FAIL_CONTROL_EFFECT"
        else:
            effects.append("exact")
    if effects[0] != "exact":
        return "FAIL_CONTROL_EFFECT"
    if effects[1:] == ["refused", "refused"]:
        return "PASS_MIDPROGRAM_REMAP_FAIL_CLOSED"
    if effects[1:] == ["exact", "exact"]:
        return "NO_STALE_EFFECT_OBSERVED"
    if "refused" in effects[1:]:
        return "STOP_MIXED_REMAP_DISPOSITION"
    return "FAIL_STALE_MAP_EFFECT"


def main() -> int:
    source, destination = map(Path, sys.argv[1:3])
    try:
        outcome = verify(json.loads(source.read_text(encoding="utf-8")))
        report = {"decision": outcome, "errors": []}
    except Exception as exc:
        report = {"decision": "STOP_PROVENANCE_OR_RUNNER", "errors": [repr(exc)]}
    destination.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, sort_keys=True))
    return 0 if not report["errors"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
