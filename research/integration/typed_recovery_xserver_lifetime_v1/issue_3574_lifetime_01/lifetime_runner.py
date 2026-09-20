#!/usr/bin/env python3
"""One frozen, read-only X-server reincarnation identity allocation."""
import hashlib
import json
import os
from pathlib import Path
import secrets
import subprocess
import sys
import time

from Xlib import X, display
from Xlib.ext import res

sys.path.insert(0, "/freeze")
import validator_881_frozen as validator

ROOT = Path("/evidence")
DISPLAY = ":149"
SOCKET = Path("/tmp/.X11-unix/X149")
REPS = 4


def sha(data):
    return hashlib.sha256(data).hexdigest()


def git_blob_sha(data):
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


def verify_freeze():
    manifest_path = Path("/freeze/freeze.json")
    manifest_bytes = manifest_path.read_bytes()
    manifest = json.loads(manifest_bytes)
    for name, expected in manifest["sha256"].items():
        if sha((Path("/freeze") / name).read_bytes()) != expected:
            raise RuntimeError("FREEZE_SHA256_MISMATCH:" + name)
    validator_data = (Path("/freeze") / "validator_881_frozen.py").read_bytes()
    if git_blob_sha(validator_data) != manifest["validator_git_blob_sha1"]:
        raise RuntimeError("VALIDATOR_GIT_BLOB_MISMATCH")
    return manifest, sha(manifest_bytes)


def proc_start_ticks(pid):
    row = Path(f"/proc/{pid}/stat").read_text()
    tail = row[row.rfind(")") + 2:].split()
    return tail[19]


def fixture_script():
    return r'''import base64,hashlib,json,os,time
from Xlib import X,display
d=display.Display(":149"); s=d.screen()
w=s.root.create_window(80,80,240,160,0,s.root_depth,X.InputOutput,X.CopyFromParent,background_pixel=s.white_pixel,event_mask=X.ExposureMask)
w.set_wm_name("lifetime-902"); w.set_wm_class("lifetime-902","Lifetime902"); w.map(); d.sync(); time.sleep(.12)
atom=d.intern_atom("WM_TRANSIENT_FOR")
transient=w.get_full_property(atom,X.AnyPropertyType)
im=w.get_image(0,0,240,160,X.ZPixmap,0xffffffff)
print(json.dumps({"xid":int(w.id),"root_xid":int(s.root.id),"geometry":[80,80,240,160],"title":w.get_wm_name(),"wm_class":w.get_wm_class(),"transient_present":transient is not None,"pixel_bytes":len(im.data),"pixel_sha256":hashlib.sha256(im.data).hexdigest(),"pixel_b64":base64.b64encode(im.data).decode()}),flush=True)
time.sleep(30)
'''


