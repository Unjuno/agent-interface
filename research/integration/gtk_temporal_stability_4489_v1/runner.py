"""No-input repeated GTK target captures before and after a render-only decoy."""
import json
import os
from pathlib import Path
import select
import subprocess
import sys
import time

from Xlib import X, display
from stability_gate import main as evaluate_candidate

ROOT = Path(__file__).resolve().parent
OUT = Path(os.environ.get("OUT", "/out"))
SCHEDULE = json.loads((ROOT / "case_schedule.json").read_text())


def line(path, value):
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n")
        f.flush()
        os.fsync(f.fileno())


def x_info(env, xid):
    props = subprocess.run(["xprop", "-id", str(xid), "_NET_WM_PID", "WM_NAME", "WM_CLASS"],
                           env=env, check=True, text=True, capture_output=True).stdout
    geom = subprocess.run(["xwininfo", "-id", str(xid)], env=env,
                          check=True, text=True, capture_output=True).stdout
    vals = {}
    for key in ("Width", "Height", "Absolute upper-left X", "Absolute upper-left Y"):
        for raw in geom.splitlines():
            if raw.strip().startswith(key + ":"):
                vals[key] = int(raw.split(":", 1)[1].strip())
                break
    dpy = display.Display(env["DISPLAY"])
    try:
        focus_obj = dpy.get_input_focus().focus
        focus = int(focus_obj.id) if hasattr(focus_obj, "id") else int(focus_obj)
    finally:
        dpy.close()
    return {"xid": int(xid), "xprop": props, "geometry": vals, "focus_xid": focus}


def xwd(env, xid, path):
    subprocess.run(["xwd", "-silent", "-id", str(xid), "-out", str(path)],
                   env=env, check=True, capture_output=True, timeout=10)


def launch_xvfb(out):
    proc = subprocess.Popen(["Xvfb", "-displayfd", "1", "-screen", "0", "1000x500x24",
                             "-nolisten", "tcp", "-ac"], stdout=subprocess.PIPE,
                            stderr=(out / "xvfb.stderr").open("wb"), text=True)
    if not select.select([proc.stdout], [], [], 10)[0]:
        raise TimeoutError("xvfb_readiness")
    num = proc.stdout.readline().strip()
    if not num.isdigit():
        raise RuntimeError("xvfb_displayfd_invalid")
    return proc, ":" + num


def wait_file(path, proc, label):
    deadline = time.monotonic() + 10
    while not path.exists():
        if proc.poll() is not None or time.monotonic() >= deadline:
            raise RuntimeError(label + "_readiness")
        time.sleep(0.02)


def capture_phase(out, phase, count, env, xid):
    rows = []
    interval = SCHEDULE["sample_interval_ms"] / 1000
    next_at = time.monotonic()
    for index in range(count):
        if index:
            next_at += interval
            time.sleep(max(0, next_at - time.monotonic()))
        path = out / "frames" / f"target-{phase}-{index + 1:02d}.xwd"
        before = x_info(env, xid)
        capture_start_ns = time.monotonic_ns()
        xwd(env, xid, path)
        capture_end_ns = time.monotonic_ns()
        after = x_info(env, xid)
        row = {"phase": phase, "index": index + 1, "capture_start_ns": capture_start_ns,
               "capture_end_ns": capture_end_ns, "path": str(path.relative_to(out)),
               "sha256": __import__("hashlib").sha256(path.read_bytes()).hexdigest(),
               "identity_before": before, "identity_after": after}
        line(out / "captures.jsonl", row)
        rows.append(row)
    return rows


