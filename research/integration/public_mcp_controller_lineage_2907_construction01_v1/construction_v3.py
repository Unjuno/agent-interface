"""No-model local construction probe for Issue #2907 controller/session lineage.

All app observations, dispatches and receipts share one caller-owned runtime
session. This is a boundary construction check, not the frozen four-transition
formal allocation and not a public-MCP/controller composition.
"""
import hashlib
import json
import os
import re
import subprocess
import time
from pathlib import Path

from runtime.cli_v1.api import dispatch_in_session
from runtime.cli_v1.observe import observe_in_session
from runtime.selector_v1 import open_session


def run(argv, env, timeout=12):
    return subprocess.run(argv, env=env, text=True, capture_output=True,
                          timeout=timeout, check=False)


def descendants(root_pid):
    owned = {int(root_pid)}
    changed = True
    while changed:
        changed = False
        for entry in Path("/proc").iterdir():
            if not entry.name.isdigit():
                continue
            try:
                raw = (entry / "stat").read_text()
                ppid = int(raw[raw.rfind(")") + 2:].split()[1])
            except (OSError, ValueError, IndexError):
                continue
            if ppid in owned and int(entry.name) not in owned:
                owned.add(int(entry.name))
                changed = True
    return owned


def owned_window(pid, before, env, class_hint):
    deadline = time.monotonic() + 24
    while time.monotonic() < deadline:
        q = run(["xdotool", "search", "--onlyvisible", "--name", ".*"], env)
        for raw in q.stdout.split():
            try:
                wid = int(raw)
            except ValueError:
                continue
            if wid in before:
                continue
            p = run(["xprop", "-id", str(wid), "_NET_WM_PID", "WM_CLASS"], env)
            match = re.search(r"_NET_WM_PID\(CARDINAL\) = (\d+)", p.stdout)
            owner = int(match.group(1)) if match else None
            if owner in descendants(pid) and class_hint in p.stdout.lower():
                g = run(["xdotool", "getwindowgeometry", str(wid)], env)
                dims = re.search(r"Geometry: (\d+)x(\d+)", g.stdout)
                if dims and min(map(int, dims.groups())) >= 100:
                    return wid
        time.sleep(.25)
    raise RuntimeError("OWNED_VISIBLE_WINDOW_NOT_FOUND:" + str(pid))


