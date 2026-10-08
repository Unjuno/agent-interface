from __future__ import annotations

import hashlib
import json
from pathlib import Path

BASE = "f65b39b6434714a08dfa743f8f16f5cae1667f6d"
SOURCES = {
    "runtime/backends/x11_v1/backend.py": "7d996e90831c12227243393c20565d884605e088",
    "runtime/backends/x11_v1/fixture_app.py": "11c30cf084744ffdba3b00df7637b5853c8571ac",
    "runtime/backends/x11_v1/session.py": "4dbd6dd219e2ec7313cd32d3e4cb154e0efcfbb1",
}
EXPECTED = "http://a_b"
WAIT_MS = 900
CASES = (("control_us", "us", None), ("jp_to_us", "jp", "us"),
         ("us_to_jp", "us", "jp"))


def _read(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def audit(root: Path) -> dict:
    root = Path(root)
    errors = []
    try:
        summary = _read(root / "summary.json")
    except Exception as error:
        return {"decision": "STOP_PROVENANCE_OR_RUNNER", "errors": [f"summary:{error!r}"]}
    if summary.get("allocation_id") != "ISSUE5236-UBUNTU-WSL-20260928-01":
        errors.append("allocation_id")
    if summary.get("base") != BASE or summary.get("sources") != SOURCES:
        errors.append("source_identity")
    cases = summary.get("cases")
    expected_ids = [row[0] for row in CASES]
    if not isinstance(cases, list) or [row.get("case_id") for row in cases] != expected_ids:
        errors.append("case_order_or_cardinality")
        cases = cases if isinstance(cases, list) else []
    if summary.get("run_error"):
        errors.append("runner_error")

    effects = {}
    statuses = {}
    for index, (case_id, initial, target) in enumerate(CASES):
        if index >= len(cases) or not isinstance(cases[index], dict):
            errors.append(f"missing_row:{case_id}")
            continue
        row = cases[index]
        try:
            if row != _read(root / case_id / "case.json"):
                errors.append(f"summary_row_mismatch:{case_id}")
        except Exception:
            errors.append(f"case_record_missing:{case_id}")
        if row.get("case_id") != case_id:
            errors.append(f"case_id:{case_id}")
        if row.get("initial_layout_requested") != initial or row.get("target_layout") != target:
            errors.append(f"layout_assignment:{case_id}")
        if row.get("initial_layout", {}).get("layout") != initial:
            errors.append(f"initial_layout_receipt:{case_id}")
        if row.get("final_layout", {}).get("layout") != (target or initial):
            errors.append(f"final_layout_receipt:{case_id}")
        for name, record in (("initial", row.get("initial_symbol_map", {})),
                             ("actor", row.get("actor", {}).get("symbol_map", {}))):
            if name == "actor" and target is None:
                continue
            symbols = record.get("symbol_keycodes", {})
            if record.get("returncode") != 0 or any(not symbols.get(char) for char in ("_", "/", ":")):
                errors.append(f"{name}_symbol_map_receipt:{case_id}")
        try:
            process = _read(root / case_id / "processes.json")
            if process != {"app_exit": row.get("app_exit"), "xvfb_exit": row.get("xvfb_exit"),
                           "socket_absent_after_cleanup": row.get("socket_absent_after_cleanup")}:
                errors.append(f"process_receipt_mismatch:{case_id}")
            if row.get("app_exit") is None or row.get("xvfb_exit") is None or row.get("socket_absent_after_cleanup") is not True:
                errors.append(f"process_cleanup:{case_id}")
        except Exception:
            errors.append(f"process_receipt_missing:{case_id}")

        actor = row.get("actor", {})
        if target is None:
            if actor.get("scheduled") is not False:
                errors.append("unexpected_control_actor")
        else:
            if (actor.get("scheduled") is not True or actor.get("returncode") != 0
                    or actor.get("final_layout", {}).get("layout") != target):
                errors.append(f"actor_receipt:{case_id}")
            wait_rows = [wait for wait in row.get("waits", [])
                         if wait.get("requested_ms") == WAIT_MS and wait.get("completed") is True]
            if len(wait_rows) != 1:
                errors.append(f"wait_receipt:{case_id}")
            else:
                wait = wait_rows[0]
                if not (wait["started_ns"] <= actor.get("started_ns", -1)
                        <= actor.get("ended_ns", -1) <= wait["ended_ns"]):
                    errors.append(f"actor_outside_wait:{case_id}")
                if not (row.get("dispatch_started_ns", -1) <= wait["started_ns"]
                        < wait["ended_ns"] <= row.get("dispatch_ended_ns", -1)):
                    errors.append(f"wait_outside_dispatch:{case_id}")
        dispatch = row.get("dispatch", {})
        status = dispatch.get("status")
        statuses[case_id] = status
        if row.get("expected_text") != EXPECTED or row.get("wait_ms") != WAIT_MS:
            errors.append(f"expected_contract:{case_id}")
        if row.get("effect_present"):
            try:
                raw = (root / case_id / "effect.json").read_bytes()
                digest = hashlib.sha256(raw).hexdigest()
                decoded = raw.decode("utf-8")
                effect = json.loads(decoded)
                if digest != row.get("effect_sha256") or decoded != row.get("effect_bytes_utf8"):
                    errors.append(f"effect_digest_or_bytes:{case_id}")
                if effect.get("saved") is not True:
                    errors.append(f"effect_not_saved:{case_id}")
                effects[case_id] = effect.get("text")
            except Exception:
                errors.append(f"effect_file_missing_or_invalid:{case_id}")
        else:
            if row.get("effect_sha256") is not None or row.get("effect_bytes_utf8") is not None:
                errors.append(f"effect_absence_receipt:{case_id}")
            effects[case_id] = None
        releases = row.get("releases")
        if isinstance(releases, dict):
            releases = [releases]
        if status == "completed":
            execution = dispatch.get("execution", {})
            if not (isinstance(releases, list) and releases and releases[-1].get("verified") is True
                    and releases[-1].get("keys_down") == [] and releases[-1].get("buttons_down") == []):
                errors.append(f"release_not_verified:{case_id}")
            if 6 not in execution.get("completed_ops", []):
                errors.append(f"suffix_op_not_completed:{case_id}")
        elif status == "refused":
            if dispatch.get("input_dispatched") is True or row.get("program_emissions") not in (None, 0):
                errors.append(f"refusal_after_input:{case_id}")
        else:
            errors.append(f"unexpected_dispatch_status:{case_id}")

    if statuses.get("control_us") != "completed" or effects.get("control_us") != EXPECTED:
        errors.append("control_not_exact")
    remap_rows = ["jp_to_us", "us_to_jp"]
    safe_refusals = all(statuses.get(case_id) == "refused" and effects.get(case_id) in (None, EXPECTED)
                        for case_id in remap_rows)
    exact_completions = all(statuses.get(case_id) == "completed" and effects.get(case_id) == EXPECTED
                            for case_id in remap_rows)
    wrong_completed = any(statuses.get(case_id) == "completed" and effects.get(case_id) != EXPECTED
                          for case_id in remap_rows)
    if errors:
        decision = "STOP_PROVENANCE_OR_RUNNER"
    elif wrong_completed:
        decision = "FAIL_STALE_MAP_EFFECT"
    elif safe_refusals:
        decision = "PASS_MIDPROGRAM_REMAP_FAIL_CLOSED"
    elif exact_completions:
        decision = "NO_STALE_EFFECT_OBSERVED"
    else:
        decision = "HOLD_MIXED_REMAP_OUTCOME"
    return {"decision": decision, "errors": errors, "case_count": len(cases),
            "statuses": statuses, "effects": effects}


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--audit-output", type=Path, required=True)
    args = parser.parse_args()
    result = audit(args.root)
    args.audit_output.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return 0 if result["decision"] != "STOP_PROVENANCE_OR_RUNNER" else 2


if __name__ == "__main__":
    raise SystemExit(main())