def stop(role, proc):
    if proc is None:
        return {"role": role, "pid": None, "returncode": None}
    if proc.poll() is None:
        proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait(timeout=3)
    return {"role": role, "pid": proc.pid, "returncode": proc.returncode}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "frames").mkdir(exist_ok=True)
    (OUT / "captures.jsonl").write_text("")
    processes = []
    result = {"allocation": os.environ.get("ALLOCATION", "construction-01"),
              "container_image_id": os.environ.get("IMAGE_ID"),
              "container_platform": os.environ.get("IMAGE_PLATFORM"),
              "container_id": os.uname().nodename,
              "network": "none", "root_read_only": True,
              "source_read_only": True, "writable_path": "/out only",
              "input_events": 0, "model_calls": 0, "provider_calls": 0,
              "target_operations": 0, "schedule": SCHEDULE}
    try:
        xvfb, display_name = launch_xvfb(OUT)
        processes.append(("xvfb", xvfb))
        env = dict(os.environ, DISPLAY=display_name, GSETTINGS_BACKEND="memory", NO_AT_BRIDGE="1")
        target_meta = OUT / "target-meta.json"
        target = subprocess.Popen(["/usr/bin/python3", str(ROOT / "fixture.py"),
                                   "--mode", "useful", "--meta", str(target_meta),
                                   "--effect", str(OUT / "effect.json"),
                                   "--events", str(OUT / "target-events.jsonl")],
                                  env=env, stdout=(OUT / "target.stdout").open("wb"),
                                  stderr=(OUT / "target.stderr").open("wb"))
        processes.append(("target", target))
        wait_file(target_meta, target, "target")
        meta = json.loads(target_meta.read_text())
        target_xid = int(meta["window_id"])
        entry_xid = int(meta["entry_window_id"])
        focus_display = display.Display(display_name)
        try:
            focus_display.set_input_focus(entry_xid, X.RevertToParent, X.CurrentTime)
            focus_display.sync()
        finally:
            focus_display.close()
        result.update({"display": display_name, "target_pid": target.pid,
                       "target_xid": target_xid,
                       "target_entry_xid": entry_xid,
                       "focus_setup": "XSetInputFocus(GTK Entry window before capture; no key/button events)",
                       "target_title": "AgentInterfaceGtkFixture"})
        target_pre = x_info(env, target_xid)
        xwd(env, target_xid, OUT / "frames" / "target-initial.xwd")
        result["target_identity_initial"] = target_pre
        pre = capture_phase(OUT, "pre_decoy", SCHEDULE["pre_decoy_captures"], env, target_xid)
        decoy_meta = OUT / "decoy-meta.json"
        decoy = subprocess.Popen(["/usr/bin/python3", str(ROOT / "decoy.py"), "--meta", str(decoy_meta)],
                                 env=env, stdout=(OUT / "decoy.stdout").open("wb"),
                                 stderr=(OUT / "decoy.stderr").open("wb"))
        processes.append(("decoy", decoy))
        wait_file(decoy_meta, decoy, "decoy")
        decoy_info = json.loads(decoy_meta.read_text())
        decoy_xid = int(decoy_info["window_id"])
        result.update({"decoy_pid": decoy.pid, "decoy_xid": decoy_xid,
                       "decoy_title": decoy_info.get("title", "AgentInterfaceGtkFixture"),
                       "target_identity_after_decoy": x_info(env, target_xid),
                       "decoy_identity": x_info(env, decoy_xid)})
        xwd(env, decoy_xid, OUT / "frames" / "decoy-saved-looking.xwd")
        post = capture_phase(OUT, "post_decoy", SCHEDULE["post_decoy_captures"], env, target_xid)
        result["target_identity_final"] = x_info(env, target_xid)
        result["pre_count"] = len(pre)
        result["post_count"] = len(post)
        (OUT / "manifest.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
        evaluate_candidate(OUT)
        audit = subprocess.run(["/usr/bin/python3", str(ROOT / "audit.py"), str(OUT), "--live",
                                "--output", "LIVE_AUDIT_RESULT.json"],
                               capture_output=True, text=True, timeout=60)
        (OUT / "live-audit.stdout.txt").write_text(audit.stdout)
        (OUT / "live-audit.stderr.txt").write_text(audit.stderr)
        if audit.returncode:
            raise RuntimeError("independent_audit_failed:" + str(audit.returncode))
    finally:
        cleanup = [stop(role, proc) for role, proc in reversed(processes)]
        (OUT / "cleanup.json").write_text(json.dumps(cleanup, sort_keys=True, indent=2) + "\n")
        if (OUT / "manifest.json").exists() and (OUT / "candidate_decisions.json").exists():
            offline = subprocess.run(["/usr/bin/python3", str(ROOT / "audit.py"), str(OUT),
                                      "--output", "AUDIT_RESULT.json"],
                                     capture_output=True, text=True, timeout=60)
            (OUT / "audit.stdout.txt").write_text(offline.stdout)
            (OUT / "audit.stderr.txt").write_text(offline.stderr)
            if offline.returncode:
                raise RuntimeError("post_cleanup_audit_failed:" + str(offline.returncode))
            print(offline.stdout.strip(), flush=True)


if __name__ == "__main__":
    main()
