import hashlib
import json
import os
import signal
import subprocess
import time
from pathlib import Path


DISPLAY = ":155"
BASE = "OBSTAC_3430_ALLOCATION_02"
RAW = Path("/out/raw.jsonl")
PROCESSES = []


def start(args, **kwargs):
    p = subprocess.Popen(args, start_new_session=True, **kwargs)
    PROCESSES.append(p)
    return p


def stop(p):
    if p.poll() is None:
        os.killpg(p.pid, signal.SIGTERM)
        try:
            p.wait(timeout=4)
        except subprocess.TimeoutExpired:
            os.killpg(p.pid, signal.SIGKILL)
            p.wait(timeout=4)


def run(*args, timeout=5):
    return subprocess.run(args, text=True, capture_output=True, timeout=timeout)


def wait_window(title, timeout=15):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        r = run("xdotool", "search", "--name", title)
        if r.returncode == 0 and r.stdout.strip():
            wid = int(r.stdout.splitlines()[0])
            pr = run("xdotool", "getwindowpid", str(wid))
            if pr.returncode == 0 and pr.stdout.strip():
                return wid, int(pr.stdout.strip())
        time.sleep(0.1)
    raise TimeoutError(f"window did not appear: {title}")


def title_exists(title):
    return run("xdotool", "search", "--name", title).returncode == 0


def launch(label, title, port):
    page = (
        "data:text/html,<title>" + title + "</title><body><script>"
        "document.onkeydown=e=>{if(e.key==='Enter'){document.title='" + title +
        "-EFFECT';document.body.dataset.effect='" + title + "'}}</script></body>"
    )
    return start([
        "/usr/bin/chromium", "--no-sandbox", "--disable-gpu",
        "--disable-dev-shm-usage", f"--user-data-dir=/tmp/obstac-{label}",
        f"--remote-debugging-port={port}", "--no-first-run", "--app=" + page,
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def keypress(wid):
    r = run("xdotool", "key", "--window", str(wid), "Return")
    time.sleep(0.35)
    return {"returncode": r.returncode, "stderr": r.stderr.strip()[:300]}


def main():
    os.environ["DISPLAY"] = DISPLAY
    xvfb = start(["Xvfb", DISPLAY, "-screen", "0", "1024x768x24", "-ac"],
                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(0.4)
    if xvfb.poll() is not None:
        raise RuntimeError("Xvfb exited before allocation")

    rows = []
    try:
        old = launch("p1", "P1-3430", 9601)
        old_w, old_pid = wait_window("P1-3430")
        old_proc_start = time.monotonic_ns()
        stop(old)
        time.sleep(0.25)

        p2 = launch("p2", "P2-3430", 9602)
        decoy = launch("decoy", "DECOY-3430", 9603)
        p2_w, p2_pid = wait_window("P2-3430")
        decoy_w, decoy_pid = wait_window("DECOY-3430")
        p2_proc_start = time.monotonic_ns()

        # Attempt the old X11 target directly; record the actual send and effects.
        old_send = keypress(old_w)
        rows.append({
            "event": "old_target_attempt", "old_generation": 1,
            "current_generation": 2, "old_window": old_w,
            "old_pid": old_pid, "current_pid": p2_pid, "send": old_send,
            "p2_effect_after_attempt": title_exists("P2-3430-EFFECT"),
            "decoy_effect_after_attempt": title_exists("DECOY-3430-EFFECT"),
        })

        decoy_send = keypress(decoy_w)
        rows.append({
            "event": "decoy_target_attempt", "target_generation": 2,
            "target_pid": p2_pid, "window_pid": decoy_pid,
            "window": decoy_w, "send": decoy_send,
            "decoy_effect": title_exists("DECOY-3430-EFFECT"),
            "p2_effect": title_exists("P2-3430-EFFECT"),
        })

        p2_send = keypress(p2_w)
        rows.append({
            "event": "p2_positive_control", "generation": 2,
            "target_pid": p2_pid, "window_pid": p2_pid,
            "window": p2_w, "send": p2_send,
            "p2_effect": title_exists("P2-3430-EFFECT"),
        })
        rows.append({
            "event": "allocation_identity", "old_generation": 1,
            "current_generation": 2, "old_pid": old_pid,
            "old_window": old_w, "current_pid": p2_pid,
            "current_window": p2_w, "old_start_monotonic_ns": old_proc_start,
            "current_start_monotonic_ns": p2_proc_start,
            "pid_reused": old_pid == p2_pid, "xid_reused": old_w == p2_w,
        })
    finally:
        for p in reversed(PROCESSES):
            stop(p)

    RAW.parent.mkdir(parents=True, exist_ok=True)
    raw = b"".join((json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8") for row in rows)
    RAW.write_bytes(raw)
    exact = RAW.read_bytes()
    print(json.dumps({
        "allocation": BASE, "row_count": len(rows),
        "raw_bytes": len(exact), "raw_sha256": hashlib.sha256(exact).hexdigest(),
        "raw_base64": __import__("base64").b64encode(exact).decode("ascii"),
        "container_exit": 0,
    }, sort_keys=True))


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        for p in reversed(PROCESSES):
            try:
                stop(p)
            except Exception:
                pass
        print(json.dumps({"allocation": BASE, "stop_reason": type(e).__name__ + ": " + str(e)}, sort_keys=True))
        raise
