#!/usr/bin/env python3
"""Raw-only auditor: does not import the runner or tested resolver."""
import copy
import hashlib
import json
import sys
from pathlib import Path

EXPECTED = [
    (0, "RAW_RETAINED_MAP", 0), (1, "SNAPSHOT_REFUSE_ON_CHANGE", 0),
    (2, "CURRENT_FRESH_MAP", 0), (3, "RAW_RETAINED_MAP", 1),
    (4, "SNAPSHOT_REFUSE_ON_CHANGE", 1), (5, "CURRENT_FRESH_MAP", 1),
]


def check(rows):
    errors = []
    if len(rows) != 6:
        errors.append("row_count")
    seen = set()
    for row in rows:
        spec = row.get("spec", {})
        key = (spec.get("index"), spec.get("policy"), spec.get("rep"))
        if key not in EXPECTED or key in seen:
            errors.append("schedule_identity")
        seen.add(key)
        if row.get("error") is not None:
            errors.append("runner_error")
            continue
        mp = row.get("mapping", {})
        if not mp.get("server_changed") or not mp.get("retained_map_stale"):
            errors.append("map_transition_not_observed")
        if mp.get("fresh_z_keycode") in (None, 0) or mp.get("retained_z_keycode") in (None, 0):
            errors.append("keycode_missing")
        policy = spec.get("policy")
        emitted = row.get("emission_requests", [])
        observed = row.get("server_events", [])
        if policy == "SNAPSHOT_REFUSE_ON_CHANGE":
            if row.get("decision") != "REFUSE_STALE_MAP" or emitted or observed:
                errors.append("snapshot_not_fail_closed")
        else:
            expected_code = mp.get("retained_z_keycode") if policy == "RAW_RETAINED_MAP" else mp.get("fresh_z_keycode")
            if row.get("decision") != "EMIT" or len(emitted) != 4 or len(observed) < 4:
                errors.append("emission_or_event_count")
            else:
                downs = [e for e in emitted if e.get("type") == "KeyPress"]
                ups = [e for e in emitted if e.get("type") == "KeyRelease"]
                if len(downs) != 2 or len(ups) != 2 or [e["detail"] for e in downs] != [mp.get("control_keycode"), expected_code]:
                    errors.append("emission_sequence")
                states = row.get("key_state_after_request", [])
                if len(states) != 4:
                    errors.append("key_state_sample_count")
                else:
                    for n, sample in enumerate(states):
                        expected_down = n < 2
                        if sample.get("target_down") != expected_down:
                            errors.append("target_state_transition")
                        if sample.get("control_down") != (n < 3):
                            errors.append("control_state_transition")
                if len(observed) < 4 or sorted(e.get("detail") for e in observed[:4]) != sorted(e.get("detail") for e in emitted):
                    errors.append("server_event_detail_mismatch")
        terminal = row.get("terminal_state", {})
        if not terminal.get("neutral"):
            errors.append("terminal_not_neutral")
        if not row.get("socket_absent_after_cleanup") or not row.get("auth_file_absent_after_cleanup"):
            errors.append("cleanup_incomplete")
        proc = row.get("process_receipts", {})
        if not proc.get("xvfb_reaped") or proc.get("xvfb_exit") not in (-15, 0):
            errors.append("xvfb_cleanup_receipt")
    if seen != set(EXPECTED):
        errors.append("missing_schedule_rows")
    return sorted(set(errors))


def main():
    root = Path(sys.argv[1])
    rows = []
    artifacts = {}
    for index, _, _ in EXPECTED:
        folder = root / f"case-{index}"
        raw = folder / "ROW.json"
        if not raw.is_file():
            print(json.dumps({"decision": "STOP_MISSING_RAW", "index": index}))
            raise SystemExit(2)
        blob = raw.read_bytes()
        artifacts[str(raw.relative_to(root))] = hashlib.sha256(blob).hexdigest()
        rows.append(json.loads(blob))
        log = folder / "xvfb.log"
        if log.exists():
            artifacts[str(log.relative_to(root))] = hashlib.sha256(log.read_bytes()).hexdigest()
    errors = check(rows)
    controls = {}
    mutations = [
        lambda x: x.pop(),
        lambda x: x[0]["spec"].update(index=5),
        lambda x: x[0].update(error="injected"),
        lambda x: x[0]["mapping"].update(server_changed=False),
        lambda x: x[1].update(emission_requests=[{"type":"KeyPress"}]),
        lambda x: x[2]["mapping"].update(fresh_z_keycode=0),
        lambda x: x[2].update(terminal_state={"neutral":False}),
        lambda x: x[4].update(socket_absent_after_cleanup=False),
        lambda x: x[0]["key_state_after_request"][2].update(target_down=True),
        lambda x: x[3]["process_receipts"].update(xvfb_reaped=False),
    ]
    for n, mutate in enumerate(mutations, 1):
        changed = copy.deepcopy(rows)
        mutate(changed)
        controls[str(n)] = bool(check(changed))
    result = {"decision": "PASS_XKB_CURRENT_MAP_BOUNDARY_SCOPED" if not errors and all(controls.values()) else "FAIL_AUDIT",
              "rows": len(rows), "errors": errors, "corruption_controls": controls,
              "corruption_rejections": sum(controls.values()), "artifacts_sha256": artifacts}
    (root / "AUDIT.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    print(json.dumps(result, sort_keys=True))
    if result["decision"] != "PASS_XKB_CURRENT_MAP_BOUNDARY_SCOPED":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
