import hashlib
import json
import os
import signal
import subprocess
import time
from pathlib import Path


DISPLAY = ":157"
RAW = Path("/out/raw.jsonl")
PROCESSES = []
STARTED = {}


def start(label, args, **kwargs):
    p = subprocess.Popen(args, start_new_session=True, **kwargs)
    PROCESSES.append((label, p))
    STARTED[label] = time.monotonic_ns()
    return p


def stop(label, p):
    if p.poll() is None:
        os.killpg(p.pid, signal.SIGTERM)
        try:
            p.wait(timeout=4)
        except subprocess.TimeoutExpired:
            os.killpg(p.pid, signal.SIGKILL)
            p.wait(timeout=4)
    return p.returncode


def cmd(*args, timeout=5):
    return subprocess.run(args, text=True, capture_output=True, timeout=timeout)


def launch(label, title, port):
    script = (
        "document.body.dataset.effects='0';document.title='READY-" + title +
        "';document.onkeydown=e=>{if(e.key==='Enter'){let n=Number(document.body.dataset.effects)+1;"
        "document.body.dataset.effects=String(n);document.title='" + title + "-EFFECT-'+n}}"
    )
    url = "data:text/html,<body><script>" + script + "</script></body>"
    return start(label, [
        "/usr/bin/chromium", "--no-sandbox", "--disable-gpu",
        "--disable-dev-shm-usage", f"--user-data-dir=/tmp/obstac-03-{label}",
        f"--remote-debugging-port={port}", "--no-first-run", "--app=" + url,
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def ready_window(title, timeout=15):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        r = cmd("xdotool", "search", "--name", "READY-" + title)
        if r.returncode == 0 and r.stdout.strip():
            wid = int(r.stdout.splitlines()[0])
            p = cmd("xdotool", "getwindowpid", str(wid))
            if p.returncode == 0 and p.stdout.strip():
                return wid, int(p.stdout.strip())
        time.sleep(0.1)
    raise TimeoutError("readiness title missing for " + title)


def title(wid):
    r = cmd("xdotool", "getwindowname", str(wid))
    return r.stdout.strip() if r.returncode == 0 else None


def owner(wid):
    r = cmd("xdotool", "getwindowpid", str(wid))
    return int(r.stdout.strip()) if r.returncode == 0 and r.stdout.strip() else None


def focus_and_return(wid):
    f = cmd("xdotool", "windowfocus", "--sync", str(wid))
    g = cmd("xdotool", "getwindowfocus")
    focused = int(g.stdout.strip()) if g.stdout.strip().isdigit() else None
    if f.returncode == 0 and focused == wid:
        k = cmd("xdotool", "key", "--clearmodifiers", "Return")
        time.sleep(0.35)
        send_rc, send_error = k.returncode, k.stderr.strip()[:200]
    else:
        send_rc, send_error = None, "send skipped: requested XID was not focused"
    return {"focus_rc": f.returncode,
            "focused_window": focused, "send_rc": send_rc, "send_stderr": send_error,
            "send_skipped": send_rc is None}


def effect_count(window_title, name):
    prefix = name + "-EFFECT-"
    if window_title and window_title.startswith(prefix):
        try:
            return int(window_title[len(prefix):])
        except ValueError:
            return None
    return 0


def main():
    os.environ["DISPLAY"] = DISPLAY
    xv = start("xvfb", ["Xvfb", DISPLAY, "-screen", "0", "1024x768x24", "-ac"],
               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(0.4)
    if xv.poll() is not None:
        raise RuntimeError("Xvfb exited before collection")

    rows = []
    try:
        p1 = launch("p1", "P1-3430-03", 9701)
        old_w, old_pid = ready_window("P1-3430-03")
        old_start = STARTED["p1"]
        stop("p1", p1)
        time.sleep(0.25)

        p2 = launch("p2", "P2-3430-03", 9702)
        decoy = launch("decoy", "DECOY-3430-03", 9703)
        p2_w, p2_pid = ready_window("P2-3430-03")
        decoy_w, decoy_pid = ready_window("DECOY-3430-03")
        rows.append({
            "event": "generation_pair",
            "old": {"generation": 1, "pid": old_pid, "window": old_w,
                    "started_monotonic_ns": old_start},
            "p2": {"generation": 2, "pid": p2_pid, "window": p2_w,
                   "started_monotonic_ns": STARTED["p2"]},
            "decoy": {"generation": 2, "pid": decoy_pid, "window": decoy_w,
                      "started_monotonic_ns": STARTED["decoy"]},
            "ready_markers": True,
        })

        before_decoy = title(decoy_w)
        before_p2 = title(p2_w)
        stale_send = focus_and_return(old_w)
        after_stale_decoy = title(decoy_w)
        after_stale_p2 = title(p2_w)
        rows.append({
            "event": "stale_xid_direct_input",
            "receipt": {"generation": 1, "pid": old_pid, "window": old_w},
            "current_target": {"generation": 2, "pid": p2_pid, "window": p2_w},
            "xid_owner_pid_after_transition": owner(old_w),
            "send": stale_send,
            "decoy_title_before": before_decoy,
            "decoy_title_after": after_stale_decoy,
            "p2_title_before": before_p2,
            "p2_title_after": after_stale_p2,
        })

        decoy_before = title(decoy_w)
        decoy_send = focus_and_return(decoy_w)
        decoy_after = title(decoy_w)
        p2_after_decoy = title(p2_w)
        rows.append({
            "event": "decoy_input_control", "target_pid": p2_pid,
            "window_pid": decoy_pid, "window": decoy_w,
            "send": decoy_send, "decoy_title_before": decoy_before,
            "decoy_title_after": decoy_after, "p2_title_after": p2_after_decoy,
        })

        p2_before = title(p2_w)
        p2_send = focus_and_return(p2_w)
        p2_after = title(p2_w)
        rows.append({
            "event": "p2_positive_control", "target_pid": p2_pid,
            "window_pid": p2_pid, "window": p2_w, "send": p2_send,
            "p2_title_before": p2_before, "p2_title_after": p2_after,
        })
    finally:
        exits = {}
        for label, p in reversed(PROCESSES):
            exits[label] = stop(label, p)
        rows.append({"event": "cleanup", "returncodes": exits,
                     "all_processes_reaped": all(p.poll() is not None for _, p in PROCESSES)})

    RAW.parent.mkdir(parents=True, exist_ok=True)
    raw = b"".join((json.dumps(r, sort_keys=True, separators=(",", ":")) + "\n").encode()
                    for r in rows)
    RAW.write_bytes(raw)
    stored = RAW.read_bytes()
    print(json.dumps({"allocation": "OBSTAC_3430_ALLOCATION_03",
                      "rows": len(rows), "bytes": len(stored),
                      "sha256": hashlib.sha256(stored).hexdigest(),
                      "container_exit": 0}, sort_keys=True))


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        for label, p in reversed(PROCESSES):
            try:
                stop(label, p)
            except Exception:
                pass
        print(json.dumps({"allocation": "OBSTAC_3430_ALLOCATION_03",
                          "stop_reason": type(e).__name__ + ": " + str(e)}, sort_keys=True))
        raise