def start_server():
    if SOCKET.exists():
        raise RuntimeError("X11_SOCKET_PREEXISTS")
    p = subprocess.Popen(["/usr/bin/Xvfb", DISPLAY, "-screen", "0", "640x480x24", "-nolisten", "tcp"],
                         stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        if p.poll() is not None:
            raise RuntimeError("XVFB_EXITED_EARLY")
        try:
            d = display.Display(DISPLAY); d.close()
            return p, proc_start_ticks(p.pid)
        except Exception:
            time.sleep(.02)
    p.terminate(); p.wait(timeout=3)
    raise RuntimeError("XVFB_START_TIMEOUT")


def start_fixture():
    p = subprocess.Popen(["python3", "-c", fixture_script()],
                         env={**os.environ, "DISPLAY": DISPLAY, "PYTHONDONTWRITEBYTECODE": "1"},
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    line = p.stdout.readline()
    if not line:
        err = p.stderr.read()
        raise RuntimeError("FIXTURE_NO_RECORD:" + err)
    row = json.loads(line)
    row.update(pid=p.pid, pid_start_ticks=proc_start_ticks(p.pid))
    return p, row


def xres_identity(xid):
    d = display.Display(DISPLAY)
    version = d.res_query_version()
    replies = d.res_query_client_ids([
        {"client": xid, "mask": res.LocalClientPIDMask}]).ids
    d.close()
    rows = [{"client": int(item.spec.client), "mask": int(item.spec.mask),
             "values": [int(v) for v in item.value]} for item in replies]
    return {"version": [int(version.server_major), int(version.server_minor)],
            "rows": rows}


def observe_generation(rep, generation):
    server, server_ticks = start_server()
    token = secrets.token_hex(32)
    client = None
    try:
        client, fixture = start_fixture()
        ident = xres_identity(fixture["xid"])
        local_pids = [pid for row in ident["rows"] if row["mask"] & res.LocalClientPIDMask
                      for pid in row["values"]]
        fixture.update(xres=ident, xres_local_pids=local_pids)
        record = {"rep": rep, "generation": generation, "server_instance_id": token,
                  "server": {"pid": server.pid, "pid_start_ticks": server_ticks,
                             "display": DISPLAY}, "fixture": fixture,
                  "authority": "none", "task_input_granted": False,
                  "action_admission_eligible": False, "input_calls": 0}
        return record, client, server
    except Exception:
        if client is not None:
            client.terminate(); client.wait(timeout=3)
        server.terminate(); server.wait(timeout=3)
        raise


def stop_generation(client, server, record):
    client.terminate()
    try:
        client_exit = client.wait(timeout=3)
    except subprocess.TimeoutExpired:
        client.kill(); client_exit = client.wait(timeout=3)
    server.terminate()
    try:
        server_exit = server.wait(timeout=3)
    except subprocess.TimeoutExpired:
        server.kill(); server_exit = server.wait(timeout=3)
    deadline = time.monotonic() + 3
    while SOCKET.exists() and time.monotonic() < deadline:
        time.sleep(.02)
    record["cleanup"] = {"fixture_exit_code": client_exit, "fixture_reaped": client.poll() is not None,
                          "xvfb_exit_code": server_exit, "xvfb_reaped": server.poll() is not None,
                          "socket_disappeared": not SOCKET.exists()}


def core_identity(generation):
    ctx = {"client_id": generation["fixture"]["xid"], "transient_for": None}
    return validator.identity_from_context(ctx, backend="x11")


def receipt(identity):
    return {"identity": identity, "authority": "none", "task_input_granted": False,
            "action_admission_eligible": False}


def classify_lifetime(source, current, source_token, current_token):
    base = validator.classify(receipt(source), current)
    if base["classification"] != validator.EXACT_MATCH:
        return {"classification": "REJECT", "reason": base["reason"]}
    if source_token != current_token:
        return {"classification": "REJECT", "reason": "server_instance_mismatch"}
    return {"classification": "EXACT_MATCH", "reason": "all_identity_and_lifetime_equal"}


def identity_rows(old, current):
    a, b = core_identity(old), core_identity(current)
    receipt_a = receipt(a)
    base_fresh = validator.classify(receipt_a, a)
    base_stale = validator.classify(receipt_a, b)
    life_fresh = classify_lifetime(a, a, old["server_instance_id"], old["server_instance_id"])
    life_stale = classify_lifetime(a, b, old["server_instance_id"], current["server_instance_id"])
    rows = []
    for pair, source_token, current_token, result in (
        ("same_generation", old["server_instance_id"], old["server_instance_id"], base_fresh),
        ("cross_generation_stale", old["server_instance_id"], current["server_instance_id"], base_stale),
    ):
        rows.append({"rep": old["rep"], "comparison": pair, "policy": "CURRENT_TYPED",
                     "source_server_instance_id": source_token,
                     "current_server_instance_id": current_token,
                     "classification": result["classification"], "reason": result["reason"],
                     "authority": "none", "task_input_granted": False,
                     "action_admission_eligible": False})
    for pair, source_token, current_token, result in (
        ("same_generation", old["server_instance_id"], old["server_instance_id"], life_fresh),
        ("cross_generation_stale", old["server_instance_id"], current["server_instance_id"], life_stale),
    ):
        rows.append({"rep": old["rep"], "comparison": pair, "policy": "LIFETIME_BOUND",
                     "source_server_instance_id": source_token,
                     "current_server_instance_id": current_token,
                     "classification": result["classification"], "reason": result["reason"],
                     "authority": "none", "task_input_granted": False,
                     "action_admission_eligible": False})
    return rows, a, b


def negative_controls(identity, token):
    base = receipt(identity)
    missing = {"receipt": base, "current_identity": identity,
               "source_token": token, "current_token": None,
               "result": classify_lifetime(identity, identity, token, None)}
    forged = {"receipt": base, "current_identity": identity,
              "source_token": token, "current_token": "forged-token",
              "result": classify_lifetime(identity, identity, token, "forged-token")}
    escalated = dict(base, task_input_granted=True)
    changed_backend = json.loads(json.dumps(base)); changed_backend["identity"]["backend"]["value"] = "wayland"
    changed_client = json.loads(json.dumps(base)); changed_client["identity"]["top_level_client_id"]["value"] += 1
    changed_transient = json.loads(json.dumps(base)); changed_transient["identity"]["transient_for"] = validator.known(77)
    return {
        "missing_token": missing,
        "forged_token": forged,
        "authority_escalation": {"receipt": escalated, "current_identity": identity,
                                 "result": validator.classify(escalated, identity)},
        "changed_backend": {"receipt": changed_backend, "current_identity": identity,
                            "result": validator.classify(changed_backend, identity)},
        "changed_client_id": {"receipt": changed_client, "current_identity": identity,
                              "result": validator.classify(changed_client, identity)},
        "known_transient_mismatch": {"receipt": changed_transient, "current_identity": identity,
                                     "result": validator.classify(changed_transient, identity)},
    }


def main():
    manifest, manifest_sha = verify_freeze()
    if ROOT.exists() and any(ROOT.iterdir()):
        raise RuntimeError("OUTPUT_DIRECTORY_NOT_EMPTY")
    ROOT.mkdir(parents=True, exist_ok=True)
    pairs, rows, failures = [], [], []
    try:
        for rep in range(1, REPS + 1):
            old, c1, s1 = observe_generation(rep, "G1")
            stop_generation(c1, s1, old)
            if not old["cleanup"]["socket_disappeared"] or not old["cleanup"]["xvfb_reaped"]:
                raise RuntimeError("G1_LIFECYCLE_WITNESS_MISSING")
            current, c2, s2 = observe_generation(rep, "G2")
            stop_generation(c2, s2, current)
            if not current["cleanup"]["socket_disappeared"] or not current["cleanup"]["xvfb_reaped"]:
                raise RuntimeError("G2_LIFECYCLE_WITNESS_MISSING")
            pair_rows, old_identity, current_identity = identity_rows(old, current)
            pair = {"rep": rep, "G1": old, "G2": current,
                    "typed_identity_G1": old_identity, "typed_identity_G2": current_identity,
                    "rows": pair_rows, "negative_controls": negative_controls(old_identity, old["server_instance_id"])}
            pairs.append(pair); rows.extend(pair_rows)
            if old["fixture"]["xid"] != current["fixture"]["xid"]:
                raise RuntimeError("HOLD_NO_XID_REUSE_DISCRIMINATOR")
            if old["fixture"]["pixel_sha256"] != current["fixture"]["pixel_sha256"]:
                raise RuntimeError("HOLD_PIXEL_IDENTITY_MISMATCH")
            if old["server_instance_id"] == current["server_instance_id"]:
                raise RuntimeError("SERVER_INSTANCE_TOKEN_COLLISION")
        disposition = "HOLD_PENDING_INDEPENDENT_AUDIT"
    except Exception as error:
        failures.append({"error": repr(error)})
        disposition = str(error) if str(error).startswith("HOLD_") else "STOP_OR_FAIL_RUNNER"
    raw = {"schema": "xserver-lifetime-3574-v1", "allocation_id": "issue3574-lifetime-01",
           "disposition": disposition, "pairs": pairs, "classification_rows": rows,
           "failure": failures or None, "network": "none", "input_calls": 0,
           "source_validator_blob_sha1": manifest["validator_git_blob_sha1"],
           "freeze_manifest_sha256": manifest_sha,
           "source_commit": manifest["source_commit"],
           "container_image_id": manifest["container_image_id"]}
    data = json.dumps(raw, sort_keys=True, indent=2).encode()
    (ROOT / "raw.json").write_bytes(data)
    (ROOT / "raw.sha256").write_text(sha(data) + "  raw.json\n")
    print(json.dumps({"disposition": disposition, "pairs": len(pairs),
                      "classification_rows": len(rows), "raw_sha256": sha(data)}, sort_keys=True))
    if failures:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
