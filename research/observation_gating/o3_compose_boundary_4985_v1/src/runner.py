from __future__ import annotations

import hashlib
import json
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "research/observation_gating/o3_relevant_region_successor_v1"))
sys.path.insert(0, str(ROOT / "research/observation_gating/o3_live_receipt_transport_2692_v1"))

# Import-only guard: any accidental live Xlib call fails immediately.
xlib = types.ModuleType("Xlib")
xmod = types.ModuleType("Xlib.X")
xmod.AnyPropertyType = 0
dmod = types.ModuleType("Xlib.display")
def forbidden_display(*args, **kwargs):
    raise RuntimeError("live X11 access forbidden")
dmod.Display = forbidden_display
xlib.X = xmod
xlib.display = dmod
sys.modules["Xlib"] = xlib
sys.modules["Xlib.X"] = xmod
sys.modules["Xlib.display"] = dmod

from gate import evaluate_region
from adapter import evaluate_delivery
from transport import digest, effect_reference
from research.observation_gating.o3_relevant_region_3131_v1.source_window_verifier import verify_source_window

SOURCE_PATHS = {
    "gate.py": ROOT / "research/observation_gating/o3_relevant_region_successor_v1/gate.py",
    "source_window_verifier.py": ROOT / "research/observation_gating/o3_relevant_region_3131_v1/source_window_verifier.py",
    "adapter.py": ROOT / "research/observation_gating/o3_live_receipt_transport_2692_v1/adapter.py",
    "transport.py": ROOT / "research/observation_gating/o3_live_receipt_transport_2692_v1/transport.py",
}
CASES = [
    ("same_int", 2097155, 2097155),
    ("same_string", "2097155", "2097155"),
    ("mixed_int_receipt_string_trusted", 2097155, "2097155"),
    ("mixed_string_receipt_int_trusted", "2097155", 2097155),
    ("unequal_int", 2097155, 2097156),
    ("unequal_string", "2097155", "02097155"),
    ("bool_equals_int", True, 1),
    ("float_equals_int", 1.0, 1),
]

def one_case(case_id, receipt_xid, trusted_xid):
    request = {"observation_id": "obs-fixed", "intent_epoch": 17, "region_id": "region-fixed",
               "max_receipt_age_ns": 100}
    trusted = {"xid": trusted_xid, "pid": 4242, "title": "fixture-window", "generation": "gen-fixed"}
    frame = b"fixed-full-frame"
    region = b"fixed-region-frame"
    region_sha = digest(region)
    receipt = {
        "observation_id": request["observation_id"], "intent_epoch": request["intent_epoch"],
        "region_id": request["region_id"], "source_window": receipt_xid,
        "source_pid": 4242, "source_title": "fixture-window", "source_generation": "gen-fixed",
        "capture_start_ns": 1000, "capture_end_ns": 1010, "focus_xid": 777,
        "focus_stable": True, "coverage": "COMPLETE", "freshness": "CURRENT",
        "effect_binding": "BOUND",
        "effect_binding_ref": effect_reference(request["observation_id"], request["intent_epoch"],
                                               request["region_id"], region_sha),
        "full_frame_sha256": digest(frame), "region_frame_sha256": region_sha,
        "authority_grants": 0, "ambiguous": False,
    }
    event = {"source_window_snapshot": {"focus_xid": 777}}
    gate = evaluate_region(receipt, observation_id=request["observation_id"],
                           intent_epoch=request["intent_epoch"], region_id=request["region_id"],
                           trusted_source_window=trusted_xid)
    bound, bind_reason = verify_source_window(receipt, trusted_xid)
    composed = evaluate_delivery(request, receipt, event, trusted, frame, region, 1020)
    return {
        "case_id": case_id,
        "receipt_xid": receipt_xid,
        "trusted_xid": trusted_xid,
        "receipt_type": type(receipt_xid).__name__,
        "trusted_type": type(trusted_xid).__name__,
        "direct_gate": {"admitted": gate.admitted, "reason": gate.reason},
        "source_verifier": {"admitted": bound, "reason": bind_reason},
        "adapter": composed,
    }

def main(out_path):
    rows = [one_case(*case) for case in CASES]
    source_hashes = {name: hashlib.sha256(path.read_bytes()).hexdigest()
                     for name, path in SOURCE_PATHS.items()}
    payload = {
        "schema": "o3-compose-boundary-4985-raw-v1",
        "issue": 4985,
        "main_commit": "7d1208cf323408897983ef2b5c75fd34f54d6815",
        "source_hashes": source_hashes,
        "rows": rows,
        "action_emissions_total": sum(row["adapter"]["action_emissions"] for row in rows),
        "gui_calls": 0, "model_calls": 0, "authority_grants": 0,
        "interpretation": "HOLD_CALLER_TYPE_CONTRACT",
    }
    Path(out_path).write_text(json.dumps(payload, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"issue": 4985, "rows": len(rows), "output": out_path}, sort_keys=True))

if __name__ == "__main__":
    main(sys.argv[1])

