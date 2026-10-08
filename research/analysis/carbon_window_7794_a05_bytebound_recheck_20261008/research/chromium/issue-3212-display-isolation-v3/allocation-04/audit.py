import hashlib
import json
from pathlib import Path

raw = Path("/out/raw.jsonl").read_bytes()
lines = raw.splitlines(keepends=True)
rows = [json.loads(line) for line in lines]
assert raw.endswith(b"\n") and len(rows) == 5
byte_gate = all(
    line.endswith(b"\n") and
    json.dumps(row, sort_keys=True, separators=(",", ":")).encode("utf-8") + b"\n" == line
    for row, line in zip(rows, lines)
)
pair, stale, decoy, p2, cleanup = rows
assert [r["event"] for r in rows] == [
    "generation_pair", "stale_xid_direct_input", "decoy_input_control",
    "p2_positive_control", "cleanup"
]
old, target, decoy_id = pair["old"], pair["p2"], pair["decoy"]
stale_reused_to_p2 = old["window"] == target["window"] and \
    stale["xid_owner_pid_after_transition"] == target["pid"]
stale_reused_to_decoy = old["window"] == decoy_id["window"] and \
    stale["xid_owner_pid_after_transition"] == decoy_id["pid"]
stale_effect = stale["decoy_title_after"] == "DECOY-3430-04-EFFECT-1" and \
    stale["decoy_title_after"] != stale["decoy_title_before"]
p2_stale_effect = stale["p2_title_after"].startswith("P2-3430-04-EFFECT-") and \
    stale["p2_title_after"] != stale["p2_title_before"]
decoy_effect_count_before = int(decoy["decoy_title_before"].rsplit("-", 1)[-1]) \
    if "-EFFECT-" in decoy["decoy_title_before"] else 0
decoy_effect_count_after = int(decoy["decoy_title_after"].rsplit("-", 1)[-1]) \
    if "-EFFECT-" in decoy["decoy_title_after"] else 0
p2_effect_count_before = int(p2["p2_title_before"].rsplit("-", 1)[-1]) \
    if "-EFFECT-" in p2["p2_title_before"] else 0
p2_effect_count_after = int(p2["p2_title_after"].rsplit("-", 1)[-1]) \
    if "-EFFECT-" in p2["p2_title_after"] else 0
gates = {
    "byte_gate": byte_gate,
    "independent_readiness_before_stale_send": (
        pair["ready_titles"]["old"] == "READY-P1-3430-04" and
        pair["ready_titles"]["p2"] == "READY-P2-3430-04" and
        pair["ready_titles"]["decoy"] == "READY-DECOY-3430-04" and
        stale["decoy_title_before"] == "READY-DECOY-3430-04" and
        stale["p2_title_before"] == "READY-P2-3430-04"
    ),
    "generation_changed": old["generation"] != target["generation"],
    "old_xid_reused_by_current_window": stale_reused_to_p2 or stale_reused_to_decoy,
    "old_xid_was_focused_before_send": stale["send"]["focused_window"] == old["window"] and not stale["send"]["send_skipped"],
    "stale_input_retargeted_p2": stale_reused_to_p2 and p2_stale_effect,
    "stale_input_retargeted_decoy": stale_reused_to_decoy and stale_effect,
    "decoy_control_effect": decoy_effect_count_after == decoy_effect_count_before + 1,
    "decoy_did_not_change_p2": decoy["p2_title_after"] == stale["p2_title_after"],
    "p2_positive_effect": p2_effect_count_after == p2_effect_count_before + 1,
    "cleanup_reaped": cleanup["all_processes_reaped"],
}
if (gates["stale_input_retargeted_p2"] or gates["stale_input_retargeted_decoy"]) and gates["independent_readiness_before_stale_send"]:
    decision = "FAIL_STALE_XID_RETARGETED_CURRENT_WINDOW"
elif gates["stale_input_retargeted_p2"] or gates["stale_input_retargeted_decoy"]:
    decision = "HOLD_READINESS_UNVERIFIED_STALE_EFFECT_OBSERVED"
elif all(gates.values()):
    decision = "HOLD_RAW_XID_ONLY_NO_ADMISSION_PATH"
else:
    decision = "HOLD_EFFECT_OR_CLEANUP_GATE"
print(json.dumps({"audit": decision, "rows": len(rows), "bytes": len(raw),
                  "sha256": hashlib.sha256(raw).hexdigest(), "gates": gates}, sort_keys=True))
