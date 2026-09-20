from __future__ import annotations

import hashlib
import json
import os
import platform
import re
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, "/src")
import Xlib  # noqa: E402
from Xlib import XK, display  # noqa: E402
from runtime.backends.x11_v1.backend import X11Backend, X11BackendError  # noqa: E402


ALLOCATION = "issue3733-german-xkb-text-orbstack-formal-01"
FORMULA = "=B2*A2"
UNSUPPORTED = "=B2*A2€"
EVIDENCE = Path("/harness")
SOURCE_ROOT = Path("/src")
LAYOUTS = [("de-00", "de"), ("de-01", "de"), ("de-02", "de"), ("us-control", "us")]


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def read_source_manifest() -> dict:
    manifest = json.loads((EVIDENCE / "source_manifest.json").read_text(encoding="utf-8"))
    for relpath, expected in manifest["files"].items():
        actual = sha256((SOURCE_ROOT / relpath).read_bytes())
        if actual != expected:
            raise RuntimeError(f"SOURCE_SHA_MISMATCH:{relpath}:{actual}")
    return manifest


def run_text(cmd: list[str], env: dict[str, str], *, timeout: float = 12.0) -> dict:
    try:
        p = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=timeout, check=False)
        return {"argv": cmd, "returncode": p.returncode, "stdout": p.stdout, "stderr": p.stderr}
    except subprocess.TimeoutExpired as exc:
        return {
            "argv": cmd,
            "returncode": None,
            "stdout": (exc.stdout or b"").decode("utf-8", "replace") if isinstance(exc.stdout, bytes) else exc.stdout or "",
            "stderr": (exc.stderr or b"").decode("utf-8", "replace") if isinstance(exc.stderr, bytes) else exc.stderr or "",
            "timeout": True,
        }


def layout_name(query: str) -> str | None:
    match = re.search(r"(?m)^layout:\s*(\S+)", query)
    return match.group(1) if match else None


def keyboard_mapping(d) -> list[list[int]]:
    info = d.display.info
    return [list(row) for row in d.get_keyboard_mapping(info.min_keycode, info.max_keycode - info.min_keycode + 1)]


def modifier_mapping(d) -> list[list[int]]:
    return [list(row) for row in d.get_modifier_mapping()]


def fingerprint(value) -> str:
    return sha256(json.dumps(value, separators=(",", ":"), sort_keys=True).encode("utf-8"))


def symbol_levels(d) -> dict:
    out = {}
    for label, name in (("=", "equal"), ("*", "asterisk")):
        code = d.keysym_to_keycode(XK.string_to_keysym(name))
        out[label] = {
            "keysym_name": name,
            "keycode": int(code),
            "level0": int(d.keycode_to_keysym(code, 0)),
            "level1": int(d.keycode_to_keysym(code, 1)),
        }
    return out


def proc_start_ticks(pid: int) -> str | None:
    try:
        fields = Path(f"/proc/{pid}/stat").read_text().split()
        return fields[21]
    except (OSError, IndexError):
        return None


def save_text(path: Path, value: str) -> None:
    path.write_text(value, encoding="utf-8", errors="replace")


def xkb_dump(display_name: str, env: dict[str, str], path: Path) -> dict:
    result = run_text(["xkbcomp", "-xkb", display_name, "-"], env, timeout=12)
    save_text(path, result["stdout"])
    return result


def launch_xev(display_name: str, env: dict[str, str], case_dir: Path):
    log_path = case_dir / "xev.log"
    log = log_path.open("wb")
    process = subprocess.Popen(
        ["stdbuf", "-oL", "xev", "-event", "keyboard"],
        env=env,
        stdin=subprocess.DEVNULL,
        stdout=log,
        stderr=subprocess.STDOUT,
    )
    deadline = time.monotonic() + 8
    text = ""
    outer = inner = None
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError(f"XEV_EXITED_EARLY:{process.returncode}")
        text = log_path.read_text(encoding="utf-8", errors="replace")
        mo = re.search(r"Outer window is 0x([0-9a-fA-F]+)", text)
        mi = re.search(r"Inner window is 0x([0-9a-fA-F]+)", text)
        if mo and mi:
            outer, inner = int(mo.group(1), 16), int(mi.group(1), 16)
            break
        time.sleep(0.05)
    if inner is None:
        process.terminate()
        try:
            process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=3)
        log.close()
        raise RuntimeError("XEV_WINDOW_ID_TIMEOUT")
    return process, log, log_path, outer, inner


