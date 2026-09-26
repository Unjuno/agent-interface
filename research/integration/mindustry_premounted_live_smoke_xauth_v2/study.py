#!/usr/bin/env python3
"""Issue #4454: Xauthority-only successor to the #2624 live-smoke STOP."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import signal
import subprocess
import tempfile
import time

from Xlib import display as xdisplay

EXPECTED = {
    "jar": {"name": "Mindustry.jar", "bytes": 87022576, "sha256": "7f210295dfffb4c17b582b27bab41f4dde83f557f00f0877572fdac943f40539"},
    "save": {"name": "canonical.msav", "sha256": "8fff67b0c130ee59a3838c92754b73225a506902bd4838dcc3f1fb5be286cbed"},
    "mod_json": {"name": "mod/mod.json", "sha256": "4b8e413ab0c4561c82edd8e422c517b631f1baee79a0b008adb42e9624965e05", "git_blob": "137ae8036b7864af744565bbc1c2af566290ea92"},
    "main_js": {"name": "mod/scripts/main.js", "sha256": "7b5bd06bc34db9655e3946a9c202948cdaa0a4b233e0eec1fe063aa8358c220f", "git_blob": "84e9a0c291d5b7f454d6092f2c100728a9a16da2"},
    "save_git_blob": "7663b25633d853a257fbb407723fe85579120111",
}
EXPECTED_ORACLE = {"width": 300, "height": 250, "paused": True, "core_present": True, "copper": 200}
PASS_OUTCOME = "PASS_MINDUSTRY_PREMOUNTED_LIVE_SMOKE_XAUTH_SCOPED"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def git_blob(path: Path) -> str:
    data = path.read_bytes()
    hdr = f"blob {len(data)}\0".encode()
    return hashlib.sha1(hdr + data).hexdigest()


def write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def wait_until(fn, timeout: float, interval: float = 0.05) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            if fn():
                return True
        except Exception:
            pass
        time.sleep(interval)
    return False


def pick_display() -> int:
    for n in range(220, 280):
        if not Path(f"/tmp/.X11-unix/X{n}").exists() and not Path(f"/tmp/.X{n}-lock").exists():
            return n
    raise RuntimeError("no private X display available")


def x_connectable(name: str) -> bool:
    try:
        d = xdisplay.Display(name)
        d.close()
        return True
    except Exception:
        return False


def server_neutral(name: str) -> dict:
    d = xdisplay.Display(name)
    try:
        root = d.screen().root
        q = root.query_pointer()
        keymap = d.query_keymap()
        # X core modifier/button masks live in low bits of pointer mask; no XTEST input is emitted by this study.
        button_mask = int(q.mask) & 0x1F00
        any_key = any(byte != 0 for byte in keymap)
        return {"pointer_mask": int(q.mask), "button_mask": button_mask, "any_key_down": bool(any_key), "neutral": button_mask == 0 and not any_key}
    finally:
        d.close()


def process_identity(path: str) -> dict:
    rp = shutil.which(path) if "/" not in path else path
    p = Path(rp).resolve() if rp else None
    out = {"requested": path, "resolved": str(p) if p else None}
    if p and p.is_file():
        out["sha256"] = sha256(p)
    return out


def verify_fixture(root: Path) -> dict:
    files = {
        "jar": root / "Mindustry.jar",
        "save": root / "canonical.msav",
        "mod_json": root / "mod" / "mod.json",
        "main_js": root / "mod" / "scripts" / "main.js",
        "acquisition": root / "acquisition.txt",
    }
    missing = [k for k,p in files.items() if not p.is_file()]
    if missing:
        raise RuntimeError(f"missing fixture files: {missing}")
    obs = {
        k: {"path": str(p), "bytes": p.stat().st_size, "sha256": sha256(p)}
        for k,p in files.items()
    }
    obs["save"]["git_blob"] = git_blob(files["save"])
    obs["mod_json"]["git_blob"] = git_blob(files["mod_json"])
    obs["main_js"]["git_blob"] = git_blob(files["main_js"])
    errors = []
    if obs["jar"]["bytes"] != EXPECTED["jar"]["bytes"] or obs["jar"]["sha256"] != EXPECTED["jar"]["sha256"]:
        errors.append("jar_identity")
    if obs["save"]["sha256"] != EXPECTED["save"]["sha256"] or obs["save"]["git_blob"] != EXPECTED["save_git_blob"]:
        errors.append("save_identity")
    for key in ("mod_json", "main_js"):
        if obs[key]["sha256"] != EXPECTED[key]["sha256"] or obs[key]["git_blob"] != EXPECTED[key]["git_blob"]:
            errors.append(f"{key}_identity")
    acq = files["acquisition"].read_text(encoding="utf-8")
    required = [
        "schema=mindustry-2624-premounted-fixture-v1",
        "jar_asset_id=559668837",
        f"jar_size={EXPECTED['jar']['bytes']}",
        f"jar_sha256={EXPECTED['jar']['sha256']}",
        f"save_sha256={EXPECTED['save']['sha256']}",
        f"save_git_blob={EXPECTED['save_git_blob']}",
        f"mod_json_git_blob={EXPECTED['mod_json']['git_blob']}",
        f"main_js_git_blob={EXPECTED['main_js']['git_blob']}",
    ]
    missing_acq = [s for s in required if s not in acq]
    if missing_acq:
        errors.append("acquisition_manifest:" + ",".join(missing_acq))
    obs["errors"] = errors
    if errors:
        raise RuntimeError("fixture identity gate failed: " + repr(errors))
    return obs


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fixture", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--allocation-id", required=True)
    ap.add_argument("--source-commit", required=True)
    args = ap.parse_args()
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=False)

    started_ns = time.monotonic_ns()
    fixture = verify_fixture(args.fixture.resolve())
    shutil.copy2(args.fixture / "acquisition.txt", out / "acquisition.txt")
    write_json(out / "asset_manifest.json", fixture)

    temp = Path(tempfile.mkdtemp(prefix="mindustry2624-"))
    display_num = pick_display()
    display_name = f":{display_num}"
    env = os.environ.copy()
    parent_xauthority = os.environ.get("XAUTHORITY")
    xauthority = temp / "Xauthority"
    xauthority.touch(mode=0o600)
    os.chmod(xauthority, 0o600)
    os.environ["XAUTHORITY"] = str(xauthority)
    env["XAUTHORITY"] = str(xauthority)
    home = temp / "home"
    data = home / "mindustry"
    for p in (home, temp / "xdg-config", temp / "xdg-cache", temp / "xdg-data", temp / "xdg-runtime", data / "mods"):
        p.mkdir(parents=True, exist_ok=True)
    shutil.copytree(args.fixture / "mod", data / "mods" / "interface-reset-study")
    shutil.copy2(args.fixture / "canonical.msav", data / "input.msav")
    env.update({
        "DISPLAY": display_name,
        "HOME": str(home),
        "XDG_CONFIG_HOME": str(temp / "xdg-config"),
        "XDG_CACHE_HOME": str(temp / "xdg-cache"),
        "XDG_DATA_HOME": str(temp / "xdg-data"),
        "XDG_RUNTIME_DIR": str(temp / "xdg-runtime"),
        "MINDUSTRY_DATA_DIR": str(data),
        "LIBGL_ALWAYS_SOFTWARE": "1",
        "SDL_VIDEODRIVER": "x11",
        "SDL_AUDIODRIVER": "dummy",
        "ALSOFT_DRIVERS": "null",
        "LANG": "C.UTF-8",
        "LC_ALL": "C.UTF-8",
    })
    env.pop("PULSE_SERVER", None)

    procs = []
    forced = []
    record = {
        "allocation_id": args.allocation_id,
        "source_commit": args.source_commit,
        "formal_invocations": 1,
        "model_calls": 0,
        "provider_calls": 0,
        "controller_calls": 0,
        "task_input_calls": 0,
        "started_ns": started_ns,
        "display": display_name,
        "platform": platform.platform(),
        "python": platform.python_version(),
        "fixture": fixture,
        "parent_xauthority": parent_xauthority,
        "xauthority": {"path": str(xauthority), "exists_at_launch": xauthority.is_file(), "mode": oct(xauthority.stat().st_mode & 0o777)},
        "process_identities": {k: process_identity(k) for k in ("java", "Xvfb", "openbox", "wmctrl")},
        "env_subset": {k: env.get(k) for k in ("DISPLAY","XAUTHORITY","HOME","XDG_CONFIG_HOME","XDG_CACHE_HOME","XDG_DATA_HOME","XDG_RUNTIME_DIR","MINDUSTRY_DATA_DIR","LIBGL_ALWAYS_SOFTWARE","SDL_VIDEODRIVER","SDL_AUDIODRIVER","ALSOFT_DRIVERS","LANG","LC_ALL")},
    }

    def spawn(cmd, *, stdout=None, stderr=None):
        p = subprocess.Popen(cmd, env=env, start_new_session=True, stdout=stdout, stderr=stderr)
        procs.append(p)
        return p

    xvfb_out = (out / "xvfb.stdout.txt").open("w", encoding="utf-8")
    xvfb_err = (out / "xvfb.stderr.txt").open("w", encoding="utf-8")
    ob_out = (out / "openbox.stdout.txt").open("w", encoding="utf-8")
    ob_err = (out / "openbox.stderr.txt").open("w", encoding="utf-8")
    game_out = (out / "mindustry.stdout.txt").open("w", encoding="utf-8")
    game_err = (out / "mindustry.stderr.txt").open("w", encoding="utf-8")

    outcome = "STOP_INFRASTRUCTURE"
    try:
        xvfb_cmd = ["Xvfb", display_name, "-screen", "0", "1280x800x24", "-ac", "-nolisten", "tcp", "-noreset"]
        xvfb = spawn(xvfb_cmd, stdout=xvfb_out, stderr=xvfb_err)
        record["xvfb"] = {"pid": xvfb.pid, "command": xvfb_cmd}
        if not wait_until(lambda: x_connectable(display_name), 5.0):
            raise RuntimeError("Xvfb not connectable")
        ob_cmd = ["openbox", "--config-file", "/etc/xdg/openbox/rc.xml"]
        ob = spawn(ob_cmd, stdout=ob_out, stderr=ob_err)
        record["openbox"] = {"pid": ob.pid, "command": ob_cmd}
        time.sleep(0.4)

        pre_neutral = server_neutral(display_name)
        record["pre_input_state"] = pre_neutral
        jar = args.fixture.resolve() / "Mindustry.jar"
        java = shutil.which("java") or "/usr/bin/java"
        game_cmd = [java, "-Xmx768m", f"-Duser.home={home}", "-jar", str(jar)]
        record["mindustry"] = {"command": game_cmd}
        game_start_ns = time.monotonic_ns()
        game = spawn(game_cmd, stdout=game_out, stderr=game_err)
        record["mindustry"]["pid"] = game.pid
        record["mindustry"]["started_ns"] = game_start_ns

        ready = wait_until(lambda: (data / "ready.txt").is_file() or game.poll() is not None, 60.0, 0.1)
        record["wait_completed"] = bool(ready)
        record["ready"] = (data / "ready.txt").is_file()
        record["ready_ns"] = time.monotonic_ns() if record["ready"] else None
        win = subprocess.run(["wmctrl", "-l"], env=env, text=True, capture_output=True, timeout=5)
        (out / "windows.txt").write_text(win.stdout, encoding="utf-8")
        record["window_listing_exit"] = win.returncode
        record["mindustry_window"] = any("mindustry" in line.lower() for line in win.stdout.splitlines())
        record["game_poll_at_ready"] = game.poll()

        if (data / "ready.txt").is_file():
            shutil.copy2(data / "ready.txt", out / "ready.txt")
        if (data / "oracle.json").is_file():
            shutil.copy2(data / "oracle.json", out / "oracle.json")
            oracle = json.loads((out / "oracle.json").read_text(encoding="utf-8"))
            record["oracle"] = {
                "width": oracle.get("width"), "height": oracle.get("height"),
                "paused": oracle.get("paused"), "core_present": oracle.get("core_present"),
                "copper": oracle.get("copper"),
                "tile_rows": len(oracle.get("tiles", [])) if isinstance(oracle.get("tiles"), list) else None,
                "row_widths_ok": (all(isinstance(r, list) and len(r) == EXPECTED_ORACLE["width"] for r in oracle.get("tiles", []))
                                  if isinstance(oracle.get("tiles"), list) else False),
            }
        else:
            record["oracle"] = None

        record["pre_cleanup_input_state"] = server_neutral(display_name)

        if game.poll() is None:
            os.killpg(game.pid, signal.SIGTERM)
            try:
                game.wait(timeout=10)
                record["mindustry"]["forced_kill"] = False
            except subprocess.TimeoutExpired:
                os.killpg(game.pid, signal.SIGKILL)
                game.wait(timeout=5)
                record["mindustry"]["forced_kill"] = True
                forced.append("mindustry")
        else:
            record["mindustry"]["forced_kill"] = False
        record["mindustry"]["returncode"] = game.returncode

        oracle_ok = record.get("oracle") == {
            "width": 300, "height": 250, "paused": True, "core_present": True, "copper": 200,
            "tile_rows": 250, "row_widths_ok": True,
        }
        if not record["ready"]:
            outcome = "FAIL_LIVE_FIXTURE_STARTUP"
        elif not oracle_ok or not record["mindustry_window"] or not record["pre_cleanup_input_state"]["neutral"] or forced:
            outcome = "FAIL_ORACLE_OR_CLEANUP"
        else:
            outcome = PASS_OUTCOME
    except Exception as exc:
        record["exception"] = repr(exc)
        if "fixture identity gate" in repr(exc):
            outcome = "HOLD_ASSET_OR_SOURCE_IDENTITY"
        elif "Xvfb not connectable" in repr(exc):
            outcome = "STOP_XAUTHORITY_BOOTSTRAP"
        else:
            outcome = "STOP_INFRASTRUCTURE"
    finally:
        for p in reversed(procs):
            if p.poll() is None:
                try:
                    os.killpg(p.pid, signal.SIGTERM)
                    p.wait(timeout=5)
                except Exception:
                    try:
                        os.killpg(p.pid, signal.SIGKILL)
                        p.wait(timeout=3)
                        forced.append(f"pid:{p.pid}")
                    except Exception:
                        pass
        for f in (xvfb_out,xvfb_err,ob_out,ob_err,game_out,game_err):
            f.close()
        record["forced_kill_records"] = forced
        record["processes"] = [{"pid": p.pid, "returncode": p.poll()} for p in procs]
        record["all_owned_processes_exited"] = all(p.poll() is not None for p in procs)
        record["x_socket_absent_after_cleanup"] = not Path(f"/tmp/.X11-unix/X{display_num}").exists()
        record["finished_ns"] = time.monotonic_ns()
        record["outcome"] = outcome
        write_json(out / "RESULT.json", record)
        if parent_xauthority is None:
            os.environ.pop("XAUTHORITY", None)
        else:
            os.environ["XAUTHORITY"] = parent_xauthority
        shutil.rmtree(temp, ignore_errors=True)

    print(json.dumps({"outcome": outcome, "out": str(out)}, sort_keys=True))
    return 0 if outcome == PASS_OUTCOME else 1


if __name__ == "__main__":
    raise SystemExit(main())
