from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import secrets
import subprocess
import time

from Xlib import X, display

from typed_validator_881 import EXACT_MATCH, INVALID, MISMATCH, classify


DISPLAY_NUM = 149
SOCKET = Path(f"/tmp/.X11-unix/X{DISPLAY_NUM}")
EVIDENCE = Path("/evidence")


def pid_start_ticks(pid: int) -> str:
    text = Path(f"/proc/{pid}/stat").read_text(encoding="ascii")
    end = text.rfind(")")
    if end < 0:
        raise RuntimeError("malformed proc stat")
    fields = text[end + 1 :].split()
    return fields[19]  # proc field 22 (starttime), after pid and comm


def start_xvfb(generation: str) -> tuple[subprocess.Popen, display.Display, dict]:
    if SOCKET.exists():
        raise RuntimeError("fixed display socket already exists")
    proc = subprocess.Popen(
        ["Xvfb", f":{DISPLAY_NUM}", "-screen", "0", "640x480x24", "-nolisten", "tcp", "-ac"],
        stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
    )
    start_ticks = pid_start_ticks(proc.pid)
    deadline = time.monotonic() + 8
    while time.monotonic() < deadline:
        if proc.poll() is not None:
            err = proc.stderr.read().decode("utf-8", "replace")
            raise RuntimeError(f"Xvfb exited before socket appeared: {err}")
        if SOCKET.exists():
            break
        time.sleep(0.02)
    if not SOCKET.exists():
        proc.terminate()
        proc.wait(timeout=3)
        raise RuntimeError("Xvfb socket did not appear")
    token = secrets.token_hex(32)
    display_conn = display.Display(f":{DISPLAY_NUM}")
    root = display_conn.screen().root
    server_info = {
        "generation": generation,
        "display": f":{DISPLAY_NUM}",
        "xvfb_pid": proc.pid,
        "xvfb_start_ticks": start_ticks,
        "server_instance_id": token,
        "socket_path": str(SOCKET),
        "socket_present_after_start": SOCKET.exists(),
    }
    return proc, display_conn, server_info


def create_fixture(d: display.Display) -> tuple[dict, object]:
    root = d.screen().root
    window = root.create_window(20, 20, 100, 60, 1, d.screen().root_depth,
                                X.InputOutput, X.CopyFromParent)
    window.set_wm_name("typed-recovery-lifetime")
    window.set_wm_class("typed-recovery-lifetime", "TypedRecoveryFixture")
    window.map()
    d.sync()
    geometry = window.get_geometry()
    transient_atom = d.intern_atom("WM_TRANSIENT_FOR")
    transient_property = window.get_full_property(transient_atom, X.AnyPropertyType)
    if transient_property is None:
        transient = {"state": "KNOWN_NULL"}
    else:
        transient = {"state": "KNOWN", "value": int(transient_property.value[0])}
    identity = {
        "backend": {"state": "KNOWN", "value": "x11"},
        "top_level_client_id": {"state": "KNOWN", "value": int(window.id)},
        "transient_for": transient,
    }
    context = {
        "root_xid": int(root.id),
        "top_level_xid": int(window.id),
        "geometry": [int(geometry.x), int(geometry.y), int(geometry.width), int(geometry.height)],
        "wm_name": window.get_wm_name(),
        "wm_class": list(window.get_wm_class() or []),
        "transient_property_present": transient_property is not None,
    }
    return {"identity": identity, "context": context}, window


def reread_fixture(d: display.Display, window_id: int) -> dict:
    window = d.create_resource_object("window", window_id)
    geometry = window.get_geometry()
    transient_atom = d.intern_atom("WM_TRANSIENT_FOR")
    prop = window.get_full_property(transient_atom, X.AnyPropertyType)
    transient = ({"state": "KNOWN_NULL"} if prop is None else
                 {"state": "KNOWN", "value": int(prop.value[0])})
    return {
        "identity": {
            "backend": {"state": "KNOWN", "value": "x11"},
            "top_level_client_id": {"state": "KNOWN", "value": int(window_id)},
            "transient_for": transient,
        },
        "geometry": [int(geometry.x), int(geometry.y), int(geometry.width), int(geometry.height)],
    }


def make_receipt(identity: dict, token: str) -> dict:
    return {
        "receipt_id": secrets.token_hex(16),
        "identity": identity,
        "server_instance_id": token,
        "authority": "none",
        "task_input_granted": False,
        "action_admission_eligible": False,
    }


def lifetime_classify(receipt: dict, current: dict, observed_token: str, registry: dict) -> dict:
    issued_token = registry.get(receipt.get("receipt_id"))
    if issued_token is None:
        return {"classification": "REJECT", "reason": "unknown_receipt"}
    if receipt.get("server_instance_id") != issued_token:
        return {"classification": "REJECT", "reason": "receipt_token_forged_or_changed"}
    if issued_token != observed_token:
        return {"classification": "REJECT", "reason": "server_instance_mismatch"}
    typed = classify(receipt, current)
    return {"classification": "ACCEPT" if typed["classification"] == EXACT_MATCH else "REJECT",
            "reason": typed["reason"], "typed_classification": typed["classification"]}