def parse_xev_events(text: str) -> list[dict]:
    events = []
    blocks = re.split(r"(?m)(?=^(?:KeyPress|KeyRelease) event,)", text)
    for block in blocks:
        first = re.match(r"(?m)^(KeyPress|KeyRelease) event,", block)
        if not first:
            continue
        code = re.search(r"keycode\s+(\d+)\s+\(keysym\s+0x[0-9a-fA-F]+,\s*([^)]+)\)", block)
        state = re.search(r"(?m)^\s*state\s+0x([0-9a-fA-F]+)", block)
        lookup = re.search(r"XLookupString gives \d+ bytes: \(([^)]*)\)", block)
        payload = ""
        if lookup and lookup.group(1).strip():
            try:
                payload = bytes.fromhex(lookup.group(1)).decode("ascii")
            except (ValueError, UnicodeDecodeError):
                payload = "<non-ascii>"
        events.append({
            "type": first.group(1),
            "keycode": int(code.group(1)) if code else None,
            "keysym": code.group(2).strip() if code else None,
            "state": int(state.group(1), 16) if state else None,
            "lookup_ascii": payload,
        })
    return events


def stop_process(process, log_handle=None) -> dict:
    if process is None:
        if log_handle:
            log_handle.close()
        return {"pid": None, "returncode": None, "reaped": True, "start_ticks": None}
    pid = process.pid
    ticks = proc_start_ticks(pid)
    if process.poll() is None:
        process.terminate()
    try:
        code = process.wait(timeout=4)
    except subprocess.TimeoutExpired:
        process.kill()
        code = process.wait(timeout=4)
    if log_handle:
        log_handle.flush()
        log_handle.close()
    return {"pid": pid, "returncode": code, "reaped": process.poll() is not None, "start_ticks": ticks}


