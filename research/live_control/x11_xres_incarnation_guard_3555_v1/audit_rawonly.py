from __future__ import annotations

import base64
import copy
import hashlib
import json
from pathlib import Path


PASS = "PASS_GENERATION_GUARD_REJECTED_STALE_ALIAS"
FAIL = "FAIL_GENERATION_GUARD_DID_NOT_REJECT_STALE_ALIAS"
HOLD = "HOLD_FORMAL_PRECONDITION_NOT_MET"
STOP = "HOLD_OR_STOP_UNCLASSIFIED"


def classify(raw: dict) -> str:
    pre = raw.get("preconditions")
    if not isinstance(pre, dict) or not pre or not all(v is True for v in pre.values()):
        return HOLD

    pixels = raw.get("independent_window_pixels", {})
    p1px, p2px = pixels.get("p1", {}), pixels.get("p2", {})
    try:
        b1 = base64.b64decode(p1px["base64"], validate=True)
        b2 = base64.b64decode(p2px["base64"], validate=True)
        pixel_ok = (p1px["size"] == p2px["size"] == [240, 160]
                    and len(b1) == len(b2) == 153600
                    and hashlib.sha256(b1).hexdigest() == p1px["sha256"]
                    and hashlib.sha256(b2).hexdigest() == p2px["sha256"]
                    and b1 == b2 and pixels.get("pixel_identical") is True)
    except (KeyError, TypeError, ValueError):
        pixel_ok = False

    old = raw.get("old_alias_guard", {})
    fresh = raw.get("fresh_control", {})
    captured = raw.get("old_handle", {}).get("owner_identity", {})
    current = raw.get("p2_owner_identity", {})
    fresh_owner = fresh.get("current_owner_identity", {})
    owner_ok = (
        captured.get("xres_version", [0, 0]) >= [1, 2]
        and current.get("xres_version", [0, 0]) >= [1, 2]
        and captured.get("xid") == current.get("xid") == raw.get("p1", {}).get("xid") == raw.get("p2", {}).get("xid")
        and captured.get("pid") == raw.get("p1", {}).get("pid")
        and current.get("pid") == raw.get("p2", {}).get("pid")
        and captured.get("pid_start_ticks") == raw.get("p1", {}).get("pid_start_ticks")
        and current.get("pid_start_ticks") == raw.get("p2", {}).get("pid_start_ticks")
        and captured.get("pid") != current.get("pid")
        and captured.get("pid_start_ticks") != current.get("pid_start_ticks")
        and fresh_owner.get("pid") == current.get("pid")
        and fresh_owner.get("pid_start_ticks") == current.get("pid_start_ticks")
    )
    fresh_result = fresh.get("result", {})
    execution = fresh_result.get("execution", {})
    releases = execution.get("releases")
    releases_ok = (isinstance(releases, list) and bool(releases)
                   and all(isinstance(r, dict) and r.get("verified") is True
                           and r.get("keys_down") == [] and r.get("buttons_down") == []
                           for r in releases))
    fresh_ok = (
        raw.get("fresh_control_attempts") == 1
        and fresh.get("permitted") is True
        and fresh.get("reason") == "SAME_PROCESS_INCARNATION"
        and fresh_result.get("status") == "completed"
        and fresh.get("emissions_after", -1) - fresh.get("emissions_before", 0) == 3
        and fresh.get("effect") == [1, 212, 118]
        and releases_ok
    )
    stale_block = (
        raw.get("old_guard_decisions") == 1
        and old.get("permitted") is False
        and old.get("reason") == "PROCESS_INCARNATION_MISMATCH"
        and old.get("bridge_click_invoked") is False
        and raw.get("bridge_old_click_invocations") == 0
        and old.get("emissions_before") == old.get("emissions_after") == 0
        and old.get("effect_before") == old.get("effect_after") == [0, 0, 0]
    )
    fail_observed = (
        raw.get("old_guard_decisions") == 1
        and old.get("permitted") is True
        and old.get("bridge_click_invoked") is True
        and raw.get("bridge_old_click_invocations") == 1
        and old.get("bridge_result", {}).get("status") == "completed"
        and old.get("emissions_after", 0) > old.get("emissions_before", 0)
        and old.get("effect_before") == [0, 0, 0]
        and old.get("effect_after") == [1, 109, 118]
        and raw.get("fresh_control_attempts") == 0
    )
    if pixel_ok and owner_ok and stale_block and fresh_ok:
        return PASS
    if pixel_ok and owner_ok and fail_observed:
        return FAIL
    return STOP


def corruption_controls(raw: dict) -> list[dict]:
    controls = []
    mutations = [
        ("xid-mismatch", lambda x: x["p2_owner_identity"].update(xid=-1)),
        ("same-pid", lambda x: x["p2_owner_identity"].update(pid=x["p1"]["pid"])),
        ("emission-not-zero", lambda x: x["old_alias_guard"].update(emissions_after=1)),
        ("effect-present", lambda x: x["old_alias_guard"].update(effect_after=[1, 109, 118])),
        ("missing-fresh-control", lambda x: x.update(fresh_control_attempts=0)),
        ("unverified-release", lambda x: x["fresh_control"]["result"]["execution"]["releases"][0].update(verified=False)),
        ("held-button-release", lambda x: x["fresh_control"]["result"]["execution"]["releases"][0].update(buttons_down=[1])),
        ("false-pass-on-failure", lambda x: (
            x["old_alias_guard"].update(permitted=True, bridge_click_invoked=True,
                                        bridge_result={"status": "completed"}, emissions_after=3,
                                        effect_before=[0, 0, 0], effect_after=[1, 109, 118]),
            x.update(bridge_old_click_invocations=1, fresh_control_attempts=0))),
    ]
    baseline = classify(raw)
    for name, mutate in mutations:
        altered = copy.deepcopy(raw)
        mutate(altered)
        detected = classify(altered) != baseline
        controls.append({"name": name, "detected": detected,
                         "mutated_disposition": classify(altered)})
    return controls


def main(raw_path: Path, out_path: Path) -> None:
    raw_bytes = raw_path.read_bytes()
    raw = json.loads(raw_bytes)
    controls = corruption_controls(raw)
    audit = {
        "audit": "PASS_INDEPENDENT_RAW_RECONSTRUCTION" if all(x["detected"] for x in controls) else "STOP_CORRUPTION_CONTROL_FAILED",
        "allocation_id": raw.get("allocation_id"),
        "candidate_decision": raw.get("decision"),
        "independent_decision": classify(raw),
        "raw_sha256": hashlib.sha256(raw_bytes).hexdigest(),
        "freeze_sha256_embedded_in_raw": raw.get("freeze_sha256"),
        "source_manifest_sha256_embedded_in_raw": raw.get("source_manifest_sha256"),
        "corruption_controls": controls,
    }
    out_path.write_text(json.dumps(audit, sort_keys=True, indent=2) + "\n")
    print(json.dumps(audit, sort_keys=True))


if __name__ == "__main__":
    import sys
    main(Path(sys.argv[1]), Path(sys.argv[2]))
