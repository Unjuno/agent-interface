"""One-shot Calc launcher/window-owner process-group lifecycle allocation."""
from __future__ import annotations

import hashlib
import json
import os
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path


DISPLAY = ":143"
ALLOC = "issue3657-launcher-reap-order-formal-01"


def stat_record(pid: int) -> dict | None:
    try:
        raw = Path(f"/proc/{pid}/stat").read_text()
        comm_end = raw.rfind(") ")
        fields = raw[comm_end + 2:].split()
        return {"pid": pid, "comm": raw[raw.find("(") + 1:comm_end],
                "state": fields[0], "ppid": int(fields[1]),
                "pgid": int(fields[2]), "sid": int(fields[3]),
                "start_ticks": fields[19]}
    except (OSError, ValueError, IndexError):
        return None


def process_record(pid: int) -> dict | None:
    record = stat_record(pid)
    if record is None:
        return None
    try:
        record["cmdline"] = Path(f"/proc/{pid}/cmdline").read_bytes().replace(
            b"\0", b" ").decode("utf-8", "replace").strip()
    except OSError:
        record["cmdline"] = None
    return record


def group_snapshot(pgid: int) -> list[dict]:
    rows = []
    for p in Path("/proc").iterdir():
        if not p.name.isdigit():
            continue
        record = process_record(int(p.name))
        if record and record["pgid"] == pgid:
            rows.append(record)
    return sorted(rows, key=lambda x: x["pid"])


def run(argv: list[str], env: dict, timeout: float = 8) -> dict:
    try:
        p = subprocess.run(argv, env=env, text=True, capture_output=True,
                           timeout=timeout, check=False)
        return {"argv": argv, "returncode": p.returncode,
                "stdout": p.stdout.strip(), "stderr": p.stderr.strip()}
    except Exception as exc:
        return {"argv": argv, "returncode": None, "stdout": "",
                "stderr": repr(exc)}


def windows(env: dict) -> list[dict]:
    q = run(["xdotool", "search", "--onlyvisible", "--name", ".*"], env)
    rows = []
    for xid in q["stdout"].splitlines():
        if not xid.strip().isdigit():
            continue
        title = run(["xdotool", "getwindowname", xid.strip()], env)["stdout"]
        owner_text = run(["xdotool", "getwindowpid", xid.strip()], env)["stdout"]
        props = run(["xprop", "-id", xid.strip(), "_NET_WM_PID", "WM_CLASS"], env)
        rows.append({"xid": int(xid), "title": title,
                     "owner_pid": int(owner_text) if owner_text.isdigit() else None,
                     "xprop": props["stdout"],
                     "probe_returncodes": [q["returncode"]]})
    return sorted(rows, key=lambda x: x["xid"])


def visible_xid(env: dict, xid: int) -> bool:
    return xid in [r["xid"] for r in windows(env)]


def digest(raw: dict) -> str:
    return hashlib.sha256(json.dumps(raw, sort_keys=True,
                                     separators=(",", ":")).encode()).hexdigest()