def run_case(case_id: str, layout: str, display_number: int, out: Path) -> dict:
    case_dir = out / "cases" / case_id
    case_dir.mkdir(parents=True, exist_ok=False)
    display_name = f":{display_number}"
    xvfb_log_path = case_dir / "xvfb.log"
    xvfb_log = xvfb_log_path.open("wb")
    xvfb_env = os.environ.copy()
    xvfb_env["DISPLAY"] = display_name
    xvfb = subprocess.Popen(
        ["/usr/bin/Xvfb", display_name, "-screen", "0", "800x600x24", "-nolisten", "tcp", "+extension", "XKEYBOARD", "+extension", "XTEST"],
        env=xvfb_env,
        stdin=subprocess.DEVNULL,
        stdout=xvfb_log,
        stderr=subprocess.STDOUT,
    )
    xvfb_pid, xvfb_ticks = xvfb.pid, proc_start_ticks(xvfb.pid)
    xev = None
    xev_log = None
    backend = None
    row = {
        "case_id": case_id,
        "requested_layout": layout,
        "display": display_name,
        "xvfb_argv": ["/usr/bin/Xvfb", display_name, "-screen", "0", "800x600x24", "-nolisten", "tcp", "+extension", "XKEYBOARD", "+extension", "XTEST"],
        "xvfb_pid": xvfb_pid,
        "xvfb_start_ticks": xvfb_ticks,
        "status": "STOP_SETUP_EXCEPTION",
    }
    try:
        deadline = time.monotonic() + 8
        server = None
        last_connect_error = None
        while time.monotonic() < deadline:
            if xvfb.poll() is not None:
                raise RuntimeError(f"XVFB_EXITED_EARLY:{xvfb.returncode}")
            try:
                server = display.Display(display_name)
                break
            except Exception as exc:  # connection readiness only
                last_connect_error = repr(exc)
                time.sleep(0.05)
        if server is None:
            raise RuntimeError(f"XVFB_CONNECT_TIMEOUT:{last_connect_error}")

        ext_xkb = bool(server.query_extension("XKEYBOARD").present)
        ext_xtest = bool(server.has_extension("XTEST"))
        row["extensions"] = {"XKEYBOARD": ext_xkb, "XTEST": ext_xtest}
        if not ext_xkb or not ext_xtest:
            row["status"] = "STOP_X11_EXTENSION_MISSING"
            server.close()
            return row

        baseline_query = run_text(["setxkbmap", "-query"], xvfb_env)
        save_text(case_dir / "baseline.query.txt", baseline_query["stdout"])
        baseline_dump = xkb_dump(display_name, xvfb_env, case_dir / "baseline.server.xkb")
        before_map = keyboard_mapping(server)
        before_modifiers = modifier_mapping(server)
        before_levels = symbol_levels(server)
        baseline_layout = layout_name(baseline_query["stdout"])
        row["baseline"] = {
            "query_returncode": baseline_query["returncode"],
            "layout": baseline_layout,
            "server_dump_returncode": baseline_dump["returncode"],
            "server_dump_sha256": sha256(baseline_dump["stdout"].encode()),
            "core_map_sha256": fingerprint(before_map),
            "modifier_map_sha256": fingerprint(before_modifiers),
            "symbol_levels": before_levels,
        }
        if baseline_layout != "us" or baseline_dump["returncode"] != 0:
            row["status"] = "STOP_BASELINE_NOT_US_OR_DUMP_FAILED"
            server.close()
            return row

        if layout == "de":
            apply = run_text(["setxkbmap", "-layout", "de"], xvfb_env)
            save_text(case_dir / "apply.log", json.dumps(apply, indent=2, sort_keys=True) + "\n")
            after_query = run_text(["setxkbmap", "-query"], xvfb_env)
            save_text(case_dir / "after.query.txt", after_query["stdout"])
            after_dump = xkb_dump(display_name, xvfb_env, case_dir / "after.server.xkb")
            after_map = keyboard_mapping(server)
            after_modifiers = modifier_mapping(server)
            after_levels = symbol_levels(server)
            row["apply"] = {"argv": apply["argv"], "returncode": apply["returncode"], "stdout": apply["stdout"], "stderr": apply["stderr"]}
            row["after"] = {
                "query_returncode": after_query["returncode"],
                "layout": layout_name(after_query["stdout"]),
                "server_dump_returncode": after_dump["returncode"],
                "server_dump_sha256": sha256(after_dump["stdout"].encode()),
                "core_map_sha256": fingerprint(after_map),
                "modifier_map_sha256": fingerprint(after_modifiers),
                "symbol_levels": after_levels,
                "server_changed": baseline_dump["stdout"] != after_dump["stdout"],
                "core_map_changed": before_map != after_map,
                "modifier_map_changed": before_modifiers != after_modifiers,
            }
            server.close()
            if not (
                apply["returncode"] == 0
                and row["after"]["query_returncode"] == 0
                and row["after"]["layout"] == "de"
                and row["after"]["server_dump_returncode"] == 0
                and row["after"]["server_changed"]
                and row["after"]["core_map_changed"]
            ):
                row["status"] = "STOP_SETUP_BLOCKED_NATIVE_XKB_APPLY"
                return row
            active_levels = after_levels
        else:
            server.close()
            row["after"] = row["baseline"] | {"layout": baseline_layout, "server_changed": False, "core_map_changed": False, "modifier_map_changed": False}
            active_levels = before_levels

        xev, xev_log, xev_log_path, outer_id, inner_id = launch_xev(display_name, xvfb_env, case_dir)
        row["receiver"] = {"process_pid": xev.pid, "process_start_ticks": proc_start_ticks(xev.pid), "outer_window": outer_id, "inner_window": inner_id, "implementation": "xev XLookupString"}
        backend = X11Backend(display_name, {"receiver": inner_id})
        row["active_symbol_levels"] = active_levels
        try:
            row["candidate_plan"] = backend._text_plan(FORMULA)
        except X11BackendError as exc:
            row["candidate_error"] = str(exc)
            row["status"] = "FAIL_CANDIDATE_TEXT_PLAN"
            return row
        row["candidate_plan_keycodes"] = [[backend._keycode(key) for key in chord] for chord in row["candidate_plan"]]

        unsupported_error = None
        try:
            backend.preflight({"ops": [{"op": "focus", "target": "receiver"}, {"op": "text", "text": UNSUPPORTED}]})
        except X11BackendError as exc:
            unsupported_error = str(exc)
        time.sleep(0.15)
        preflight_log = xev_log_path.read_text(encoding="utf-8", errors="replace")
        save_text(case_dir / "unsupported.preflight.xev.txt", preflight_log)
        preflight_keypress_count = len(re.findall(r"(?m)^KeyPress event,", preflight_log))
        row["unsupported_control"] = {
            "payload": UNSUPPORTED,
            "refused": unsupported_error is not None,
            "error": unsupported_error,
            "emissions_after": backend.emissions,
            "receiver_keypresses_after": preflight_keypress_count,
        }
        if not (unsupported_error and "U+20AC" in unsupported_error and backend.emissions == 0 and preflight_keypress_count == 0):
            row["status"] = "FAIL_UNSUPPORTED_PREFLIGHT_EMITTED_OR_ACCEPTED"
            return row

        valid_preflight_error = None
        try:
            backend.preflight({"ops": [{"op": "focus", "target": "receiver"}, {"op": "text", "text": FORMULA}]})
        except X11BackendError as exc:
            valid_preflight_error = str(exc)
        if valid_preflight_error:
            row["status"] = "FAIL_VALID_FORMULA_PREFLIGHT"
            row["valid_preflight_error"] = valid_preflight_error
            return row

        backend.focus("receiver")
        row["emissions_before_text"] = backend.emissions
        backend.text(FORMULA)
        row["emissions_after_text"] = backend.emissions
        deadline = time.monotonic() + 4
        text = ""
        while time.monotonic() < deadline:
            time.sleep(0.05)
            text = xev_log_path.read_text(encoding="utf-8", errors="replace")
            payloads = []
            for block in re.split(r"(?=KeyPress event,)", text)[1:]:
                match = re.search(r"XLookupString gives \d+ bytes: \(([^)]*)\)", block)
                if match and match.group(1).strip():
                    try:
                        payloads.append(bytes.fromhex(match.group(1)).decode("ascii"))
                    except (ValueError, UnicodeDecodeError):
                        payloads.append("<non-ascii>")
            if "".join(payloads) == FORMULA:
                break
        row["receiver_events"] = parse_xev_events(text)
        row["receiver_text"] = "".join(event["lookup_ascii"] for event in row["receiver_events"] if event["type"] == "KeyPress")
        row["status"] = "EXECUTED"
        row["valid_preflight_error"] = None
        row["event_log_sha256"] = sha256(xev_log_path.read_bytes())
        return row
    except Exception as exc:
        row["error"] = f"{type(exc).__name__}:{exc}"
        return row
    finally:
        if backend is not None:
            try:
                backend.close()
            except Exception as exc:
                row["backend_close_error"] = repr(exc)
        if xev is not None:
            row["xev_process"] = stop_process(xev, xev_log)
            if xev_log_path and xev_log_path.exists():
                row["event_log_sha256"] = sha256(xev_log_path.read_bytes())
        xvfb_result = stop_process(xvfb, xvfb_log)
        row["xvfb_process"] = xvfb_result
        if xvfb_log_path.exists():
            row["xvfb_log_sha256"] = sha256(xvfb_log_path.read_bytes())


