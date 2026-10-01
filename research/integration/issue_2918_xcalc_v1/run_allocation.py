"""One-shot real-app transfer experiment for Issue #2918, using XCalc."""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import time
from pathlib import Path

from PIL import Image
from Xlib import X, XK, display
from Xlib.ext import xtest
from Xlib.ext import res as xres

from runtime.cli_v1.observe import observe
from research.integration.issue_2918_xcalc_v1.live_xcalc_candidate import decide

OUT = Path(os.environ.get("OUT", "/out"))
CAP = OUT / "captures"
CAP.mkdir(parents=True, exist_ok=True)
DISPLAY = os.environ["DISPLAY"]
D = display.Display(DISPLAY)
ROOT = D.screen().root
TEMPLATE = json.loads(Path("research/integration/issue_2918_xcalc_v1/display_templates.json").read_text())
CAPTURE_BOX = TEMPLATE["capture"]
PIDS: list[subprocess.Popen] = []
LAST_INPUT_TRACE: list[dict] = []
WINDOW_GENERATION = 0


def owner_pid(xid: int):
    clients = D.res_query_clients().clients
    owners = [c for c in clients if (xid & (~int(c.resource_mask) & 0xFFFFFFFF)) == int(c.resource_base)]
    if len(owners) != 1:
        raise RuntimeError(f"XRes client owner count for {xid}: {len(owners)}")
    ids = D.res_query_client_ids([{"client": owners[0].resource_base,
                                   "mask": xres.LocalClientPIDMask}]).ids
    matches = [int(i.value[0]) for i in ids if int(i.spec.mask) == xres.LocalClientPIDMask and i.value]
    if len(matches) != 1:
        raise RuntimeError(f"XRes local PID count for {xid}: {len(matches)}")
    return matches[0], int(owners[0].resource_base)