def main(outdir: str) -> int:
    outpath = Path(outdir)
    outpath.mkdir(parents=True, exist_ok=True)
    source_dir = Path(__file__).resolve().parent
    freeze = json.loads((source_dir / "FREEZE.json").read_text())
    source_manifest = json.loads((source_dir / "SOURCE_MANIFEST.json").read_text())
    manifest_bytes = (source_dir / "SOURCE_MANIFEST.json").read_bytes()
    manifest_hash = hashlib.sha256(manifest_bytes).hexdigest()
    if manifest_hash != freeze.get("source_manifest_sha256"):
        raise RuntimeError("source manifest digest differs from frozen value")
    manifest_root = source_dir if source_dir.name == "src" else source_dir.parents[3]
    for rel, expected in source_manifest.get("files", {}).items():
        rel_path = Path(rel)
        source_path = (manifest_root / rel_path.relative_to("research/integration/issue_3657_launcher_reap_order_v1")
                       if source_dir.name == "src" else manifest_root / rel_path)
        actual = hashlib.sha256(source_path.read_bytes()).hexdigest()
        if actual != expected:
            raise RuntimeError("frozen source file digest differs: " + rel)
    if os.environ.get("ISSUE_IMAGE_ID") != freeze.get("image_id"):
        raise RuntimeError("image ID differs from frozen value")
    if os.environ.get("ISSUE_SOURCE_COMMIT") != freeze.get("source_base_commit"):
        raise RuntimeError("source commit differs from frozen value")
    root = Path(tempfile.mkdtemp(prefix="issue3657-reap-order-"))
    for name in ("home", "config", "cache", "runtime", "lo"):
        (root / name).mkdir(mode=0o700)
    xauth = root / "Xauthority"
    xauth.touch(mode=0o600)
    env = os.environ.copy()
    env.update(DISPLAY=DISPLAY, XAUTHORITY=str(xauth), HOME=str(root / "home"),
               XDG_CONFIG_HOME=str(root / "config"),
               XDG_CACHE_HOME=str(root / "cache"),
               XDG_RUNTIME_DIR=str(root / "runtime"),
               SAL_USE_VCLPLUGIN="gen", GDK_BACKEND="x11")
    # This Xvfb display is private to the network-disabled disposable
    # container; no host display is mounted.
    auth = {"returncode": 0, "method": "Xvfb -ac on private container display",
            "display_number": DISPLAY[1:], "host_display_mounted": False}
    xproc = sentinel = launcher = None
    raw = {"allocation_id": ALLOC, "display": DISPLAY, "image_platform_expected": "linux/arm64",
           "source_base_commit": freeze["source_base_commit"],
           "image_id_asserted": os.environ.get("ISSUE_IMAGE_ID"),
           "operations": {"geometry": 0, "focus": 0, "input": 0, "model": 0, "network": 0},
           "xauth_add": auth, "launch": {}, "window_owner": None,
           "group_members_before": [], "termination": {}, "samples_after": [],
           "sentinel": {}, "cleanup": {}, "decision": None}
    unit_env = os.environ.copy()
    unit_env["PYTHONDONTWRITEBYTECODE"] = "1"
    unit_env["PYTHONPATH"] = str(source_dir)
    unit = subprocess.run([sys.executable, "-m", "unittest", "test_audit"],
                          cwd=source_dir, env=unit_env, text=True,
                          capture_output=True, timeout=30, check=False)
    raw["audit_unit_tests"] = {"returncode": unit.returncode,
                               "stdout": unit.stdout, "stderr": unit.stderr}
    if unit.returncode != 0:
        raw["decision"] = "HOLD_PROCESS_OWNERSHIP_UNRESOLVED"
        raw["error"] = "frozen independent-audit unit controls failed"
        raw["raw_sha256"] = digest(raw)
        (outpath / "raw.json").write_text(json.dumps(raw, sort_keys=True, indent=2) + "\n")
        print(json.dumps({"decision": raw["decision"], "error": raw["error"]}, sort_keys=True))
        return 0
    try:
        xlog = (outpath / "xvfb.log").open("wb")
        xproc = subprocess.Popen(["Xvfb", DISPLAY, "-screen", "0", "1600x1000x24",
                                  "-ac"], env=env,
                                 stdout=xlog, stderr=subprocess.STDOUT,
                                 start_new_session=True)
        raw["xvfb_start"] = process_record(xproc.pid)
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline and not Path("/tmp/.X11-unix/X143").exists():
            time.sleep(.05)
        if not Path("/tmp/.X11-unix/X143").exists():
            raw["decision"] = "STOP_PRIVATE_CALC_NOT_READY"
            raw["error"] = "Xvfb socket did not appear"
        else:
            slog = (outpath / "sentinel.log").open("wb")
            sentinel = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(90)"],
                                        stdout=slog, stderr=subprocess.STDOUT,
                                        start_new_session=True)
            raw["sentinel"]["launch"] = process_record(sentinel.pid)
            lolog = (outpath / "libreoffice.log").open("wb")
            launcher = subprocess.Popen(
                ["libreoffice", "--norestore", "--nofirststartwizard",
                 f"-env:UserInstallation=file://{root / 'lo'}", "--calc"],
                env=env, stdout=lolog, stderr=subprocess.STDOUT,
                start_new_session=True)
            raw["launch"] = {"pid": launcher.pid,
                             "start": process_record(launcher.pid),
                             "pgid_expected": launcher.pid,
                             "sid_expected": launcher.pid,
                             "argv": ["libreoffice", "--norestore",
                                      "--nofirststartwizard",
                                      f"-env:UserInstallation=file://{root / 'lo'}",
                                      "--calc"]}
            deadline = time.monotonic() + 30
            candidates = []
            owner = None
            while time.monotonic() < deadline:
                candidates = [w for w in windows(env)
                              if "libreoffice calc" in w["title"].casefold()]
                if len(candidates) == 1:
                    owner = process_record(candidates[0]["owner_pid"] or -1)
                    if owner:
                        break
                if launcher.poll() is not None:
                    break
                time.sleep(.2)
            raw["window_candidates_before"] = candidates
            if len(candidates) != 1 or not owner:
                raw["decision"] = "STOP_PRIVATE_CALC_NOT_READY"
                raw["error"] = "no unique visible Calc owner process"
            else:
                pgid = launcher.pid
                raw["window_owner"] = {**candidates[0], "proc": owner}
                raw["launch"]["poll_before_termination"] = launcher.poll()
                raw["group_members_before"] = group_snapshot(pgid)
                raw["sentinel"]["identity_before"] = process_record(sentinel.pid)
                raw["sentinel"]["alive_before"] = sentinel.poll() is None
                raw["termination"] = {"target_pgid": pgid,
                                       "signal": "SIGTERM",
                                       "attempts": 1,
                                       "sent_at_monotonic": time.monotonic(),
                                       "os_killpg_returned": False}
                try:
                    os.killpg(pgid, signal.SIGTERM)
                    raw["termination"]["os_killpg_returned"] = True
                except ProcessLookupError:
                    raw["termination"]["error"] = "process_group_missing"
                # Reap the direct launcher immediately after the single group
                # signal. This is the sole protocol difference from #3644.
                try:
                    launcher.wait(timeout=1.0)
                    raw["launch"]["reap_during_protocol"] = True
                    raw["launch"]["reap_returncode"] = launcher.returncode
                except subprocess.TimeoutExpired:
                    raw["launch"]["reap_during_protocol"] = False
                    raw["launch"]["reap_timeout_s"] = 1.0
                observation_started = time.monotonic()
                deadline = observation_started + 5
                owner_key = (owner["pid"], owner["start_ticks"])
                while time.monotonic() < deadline:
                    members = group_snapshot(pgid)
                    owner_now = stat_record(owner_key[0])
                    owner_same = bool(owner_now and owner_now["start_ticks"] == owner_key[1])
                    xid_alive = visible_xid(env, candidates[0]["xid"])
                    raw["samples_after"].append({"elapsed_s": round(time.monotonic() - observation_started, 4),
                                                  "group_members": members,
                                                  "owner_same_identity_alive": owner_same,
                                                  "xid_visible": xid_alive})
                    if not members and not owner_same and not xid_alive:
                        break
                    time.sleep(.1)
                raw["sentinel"]["alive_after_group_signal"] = sentinel.poll() is None
                raw["launch"]["poll_after_group_signal"] = launcher.poll()
                if launcher.poll() is None:
                    try:
                        launcher.wait(timeout=.2)
                    except subprocess.TimeoutExpired:
                        pass
                raw["launch"]["reaped"] = launcher.poll() is not None
                last = raw["samples_after"][-1] if raw["samples_after"] else {}
                group_empty = not last.get("group_members")
                owner_gone = not last.get("owner_same_identity_alive", True)
                xid_gone = not last.get("xid_visible", True)
                group_bound = (owner.get("pgid") == pgid and owner.get("sid") == pgid
                               and any(m["pid"] == owner["pid"]
                                       and m["start_ticks"] == owner["start_ticks"]
                                       for m in raw["group_members_before"]))
                if not group_bound:
                    decision = "FAIL_PROCESS_GROUP_CLEANUP"
                elif not owner_gone or not xid_gone or not raw["sentinel"]["alive_after_group_signal"]:
                    decision = "FAIL_PROCESS_GROUP_CLEANUP"
                elif not raw["termination"]["os_killpg_returned"] or not group_empty:
                    decision = "HOLD_PROCESS_OWNERSHIP_UNRESOLVED"
                elif owner_gone and xid_gone and group_empty and raw["sentinel"]["alive_after_group_signal"]:
                    decision = "PASS_PRIVATE_PROCESS_GROUP_CLEANUP_SCOPED"
                else:
                    decision = "HOLD_PROCESS_OWNERSHIP_UNRESOLVED"
                raw["decision"] = decision
    except BaseException as exc:
        raw["decision"] = raw.get("decision") or "HOLD_PROCESS_OWNERSHIP_UNRESOLVED"
        raw["error"] = repr(exc)
    finally:
        # This phase is after the frozen LO process-group decision. Each support
        # process is stopped only by its exact owned PID/session.
        if sentinel is not None:
            raw["sentinel"]["pre_cleanup_alive"] = sentinel.poll() is None
            if sentinel.poll() is None:
                os.killpg(sentinel.pid, signal.SIGTERM)
            try:
                sentinel.wait(timeout=3)
            except subprocess.TimeoutExpired:
                raw["sentinel"]["wait_timeout"] = True
            raw["sentinel"]["returncode"] = sentinel.poll()
            raw["sentinel"]["reaped"] = sentinel.poll() is not None
        if launcher is not None:
            raw["cleanup"]["launcher_returncode"] = launcher.poll()
            raw["cleanup"]["launcher_reaped"] = launcher.poll() is not None
        if xproc is not None:
            if xproc.poll() is None:
                xproc.terminate()
            try:
                xproc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                raw["cleanup"]["xvfb_wait_timeout"] = True
            raw["cleanup"]["xvfb_returncode"] = xproc.poll()
            raw["cleanup"]["xvfb_reaped"] = xproc.poll() is not None
        raw["cleanup"]["x_socket_absent"] = not Path("/tmp/.X11-unix/X143").exists()
        raw["cleanup"]["xvfb_reaped"] = xproc is not None and xproc.poll() is not None
        if raw.get("decision") is None:
            raw["decision"] = "HOLD_PROCESS_OWNERSHIP_UNRESOLVED"
        if raw.get("decision") == "PASS_PRIVATE_PROCESS_GROUP_CLEANUP_SCOPED":
            complete = (raw.get("launch", {}).get("reaped") is True
                        and raw.get("sentinel", {}).get("reaped") is True
                        and raw.get("cleanup", {}).get("xvfb_reaped") is True
                        and raw.get("cleanup", {}).get("x_socket_absent") is True)
            if not complete:
                raw["decision"] = "HOLD_PROCESS_OWNERSHIP_UNRESOLVED"
    raw["raw_sha256"] = digest(raw)
    (outpath / "raw.json").write_text(json.dumps(raw, sort_keys=True, indent=2) + "\n")
    print(json.dumps({"decision": raw["decision"], "raw_sha256": raw["raw_sha256"],
                      "owner": raw.get("window_owner"),
                      "cleanup": raw.get("cleanup")}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1]))
