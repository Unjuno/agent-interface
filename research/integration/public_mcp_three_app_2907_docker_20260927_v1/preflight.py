import hashlib
import json
import os
import re
import signal
import subprocess
import time
from pathlib import Path

DISPLAY = ":142"
OUT = Path(os.environ.get("PREFLIGHT_OUTPUT", "/evidence/construction-01"))
ENV = dict(os.environ, DISPLAY=DISPLAY)


def run(argv, timeout=5):
    return subprocess.run(argv, env=ENV, text=True, capture_output=True,
                          timeout=timeout, check=False)


def process_states():
    result = {}
    for entry in Path("/proc").iterdir():
        if not entry.name.isdigit():
            continue
        try:
            raw = (entry / "stat").read_text()
            tail = raw[raw.rfind(")") + 2:].split()
            result[int(entry.name)] = {"ppid": int(tail[1]), "state": tail[0]}
        except (OSError, ValueError, IndexError):
            pass
    return result


def descendants(root):
    tree = process_states()
    found = {root}
    changed = True
    while changed:
        changed = False
        for pid, record in tree.items():
            if record["ppid"] in found and pid not in found:
                found.add(pid)
                changed = True
    return found


def windows():
    result = run(["xdotool", "search", "--onlyvisible", "--name", ".*"])
    return {int(x) for x in result.stdout.splitlines() if x.strip().isdigit()}


def inspect_window(wid):
    prop = run(["xprop", "-id", str(wid), "_NET_WM_PID", "WM_CLASS", "WM_NAME"])
    geo = run(["xdotool", "getwindowgeometry", str(wid)])
    owner = re.search(r"_NET_WM_PID\(CARDINAL\) = (\d+)", prop.stdout)
    size = re.search(r"Geometry: (\d+)x(\d+)", geo.stdout)
    return {"window_id": wid, "properties": prop.stdout, "geometry_text": geo.stdout,
            "owner_pid": int(owner.group(1)) if owner else None,
            "size": [int(size.group(1)), int(size.group(2))] if size else None}


def main():
    OUT.mkdir(parents=True, exist_ok=False)
    launched = []
    rows = []
    display = subprocess.Popen(["Xvfb", DISPLAY, "-screen", "0", "1600x1000x24"],
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    launched.append(display.pid)
    result = {"display": DISPLAY, "apps": rows, "input_operations": 0,
              "model_calls": 0, "network_calls": 0, "decision": "STOP_PREFLIGHT"}
    try:
        for _ in range(100):
            if Path("/tmp/.X11-unix/X142").exists():
                break
            time.sleep(.05)
        if not Path("/tmp/.X11-unix/X142").exists():
            raise RuntimeError("Xvfb socket not ready")
        wm = subprocess.Popen(["openbox", "--replace"], env=ENV,
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        launched.append(wm.pid)
        time.sleep(.6)
        apps = [
            ("inkscape", ["inkscape"], "inkscape"),
            ("calc", ["libreoffice", "--calc"], "libreoffice-calc"),
            ("chromium", ["chromium", "--no-sandbox", "--disable-gpu",
                          "--disable-dev-shm-usage", "--user-data-dir=/tmp/chromium-preflight", "about:blank"], "chromium"),
        ]
        for name, argv, class_hint in apps:
            before = windows()
            proc = subprocess.Popen(argv, env=ENV, stdout=subprocess.DEVNULL,
                                    stderr=subprocess.DEVNULL, start_new_session=True)
            launched.append(proc.pid)
            deadline = time.monotonic() + 40
            selected = None
            candidates = []
            while time.monotonic() < deadline:
                for wid in sorted(windows() - before):
                    row = inspect_window(wid)
                    candidates.append(row)
                    owner = row["owner_pid"]
                    if (owner in descendants(proc.pid) and row["size"] and
                            min(row["size"]) >= 100 and class_hint in row["properties"].lower()):
                        selected = row
                        break
                if selected:
                    break
                time.sleep(.25)
            if not selected:
                raise RuntimeError(f"{name}: no new visible class/owner-bound surface; candidates={candidates[-8:]}")
            rows.append({"name": name, "launcher_pid": proc.pid,
                         "owned_pids": sorted(descendants(proc.pid)), **selected})
        result.update(decision="PASS_PREFLIGHT_IDENTITIES", distinct_window_ids=(
            len({r["window_id"] for r in rows}) == 3))
        if not result["distinct_window_ids"]:
            result["decision"] = "FAIL_PREFLIGHT_IDENTITY_COLLISION"
    except Exception as error:
        result.update(decision="STOP_PREFLIGHT", error=repr(error))
    finally:
        all_owned = set()
        for pid in launched:
            all_owned.update(descendants(pid))
        for pid in sorted(all_owned, reverse=True):
            try:
                os.kill(pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
            except PermissionError:
                pass
        time.sleep(.3)
        states = process_states()
        still = [pid for pid in sorted(all_owned) if pid in states and states[pid]["state"] != "Z"]
        zombies = [pid for pid in sorted(all_owned) if pid in states and states[pid]["state"] == "Z"]
        result["owned_pids"] = sorted(all_owned)
        result["pids_nonrunning_after_cleanup"] = not still
        result["remaining_pids"] = still
        result["zombie_pids_reaped_by_container_init"] = zombies
        result["x_socket_absent_after_cleanup"] = not Path("/tmp/.X11-unix/X142").exists()
        raw = json.dumps(result, sort_keys=True, indent=2).encode()
        (OUT / "result.json").write_bytes(raw + b"\n")
        (OUT / "sha256.txt").write_text(hashlib.sha256(raw + b"\n").hexdigest() + "  result.json\n")
    print(json.dumps(result, sort_keys=True))
    return 0 if result["decision"] == "PASS_PREFLIGHT_IDENTITIES" and result["pids_nonrunning_after_cleanup"] and result["x_socket_absent_after_cleanup"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