def main():
    out = Path(os.environ["OUTPUT_DIR"])
    out.mkdir(parents=True, exist_ok=False)
    env = dict(os.environ, DISPLAY=":142")
    targets = {}
    lineage = {"session_id": None, "observations": [], "dispatches": [],
               "authority_granted": False}
    session = None
    xvfb = subprocess.Popen(
        ["Xvfb", ":142", "-screen", "0", "1600x1000x24"],
        env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    wm = None
    apps = []
    try:
        time.sleep(0.5)
        wm = subprocess.Popen(["openbox", "--replace"], env=env,
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(0.5)
        for name, argv in [
            ("inkscape", ["inkscape"]),
            ("calc", ["libreoffice", "--norestore", "--nolockcheck",
                      "-env:UserInstallation=file:///tmp/lo-lineage", "--calc"]),
            ("chromium", ["chromium", "--no-sandbox", "--disable-gpu",
                          "--disable-dev-shm-usage",
                          "--user-data-dir=/tmp/chrome-lineage", "about:blank"]),
        ]:
            before = set()
            q = run(["xdotool", "search", "--onlyvisible", "--name", ".*"], env)
            before = {int(x) for x in q.stdout.split() if x.isdigit()}
            proc = subprocess.Popen(argv, env=env, stdout=subprocess.DEVNULL,
                                    stderr=subprocess.DEVNULL)
            apps.append(proc)
            class_hint = {"inkscape": "inkscape", "calc": "libreoffice-calc",
                          "chromium": "chromium"}[name]
            targets[name] = owned_window(proc.pid, before, env, class_hint)

        session = open_session(targets, display_name=":142")
        lineage["session_object_identity"] = id(session)
        lineage["backend_object_identity"] = id(session.backend)
        lineage["session_id"] = hashlib.sha256(
            f"{id(session)}:{id(session.backend)}:{os.environ.get('HOSTNAME','container')}".encode()
        ).hexdigest()[:24]
        for seq, target in enumerate(("inkscape", "calc", "chromium"), start=1):
            row = observe_in_session(session, target=target, frame="window_client",
                                     region=[0, 0, 320, 160],
                                     capture_directory=str(out / "images"))
            obs = row.get("observation", {})
            lineage["observations"].append({
                "target": target, "sequence": seq, "status": row.get("status"),
                "window_id": targets[target], "binding_revision": 1,
                "observation": obs,
                "image_sha256": obs.get("image_sha256"),
                "side_effect_authority": row.get("side_effect_authority"),
                "input_dispatched": row.get("input_dispatched")})

        stale = {
            "schema": "agent-interface/program-v1", "program_id": "stale-lineage",
            "source": {"observation_seq": 1, "binding_revision": 1},
            "authority": {"lease_id": "construction-bounded-probe",
                          "expires_at_ns": time.monotonic_ns() + 5_000_000_000},
            "terminal": {"release_all_required": True},
            "ops": [{"op": "key_chord", "keys": ["A"]},
                    {"op": "release_all"}]}
        denied = dispatch_in_session(session, stale, current_observation_seq=3,
                                     current_binding_revision=1,
                                     capture_directory=str(out / "dispatch-images"))
        lineage["dispatches"].append({"case": "stale-observation", "receipt": denied})
        if denied.get("result", {}).get("error") != "STALE_OBSERVATION":
            raise RuntimeError("STALE_CONTROL_DID_NOT_REACH_OBSERVATION_GATE")
        fresh = dict(stale, program_id="fresh-neutral", source={
            "observation_seq": 3, "binding_revision": 1}, authority={
                "lease_id": "construction-bounded-probe",
                "expires_at_ns": time.monotonic_ns() + 5_000_000_000},
            ops=[{"op": "key_chord", "keys": ["ESC"]},
                 {"op": "release_all"}])
        accepted = dispatch_in_session(session, fresh, current_observation_seq=3,
                                       current_binding_revision=1,
                                       capture_directory=str(out / "dispatch-images"))
        lineage["dispatches"].append({"case": "fresh-neutral-no-lease", "receipt": accepted})
        if accepted.get("result", {}).get("status") != "completed":
            raise RuntimeError("FRESH_NEUTRAL_DISPATCH_NOT_COMPLETED")
        release = session.backend.release_all()
        lineage["release"] = release
        lineage["cleanup"] = {"apps_terminated": len(apps), "xvfb_alive_before_cleanup": xvfb.poll() is None,
                              "owned_pids": sorted(set().union(*(descendants(p.pid) for p in apps)))}
        encoded = json.dumps(lineage, sort_keys=True, indent=2).encode() + b"\n"
        (out / "lineage.json").write_bytes(encoded)
        print(json.dumps({"decision": "CONSTRUCTION_COMPLETE", "session_id": lineage["session_id"],
                          "observation_statuses": [x["status"] for x in lineage["observations"]],
                          "dispatch_statuses": [x["receipt"].get("result", {}).get("status")
                                                for x in lineage["dispatches"]],
                          "release": release}, sort_keys=True))
    except Exception as error:
        lineage["stop"] = repr(error)
        (out / "lineage.json").write_text(json.dumps(lineage, sort_keys=True, indent=2) + "\n")
        print(json.dumps({"decision": "STOP_CONSTRUCTION", "error": repr(error)}))
        raise
    finally:
        if session is not None:
            session.backend.close()
        if wm is not None and wm.poll() is None:
            wm.terminate()
        for proc in reversed(apps):
            if proc.poll() is None:
                proc.terminate()
        if xvfb.poll() is None:
            xvfb.terminate()


if __name__ == "__main__":
    main()