def collect_artifacts(out: Path) -> dict[str, str]:
    return {
        path.relative_to(out).as_posix(): sha256(path.read_bytes())
        for path in sorted(out.rglob("*"))
        if path.is_file() and path.name != "raw.json"
    }


def main(out: Path) -> int:
    if out.exists() and any(out.iterdir()):
        print("STOP_OUTPUT_DIRECTORY_NOT_EMPTY")
        return 20
    out.mkdir(parents=True, exist_ok=True)
    source_manifest = read_source_manifest()
    runner_sha = sha256(Path(__file__).read_bytes())
    rows = []
    raw = {
        "schema": "agent-interface/issue-3733-german-xkb-text-v1",
        "allocation": ALLOCATION,
        "source_base": source_manifest["base_commit"],
        "candidate_blob": source_manifest["candidate_blob"],
        "source_manifest_sha256": sha256((EVIDENCE / "source_manifest.json").read_bytes()),
        "runner_sha256": runner_sha,
        "image_ref": "agent-interface-2972@sha256:69bc215db0514ee1bc4f730cceb296ecef89e4418cea8d4b2fc2ca3101101e27",
        "platform": "linux/arm64",
        "container_network": "none",
        "rows": rows,
        "artifact_sha256": {},
    }
    version_commands = {
        "setxkbmap": ["setxkbmap", "-version"],
        "xkbcomp": ["xkbcomp", "-version"],
        "debian_packages": ["dpkg-query", "-W", "-f=${Package}=${Version}\\n", "xvfb", "x11-xkb-utils", "xkb-data", "python3-xlib"],
    }
    runtime_info = {
        "python": sys.version,
        "platform": platform.platform(),
        "machine": platform.machine(),
        "python_xlib_version": str(getattr(Xlib, "__version__", "unknown")),
        "version_commands": {name: run_text(argv, os.environ.copy()) for name, argv in version_commands.items()},
    }
    write_json(out / "runtime.json", runtime_info)
    for index, (case_id, layout) in enumerate(LAYOUTS):
        row = run_case(case_id, layout, 131 + index, out)
        rows.append(row)
        raw["artifact_sha256"] = collect_artifacts(out)
        write_json(out / "raw.json", raw)
        if row["status"].startswith("STOP_"):
            break
        if row["status"].startswith("FAIL_UNSUPPORTED"):
            break
    raw["disposition"] = (
        "STOP" if any(row["status"].startswith("STOP_") for row in rows)
        else "FAIL" if any(row["status"].startswith("FAIL_") for row in rows)
        else "EXECUTED_PENDING_INDEPENDENT_AUDIT" if len(rows) == len(LAYOUTS) and all(row["status"] == "EXECUTED" for row in rows)
        else "HOLD_INCOMPLETE"
    )
    raw["artifact_sha256"] = collect_artifacts(out)
    write_json(out / "raw.json", raw)
    print(json.dumps({"allocation": ALLOCATION, "disposition": raw["disposition"], "rows": [{"case_id": row["case_id"], "status": row["status"]} for row in rows]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(Path(sys.argv[1])))