def stop_xvfb(proc: subprocess.Popen, d: display.Display, window) -> dict:
    try:
        window.destroy()
        d.sync()
    finally:
        d.close()
    proc.terminate()
    proc.wait(timeout=5)
    deadline = time.monotonic() + 5
    while SOCKET.exists() and time.monotonic() < deadline:
        time.sleep(0.02)
    stderr = proc.stderr.read().decode("utf-8", "replace")
    return {
        "exit_observed": proc.poll() is not None,
        "exit_code": proc.returncode,
        "socket_disappeared": not SOCKET.exists(),
        "stderr": stderr,
    }


def run() -> dict:
    if any(EVIDENCE.iterdir()):
        raise RuntimeError("formal evidence directory is not empty")
    rows, pairs, controls, issued_receipts = [], [], [], []
    for rep in range(4):
        p1, d1, g1 = start_xvfb(f"r{rep}-G1")
        a1, w1 = create_fixture(d1)
        # Re-read the same live window; no extra window or task operation.
        reread_g1 = reread_fixture(d1, int(w1.id))
        current_g1 = reread_g1["identity"]
        same_r1 = make_receipt(a1["identity"], g1["server_instance_id"])
        same_r2 = make_receipt(a1["identity"], g1["server_instance_id"])
        registry = {same_r1["receipt_id"]: g1["server_instance_id"],
                    same_r2["receipt_id"]: g1["server_instance_id"]}
        issued_receipts.extend([
            {"receipt_id": same_r1["receipt_id"], "server_instance_id": g1["server_instance_id"]},
            {"receipt_id": same_r2["receipt_id"], "server_instance_id": g1["server_instance_id"]},
        ])
        typed_same = classify(same_r1, current_g1)
        bound_same = lifetime_classify(same_r2, current_g1, g1["server_instance_id"], registry)
        rows.extend([
            {"rep": rep, "case": "same_generation", "policy": "CURRENT_TYPED",
             "typed": typed_same, "bound": "ACCEPT", "receipt": same_r1,
             "current_identity": current_g1, "server_instance_id": g1["server_instance_id"]},
            {"rep": rep, "case": "same_generation", "policy": "LIFETIME_BOUND",
             "typed": classify(same_r2, current_g1), "bound_result": bound_same,
             "bound": bound_same["classification"], "receipt": same_r2,
             "current_identity": current_g1, "server_instance_id": g1["server_instance_id"]},
        ])
        g1_witness = {**g1, "identity": a1["identity"], "context": a1["context"],
                      "identity_reread_top_level_xid": int(w1.id),
                      "identity_reread": reread_g1["identity"],
                      "geometry_reread": reread_g1["geometry"],
                      "same_generation_requery_equal": a1["identity"] == reread_g1["identity"]}
        g1_cleanup = stop_xvfb(p1, d1, w1)

        p2, d2, g2 = start_xvfb(f"r{rep}-G2")
        a2, w2 = create_fixture(d2)
        stale_r1 = {**same_r1}
        stale_r2 = {**same_r2}
        typed_cross = classify(stale_r1, a2["identity"])
        bound_cross = lifetime_classify(stale_r2, a2["identity"], g2["server_instance_id"], registry)
        rows.extend([
            {"rep": rep, "case": "cross_generation_stale", "policy": "CURRENT_TYPED",
             "typed": typed_cross, "bound": "ACCEPT" if typed_cross["classification"] == EXACT_MATCH else "REJECT",
             "receipt": stale_r1, "current_identity": a2["identity"],
             "server_instance_id": g2["server_instance_id"]},
            {"rep": rep, "case": "cross_generation_stale", "policy": "LIFETIME_BOUND",
             "typed": classify(stale_r2, a2["identity"]), "bound_result": bound_cross,
             "bound": bound_cross["classification"], "receipt": stale_r2,
             "current_identity": a2["identity"], "server_instance_id": g2["server_instance_id"]},
        ])

        forged = {**stale_r1, "server_instance_id": g2["server_instance_id"]}
        missing = {k: v for k, v in stale_r1.items() if k != "server_instance_id"}
        unknown_receipt = {**stale_r1, "receipt_id": "0" * 32}
        escalated = {**stale_r1, "authority": "task-input", "task_input_granted": True}
        changed_backend = {**stale_r1, "identity": {**stale_r1["identity"],
                            "backend": {"state": "KNOWN", "value": "win32"}}}
        changed_client = {**stale_r1, "identity": {**stale_r1["identity"],
                            "top_level_client_id": {"state": "KNOWN", "value": 0xDEAD}}}
        changed_transient = {**stale_r1, "identity": {**stale_r1["identity"],
                               "transient_for": {"state": "KNOWN", "value": 123}}}
        control_cases = [
            ("forged_server_token", lifetime_classify(forged, a2["identity"], g2["server_instance_id"], registry), "REJECT"),
            ("missing_server_token", lifetime_classify(missing, a2["identity"], g2["server_instance_id"], registry), "REJECT"),
            ("unknown_receipt_id", lifetime_classify(unknown_receipt, a2["identity"], g2["server_instance_id"], registry), "REJECT"),
            ("authority_escalation", classify(escalated, a2["identity"]), INVALID),
            ("changed_backend", classify(changed_backend, a2["identity"]), MISMATCH),
            ("changed_client_id", classify(changed_client, a2["identity"]), MISMATCH),
            ("known_transient_mismatch", classify(changed_transient, a2["identity"]), MISMATCH),
        ]
        controls.extend({"rep": rep, "name": name, "observed": observed,
                         "expected": expected,
                         "detected": observed.get("classification") == expected}
                        for name, observed, expected in control_cases)
        g2_witness = {**g2, "identity": a2["identity"], "context": a2["context"]}
        g2_cleanup = stop_xvfb(p2, d2, w2)
        pairs.append({"rep": rep, "g1": g1_witness, "g1_cleanup": g1_cleanup,
                      "g2": g2_witness, "g2_cleanup": g2_cleanup,
                      "same_xid": g1_witness["context"]["top_level_xid"] == g2_witness["context"]["top_level_xid"],
                      "same_root_xid": g1_witness["context"]["root_xid"] == g2_witness["context"]["root_xid"],
                      "core_identity_equal": a1["identity"] == a2["identity"],
                      "server_tokens_distinct": g1["server_instance_id"] != g2["server_instance_id"]})

    pass_gate = (
        len(rows) == 16 and len(pairs) == 4 and all(p["same_xid"] and p["same_root_xid"]
        and p["core_identity_equal"] and p["server_tokens_distinct"]
        and p["g1_cleanup"]["exit_observed"] and p["g1_cleanup"]["socket_disappeared"]
        and p["g2_cleanup"]["exit_observed"] and p["g2_cleanup"]["socket_disappeared"] for p in pairs)
        and all(r["typed"]["classification"] == EXACT_MATCH for r in rows if r["policy"] == "CURRENT_TYPED")
        and all(r["typed"]["classification"] == EXACT_MATCH for r in rows if r["policy"] == "LIFETIME_BOUND")
        and all(r["bound"] == ("ACCEPT" if r["case"] == "same_generation" else "REJECT") for r in rows if r["policy"] == "LIFETIME_BOUND")
        and len(controls) == 28 and all(c["detected"] for c in controls)
    )
    if not all(p["same_xid"] and p["same_root_xid"] and p["core_identity_equal"] for p in pairs):
        decision = "HOLD_NO_XID_REUSE_DISCRIMINATOR"
    elif any(r["case"] == "cross_generation_stale" and r["policy"] == "LIFETIME_BOUND"
             and r["bound"] == "ACCEPT" for r in rows):
        decision = "FAIL_LIFETIME_ESCAPE"
    elif any(r["case"] == "same_generation" and r["policy"] == "LIFETIME_BOUND"
             and r["bound"] != "ACCEPT" for r in rows):
        decision = "FAIL_LIFETIME_OVERINVALIDATION"
    elif pass_gate:
        decision = "PASS_XSERVER_LIFETIME_BINDING_REQUIRED_SCOPED"
    else:
        decision = "STOP_OR_HOLD_FORMAL_GATE"
    result = {
        "allocation_id": "issue3580-xserver-lifetime-formal-01",
        "issue": 3581,
        "source_commit": os.environ["OBSTAC_SOURCE_COMMIT"],
        "image_id": os.environ["OBSTAC_IMAGE_ID"],
        "freeze_sha256": hashlib.sha256(Path("/freeze.json").read_bytes()).hexdigest(),
        "source_manifest_sha256": hashlib.sha256(Path("/source_manifest.json").read_bytes()).hexdigest(),
        "decision": decision,
        "rows": rows,
        "pairs": pairs,
        "negative_controls": controls,
        "issued_receipts": issued_receipts,
        "formal_invocations": 1,
        "reruns": 0,
        "authority": 0,
        "input_calls": 0,
    }
    canonical = json.dumps(result, sort_keys=True, separators=(",", ":")).encode()
    result["result_sha256"] = hashlib.sha256(canonical).hexdigest()
    (EVIDENCE / "raw.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    print(json.dumps({"decision": result["decision"], "rows": len(rows), "pairs": len(pairs),
                      "negative_controls": len(controls), "result_sha256": result["result_sha256"]}, sort_keys=True))


if __name__ == "__main__":
    run()
