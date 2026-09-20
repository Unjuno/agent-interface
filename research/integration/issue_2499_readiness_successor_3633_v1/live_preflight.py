"""One-shot live v4 identity/readiness preflight for Issue #3633."""
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

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT / "research/integration/mixed_app_identity_2666"))
from identity_gate import EXPECTED_APPS, evaluate_identities

DISPLAY = ":141"
FILTERS = {
    "inkscape": {"needle": "inkscape", "fields": ("title", "wm_class")},
    "libreoffice": {"needle": "libreoffice calc", "fields": ("title", "wm_class")},
    "chromium": {"needle": "chromium", "fields": ("title", "wm_class")},
}


def invoke(argv: list[str], env: dict[str, str], timeout: int = 12) -> dict:
    try:
        p = subprocess.run(argv, env=env, text=True, capture_output=True,
                           timeout=timeout, check=False)
        return {"argv": argv, "returncode": p.returncode,
                "stdout": p.stdout.strip(), "stderr": p.stderr.strip()}
    except Exception as exc:  # retain bounded probe errors as data
        return {"argv": argv, "returncode": None, "stdout": "",
                "stderr": repr(exc)}


def snapshot(env: dict[str, str]) -> list[dict]:
    q = invoke(["xdotool", "search", "--onlyvisible", "--name", ".*"], env)
    rows = []
    for wid in q["stdout"].splitlines():
        wid = wid.strip()
        if not wid.isdigit():
            continue
        name = invoke(["xdotool", "getwindowname", wid], env)
        pid = invoke(["xdotool", "getwindowpid", wid], env)
        wm = invoke(["xprop", "-id", wid, "WM_CLASS"], env)
        records = {"window_id": int(wid),
                   "pid": int(pid["stdout"]) if pid["stdout"].isdigit() else None,
                   "title": name["stdout"], "wm_class": wm["stdout"],
                   "display": env["DISPLAY"],
                   "probe_returncodes": [name["returncode"], pid["returncode"],
                                         wm["returncode"]]}
        rows.append(records)
    return sorted(rows, key=lambda x: x["window_id"])


def filter_rows(rows: list[dict]) -> dict[str, list[dict]]:
    selected = {}
    for app, spec in FILTERS.items():
        needle = spec["needle"].casefold()
        selected[app] = [r for r in rows if any(
            needle in str(r[field]).casefold() for field in spec["fields"])]
    return selected


def start(argv: list[str], env: dict[str, str], logdir: Path) -> subprocess.Popen:
    log = (logdir / (argv[0].replace("/", "_") + ".log")).open("wb")
    return subprocess.Popen(argv, env=env, stdout=log, stderr=subprocess.STDOUT,
                            start_new_session=True)


def digest(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True,
                                    separators=(",", ":")).encode()).hexdigest()