def start_xcalc():
    global WINDOW_GENERATION
    existing = {int(w.id) for w in calculators()}
    proc = subprocess.Popen(["xcalc"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    PIDS.append(proc)
    for _ in range(100):
        D.sync()
        found = [w for w in calculators() if int(w.id) not in existing]
        if found:
            win = found[-1]
            pid, base = owner_pid(int(win.id))
            if pid != proc.pid:
                raise RuntimeError(f"XRes owner PID {pid} differs from launched xcalc PID {proc.pid}")
            WINDOW_GENERATION += 1
            return proc, win, pid, base, WINDOW_GENERATION
        time.sleep(0.03)
    raise RuntimeError("xcalc window did not appear")


def calculators():
    D.sync()
    return [w for w in ROOT.query_tree().children if w.get_wm_name() == "Calculator"]


def key(name: str):
    code = D.keysym_to_keycode(XK.string_to_keysym(name))
    if not code:
        raise RuntimeError(f"missing keycode {name}")
    xtest.fake_input(D, X.KeyPress, detail=code)
    xtest.fake_input(D, X.KeyRelease, detail=code)
    D.sync()
    time.sleep(0.035)
    LAST_INPUT_TRACE.append({"kind": "key", "keysym": name, "keycode": int(code),
                             "monotonic_ns": time.monotonic_ns()})


def set_number(win, value: int):
    global LAST_INPUT_TRACE
    LAST_INPUT_TRACE = []
    if value < 0 or value > 99:
        raise ValueError(value)
    D.set_input_focus(win, X.RevertToParent, X.CurrentTime)
    D.sync()
    # XCalc's visible AC button is at its stable 244x410 fixture location.
    geom = win.get_geometry()
    ROOT.warp_pointer(geom.x + 216, geom.y + 91)
    D.sync()
    xtest.fake_input(D, X.ButtonPress, detail=1)
    xtest.fake_input(D, X.ButtonRelease, detail=1)
    D.sync()
    LAST_INPUT_TRACE.append({"kind": "button", "button": "AC", "x": int(geom.x + 216),
                             "y": int(geom.y + 91), "xid": int(win.id),
                             "monotonic_ns": time.monotonic_ns()})
    time.sleep(0.06)
    for char in str(value):
        key(char)
    time.sleep(0.06)


def capture(win, tag: str, region=None):
    geom = win.get_geometry()
    if region is None:
        region = [0, 0, geom.width, geom.height]
    owner_pid_before, owner_base_before = owner_pid(int(win.id))
    before = time.monotonic_ns()
    reply = observe({"xcalc": win.id}, target="xcalc", frame="window_client",
                    region=region, capture_directory=str(CAP), display_name=DISPLAY)
    after = time.monotonic_ns()
    owner_pid_after, owner_base_after = owner_pid(int(win.id))
    obs = reply.get("observation", {})
    art = obs.get("artifact", {})
    path = Path(art.get("path", ""))
    if path.exists():
        path = Path("/out") / path.name
    pixels_value = None
    if path.is_file():
        try:
            im = Image.open(path).convert("RGB")
            box = (CAPTURE_BOX["x"], CAPTURE_BOX["y"],
                   CAPTURE_BOX["x"] + CAPTURE_BOX["width"],
                   CAPTURE_BOX["y"] + CAPTURE_BOX["height"])
            if im.size == (244, 410):
                digest = hashlib.sha256(im.crop(box).tobytes()).hexdigest()
                pixels_value = TEMPLATE["sha256_to_value"].get(digest)
        except Exception:
            pass
    return {"case": tag, "call_before_ns": before, "call_after_ns": after,
            "owner_pid_before": owner_pid_before, "owner_pid_after": owner_pid_after,
            "owner_base_before": owner_base_before, "owner_base_after": owner_base_after,
            "reply": reply, "artifact_path": str(path), "template_value": pixels_value}


def formal_row(*, tag, win, value, phase, intent, binding, prior=None,
               region=None, stale=False, binding_conflict=False, ambiguous=False,
               api_call=True):
    if api_call:
        raw = capture(win, tag, region)
        if stale:
            time.sleep(0.275)
        reply = raw["reply"]
        obs = reply.get("observation", {})
        candidate_xid = obs.get("native_window_id", 0) + (1 if binding_conflict else 0)
        row = decide(artifact=obs.get("artifact", {}), phase=phase,
                     binding=binding, intent_epoch=intent,
                     captured_ns=obs.get("capture_ended_ns", raw["call_before_ns"]),
                     now_ns=time.monotonic_ns(),
                     observed_xid=candidate_xid,
                     observed_client_pid=raw["owner_pid_before"],
                     observed_client_resource_base=raw["owner_base_before"],
                     observation_epoch=reply.get("observation_id"),
                     prior=prior, ambiguous=False)
        actual_xid = obs.get("native_window_id")
        image_path = raw["artifact_path"]
        artifact = obs.get("artifact", {})
        api_status = reply.get("status")
        obs_id = reply.get("observation_id")
        cap_start, cap_end = obs.get("capture_started_ns"), obs.get("capture_ended_ns")
        receipt_sha = obs.get("sha256")
        image_sha = artifact.get("sha256")
        api_calls = 1
        owner_pid_before = raw["owner_pid_before"]
        owner_pid_after = raw["owner_pid_after"]
        owner_base_before = raw["owner_base_before"]
        owner_base_after = raw["owner_base_after"]
    else:
        candidate_xid = binding.get("xid")
        raw = {"case": tag, "reply": None, "call_before_ns": None,
               "call_after_ns": None, "artifact_path": None, "template_value": None}
        row = decide(artifact={}, phase=phase, binding=binding, intent_epoch=intent,
                     captured_ns=time.monotonic_ns(), now_ns=time.monotonic_ns(),
                     observed_xid=binding.get("xid"),
                     observed_client_pid=binding.get("client_pid"),
                     observed_client_resource_base=binding.get("client_resource_base"),
                     observation_epoch=None,
                     prior=prior, ambiguous=ambiguous)
        actual_xid = None; image_path = None; artifact = {}; api_status = None
        obs_id = None; cap_start = None; cap_end = None; receipt_sha = None
        image_sha = None; api_calls = 0
        owner_pid_before = owner_pid_after = owner_base_before = owner_base_after = None
    row.update({"case": tag, "phase": phase, "intent_epoch": intent,
                "binding": binding, "prior": prior, "requested_value": value,
                "public_api_calls": api_calls, "api_status": api_status,
                "observation_id": obs_id, "observed_xid": actual_xid,
                "observation_epoch": obs_id,
                "candidate_observed_xid": candidate_xid,
                "candidate_observed_client_pid": owner_pid_before,
                "candidate_observed_client_resource_base": owner_base_before,
                "observed_client_pid_before": owner_pid_before,
                "observed_client_pid_after": owner_pid_after,
                "observed_client_resource_base_before": owner_base_before,
                "observed_client_resource_base_after": owner_base_after,
                "capture_started_ns": cap_start, "capture_ended_ns": cap_end,
                "decision_monotonic_ns": time.monotonic_ns(),
                "receipt_sha256": receipt_sha, "artifact_sha256": image_sha,
                "artifact_path": image_path,
                "region": ((raw["reply"] or {}).get("observation", {}).get("region")),
                "frame": ((raw["reply"] or {}).get("observation", {}).get("frame")),
                "raw_requested_state_value": value,
                "input_trace": list(LAST_INPUT_TRACE),
                "input_dispatched_by_observer": (raw["reply"] or {}).get("input_dispatched", False),
                "side_effect_authority": (raw["reply"] or {}).get("side_effect_authority", False),
                "stale_injected": stale, "binding_conflict_injected": binding_conflict,
                "ambiguous_target_injected": ambiguous,
                "template_value_diagnostic_not_used_for_decision": raw.get("template_value")})
    return row, raw


def main():
    rows, raw_meta = [], []
    proc, win, client_pid, resource_base, generation = start_xcalc()
    bind = {"display": DISPLAY, "xid": int(win.id), "role": "xcalc-calculator",
            "client_pid": client_pid, "client_resource_base": resource_base,
            "window_generation": generation}
    prior = None
    sequence = [
        ("effect_initial_14", 14, "EFFECT_PENDING", "intent-effect-01"),
        ("effect_unmasked_10", 10, "EFFECT_PENDING", "intent-effect-01"),
        ("effect_masked_12", 12, "EFFECT_PENDING", "intent-effect-01"),
    ]
    for tag, value, phase, intent in sequence:
        set_number(win, value)
        row, raw = formal_row(tag=tag, win=win, value=value, phase=phase,
                              intent=intent, binding=bind, prior=prior)
        rows.append(row); raw_meta.append({k:v for k,v in raw.items() if k != "reply"})
        if row.get("mask") is not None:
            prior = {"phase": phase, "state": tuple(row["state"]), "mask": row["mask"],
                     "binding": bind, "intent_epoch": intent}

    prior = None
    for tag, value in [("prepare_initial_12", 12), ("prepare_unmasked_14", 14)]:
        set_number(win, value)
        row, raw = formal_row(tag=tag, win=win, value=value, phase="PREPARE",
                              intent="intent-prepare-01", binding=bind, prior=prior)
        rows.append(row); raw_meta.append({k:v for k,v in raw.items() if k != "reply"})
        if row.get("mask") is not None:
            prior = {"phase": "PREPARE", "state": tuple(row["state"]), "mask": row["mask"],
                     "binding": bind, "intent_epoch": "intent-prepare-01"}

    # Observation boundary controls: clipped pixels, unavailable display ROI,
    # unrecognized displayed value, stale receipt, and contradictory binding.
    controls = [
        ("partial_capture", 14, [0, 0, 190, 72], False, False),
        ("missing_display_region", 14, [0, 72, 244, 338], False, False),
        ("unrecognized_display_99", 99, None, False, False),
        ("stale_capture", 14, None, True, False),
        ("contradictory_xid", 14, None, False, True),
    ]
    for tag, value, region, stale, conflict in controls:
        set_number(win, value)
        row, raw = formal_row(tag=tag, win=win, value=value, phase="EFFECT_PENDING",
                              intent=f"control-{tag}", binding=bind,
                              region=region, stale=stale, binding_conflict=conflict)
        rows.append(row); raw_meta.append({k:v for k,v in raw.items() if k != "reply"})

    # Window replacement must invalidate a previously issued certificate.
    set_number(win, 14)
    old_prior = {"phase": "EFFECT_PENDING", "state": (1, 1, 1, 0), "mask": ["E", "S"],
                 "binding": bind, "intent_epoch": "replace-epoch"}
    old_xid = int(win.id)
    proc.terminate(); proc.wait(timeout=3)
    proc2, win2, client_pid2, resource_base2, generation2 = start_xcalc()
    new_bind = {"display": DISPLAY, "xid": int(win2.id), "role": "xcalc-calculator",
                "client_pid": client_pid2, "client_resource_base": resource_base2,
                "window_generation": generation2}
    set_number(win2, 14)
    row, raw = formal_row(tag="target_replacement", win=win2, value=14,
                          phase="EFFECT_PENDING", intent="replace-epoch",
                          binding=new_bind, prior=old_prior)
    row["old_xid"] = old_xid
    rows.append(row); raw_meta.append({k:v for k,v in raw.items() if k != "reply"})

    # Two visible app instances with the same role are an ambiguous target:
    # refuse before calling public observation.
    second_proc, second, second_pid, second_base, second_generation = start_xcalc()
    row, raw = formal_row(tag="ambiguous_target", win=win2, value=None,
                          phase="EFFECT_PENDING", intent="ambiguous-epoch",
                          binding=new_bind, ambiguous=True, api_call=False)
    row["input_trace"] = []
    row["matching_xids"] = sorted([int(win2.id), int(second.id)])
    row["matching_client_pids"] = sorted([client_pid2, second_pid])
    row["matching_generations"] = sorted([generation2, second_generation])
    rows.append(row); raw_meta.append({k:v for k,v in raw.items() if k != "reply"})
    second_proc.terminate(); second_proc.wait(timeout=3)

    # A fresh visible result cannot reuse the predecessor certificate under a
    # different caller intent epoch.
    set_number(win2, 14)
    intent_prior = {"phase": "EFFECT_PENDING", "state": (1, 1, 1, 0), "mask": ["E", "S"],
                    "binding": new_bind, "intent_epoch": "old-intent"}
    row, raw = formal_row(tag="intent_epoch_mismatch", win=win2, value=14,
                          phase="EFFECT_PENDING", intent="new-intent",
                          binding=new_bind, prior=intent_prior)
    rows.append(row); raw_meta.append({k:v for k,v in raw.items() if k != "reply"})

    (OUT / "candidate_results.json").write_text(json.dumps(rows, sort_keys=True, indent=2) + "\n")
    (OUT / "capture_index.json").write_text(json.dumps(raw_meta, sort_keys=True, indent=2) + "\n")
    oracle = [{"case": r["case"], "requested_value": r["requested_value"],
               "phase": r["phase"], "intent_epoch": r["intent_epoch"],
               "observation_epoch": r["observation_epoch"],
               "binding": r["binding"], "prior": r["prior"],
               "artifact_path": r["artifact_path"], "artifact_sha256": r["artifact_sha256"],
               "receipt_sha256": r["receipt_sha256"],
               "capture_ended_ns": r["capture_ended_ns"], "decision_monotonic_ns": r["decision_monotonic_ns"],
               "public_api_calls": r["public_api_calls"], "api_status": r["api_status"]} for r in rows]
    (OUT / "sealed_oracle.json").write_text(json.dumps(oracle, sort_keys=True, indent=2) + "\n")
    (OUT / "allocation.json").write_text(json.dumps({"allocation":"formal-01",
       "cases":len(rows),"api_calls":sum(r["public_api_calls"] for r in rows),
       "input_route":"XTEST fixture control only; observer input_dispatched=false",
       "xcalc_version":"Debian x11-apps package in pinned local image",
       "display":DISPLAY,"authority":False}, sort_keys=True, indent=2)+"\n")
    for p in PIDS:
        if p.poll() is None:
            p.terminate()
            p.wait(timeout=3)
    D.close()
    print(json.dumps({"cases":len(rows),"api_calls":sum(r["public_api_calls"] for r in rows),"out":str(OUT)}))


if __name__ == "__main__":
    main()