def main() -> int:
    output = Path(sys.argv[1])
    output.mkdir(parents=True, exist_ok=True)
    root = Path(tempfile.mkdtemp(prefix="issue3633-"))
    for name in ("home", "config", "cache", "runtime", "chrome", "lo"):
        (root / name).mkdir(mode=0o700)
    xauth = root / "Xauthority"
    xauth.touch(mode=0o600)
    env = os.environ.copy()
    env.update(DISPLAY=DISPLAY, XAUTHORITY=str(xauth), HOME=str(root / "home"),
               XDG_CONFIG_HOME=str(root / "config"),
               XDG_CACHE_HOME=str(root / "cache"),
               XDG_RUNTIME_DIR=str(root / "runtime"),
               SAL_USE_VCLPLUGIN="gen", GDK_BACKEND="x11")
    add = invoke(["xauth", "-f", str(xauth), "add", DISPLAY, ".",
                  "0123456789abcdef0123456789abcdef"], env)
    procs: list[tuple[str, subprocess.Popen]] = []
    out = {"allocation_id": "issue3633-readiness-identity-v4-formal-01",
           "display": DISPLAY, "xauth_add": add, "forbidden_operations": {
               "geometry": 0, "focus": 0, "input": 0, "model": 0, "network": 0},
           "filters": FILTERS, "apps": list(EXPECTED_APPS),
           "snapshots": {}, "selected": {}, "readiness": None,
           "processes": [], "cleanup": {}}
    unit_env = os.environ.copy()
    unit_env["PYTHONPATH"] = str(REPO_ROOT)
    unit = subprocess.run(
        [sys.executable, "-m", "unittest",
         "research.integration.mixed_app_identity_2666.test_identity_gate"],
        cwd=REPO_ROOT, env=unit_env, text=True, capture_output=True,
        timeout=30, check=False)
    out["unit_gate"] = {"command": [sys.executable, "-m", "unittest",
                                    "research.integration.mixed_app_identity_2666.test_identity_gate"],
                        "returncode": unit.returncode,
                        "stdout": unit.stdout, "stderr": unit.stderr}
    if unit.returncode != 0:
        out["decision"] = "STOP_READINESS_IDENTITY_UNAVAILABLE"
        out["error"] = "typed identity gate unit controls failed"
        out["raw_sha256"] = digest(out)
        (output / "raw.json").write_text(json.dumps(out, sort_keys=True, indent=2) + "\n")
        print(json.dumps({"decision": out["decision"], "unit_exit": unit.returncode}, sort_keys=True))
        return 2
    xvfb = start(["Xvfb", DISPLAY, "-screen", "0", "1600x1000x24",
                  "-auth", str(xauth)], env, output)
    procs.append(("xvfb", xvfb))
    launches = {
        "inkscape": ["inkscape"],
        "libreoffice": ["libreoffice", "--norestore", "--nofirststartwizard",
                        f"-env:UserInstallation=file://{root / 'lo'}", "--calc"],
        "chromium": ["chromium", "--no-sandbox", "--disable-gpu", "--no-first-run",
                     "--no-default-browser-check", "--disable-session-crashed-bubble",
                     "--user-data-dir=" + str(root / "chrome"), "about:blank"],
    }
    try:
        time.sleep(0.8)
        for app, argv in launches.items():
            p = start(argv, env, output)
            procs.append((app, p))
            out["processes"].append({"app": app, "pid": p.pid,
                                      "start_ticks": process_start_ticks(p.pid)})
            deadline = time.monotonic() + 45
            latest = []
            while time.monotonic() < deadline:
                latest = snapshot(env)
                if filter_rows(latest)[app]:
                    break
                if p.poll() is not None:
                    break
                time.sleep(0.4)
            out["snapshots"][app] = latest
        first = snapshot(env)
        time.sleep(0.6)
        second = snapshot(env)
        first_filtered, second_filtered = filter_rows(first), filter_rows(second)
        selected, repeated = {}, {}
        for app in EXPECTED_APPS:
            selected[app] = first_filtered[app][0] if len(first_filtered[app]) == 1 else first_filtered[app]
            repeated[app] = second_filtered[app][0] if len(second_filtered[app]) == 1 else second_filtered[app]
        out["snapshots"]["formal_first"] = first
        out["snapshots"]["formal_second"] = second
        out["selected"], out["repeated"] = selected, repeated
        decision = evaluate_identities(selected, repeated, display=DISPLAY)
        out["readiness"] = {"admitted": decision.admitted, "reason": decision.reason}
        out["decision"] = ("PASS_READINESS_IDENTITY_V4_SCOPED" if decision.admitted
                           else "STOP_READINESS_IDENTITY_UNAVAILABLE")
    except BaseException as exc:
        out["decision"] = "STOP_READINESS_IDENTITY_UNAVAILABLE"
        out["error"] = repr(exc)
    finally:
        for name, p in reversed(procs):
            if p.poll() is None:
                try:
                    os.killpg(p.pid, signal.SIGTERM)
                except ProcessLookupError:
                    pass
                try:
                    p.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    os.killpg(p.pid, signal.SIGKILL)
                    p.wait(timeout=5)
            out["cleanup"][name] = {"pid": p.pid, "returncode": p.poll(),
                                     "reaped": p.poll() is not None,
                                     "start_ticks": process_start_ticks(p.pid)}
        out["cleanup"]["x_socket_absent"] = not Path("/tmp/.X11-unix/X141").exists()
    out["raw_sha256"] = digest(out)
    (output / "raw.json").write_text(json.dumps(out, sort_keys=True, indent=2) + "\n")
    print(json.dumps({"decision": out["decision"], "raw_sha256": out["raw_sha256"],
                      "readiness": out.get("readiness"), "cleanup": out["cleanup"]},
                     sort_keys=True))
    return 0 if out["decision"] == "PASS_READINESS_IDENTITY_V4_SCOPED" else 2


def process_start_ticks(pid: int) -> str | None:
    try:
        return Path(f"/proc/{pid}/stat").read_text().split(") ", 1)[1].split()[19]
    except Exception:
        return None


if __name__ == "__main__":
    raise SystemExit(main())
