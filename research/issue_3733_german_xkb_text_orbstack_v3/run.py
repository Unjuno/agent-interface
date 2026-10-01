from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, "/src")
import Xlib
from Xlib import XK, display
from runtime.backends.x11_v1.backend import X11Backend, X11BackendError

ROOT = Path("/harness")
OUT = Path(sys.argv[1])
ALLOCATION = "issue3733-german-xkb-text-orbstack-formal-03"
IMAGE = "agent-interface-2972@sha256:69bc215db0514ee1bc4f730cceb296ecef89e4418cea8d4b2fc2ca3101101e27"
BASE = "4b2e84b79633281138b6f72c70e98d5fe9a5bf95"
FORMULA = "=B2*A2"
UNSUPPORTED = "=B2*A2€"
LAYOUTS = [("de-00", "de"), ("de-01", "de"), ("de-02", "de"), ("us-control", "us")]


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def dump_json(path: Path, obj) -> None:
    path.write_text(json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def command(argv: list[str], env: dict[str, str], timeout: float = 12.0) -> dict:
    p = subprocess.run(argv, env=env, capture_output=True, text=True, timeout=timeout, check=False)
    return {"argv": argv, "returncode": p.returncode, "stdout": p.stdout, "stderr": p.stderr}


def source_manifest() -> dict:
    manifest = json.loads((ROOT / "source_manifest.json").read_text(encoding="utf-8"))
    for rel, expected in manifest["files"].items():
        actual = sha((Path("/src") / rel).read_bytes())
        if actual != expected:
            raise RuntimeError(f"SOURCE_SHA_MISMATCH:{rel}:{actual}")
    if manifest["base_commit"] != BASE or manifest["candidate_blob"] != "9cae101a219348077668c8fc086acf8e13154afe":
        raise RuntimeError("SOURCE_IDENTITY_MISMATCH")
    return manifest


def layout(query: str) -> str | None:
    match = re.search(r"(?m)^layout:\s*(\S+)", query)
    return match.group(1) if match else None


def xlib_snapshot(d) -> dict:
    info = d.display.info
    mapping = [list(row) for row in d.get_keyboard_mapping(info.min_keycode, info.max_keycode - info.min_keycode + 1)]
    symbols = {}
    for char, name in (("=", "equal"), ("*", "asterisk"), ("y", "y"), ("z", "z")):
        code = d.keysym_to_keycode(XK.string_to_keysym(name))
        symbols[char] = {
            "keysym_name": name,
            "keycode": int(code),
            "level0": int(d.keycode_to_keysym(code, 0)),
            "level1": int(d.keycode_to_keysym(code, 1)),
        }
    return {
        "mapping": mapping,
        "mapping_sha256": sha(json.dumps(mapping, separators=(",", ":")).encode()),
        "symbols": symbols,
    }


def xkb_dump(display_name: str, env: dict[str, str], path: Path) -> dict:
    result = command(["xkbcomp", "-xkb", display_name, "-"], env)
    path.write_text(result["stdout"], encoding="utf-8")
    return result


def parse_events(text: str) -> list[dict]:
    result = []
    for block in re.split(r"(?m)(?=^(?:KeyPress|KeyRelease) event,)", text):
        kind = re.match(r"(?m)^(KeyPress|KeyRelease) event,", block)
        if not kind:
            continue
        key = re.search(r"keycode\s+(\d+)\s+\(keysym\s+0x[0-9a-fA-F]+,\s*([^)]+)\)", block)
        state = re.search(r"(?m)^\s*state\s+0x([0-9a-fA-F]+)", block)
        lookup = re.search(r"XLookupString gives \d+ bytes: \(([^)]*)\)", block)
        payload = ""
        if lookup and lookup.group(1).strip():
            try:
                payload = bytes.fromhex(lookup.group(1)).decode("ascii")
            except (ValueError, UnicodeDecodeError):
                payload = "<non-ascii>"
        result.append({
            "type": kind.group(1),
            "keycode": int(key.group(1)) if key else None,
            "keysym": key.group(2).strip() if key else None,
            "state": int(state.group(1), 16) if state else None,
            "lookup_ascii": payload,
        })
    return result


def proc_ticks(pid: int) -> str | None:
    try:
        return Path(f"/proc/{pid}/stat").read_text().split()[21]
    except (OSError, IndexError):
        return None


def stop_process(proc, log=None) -> dict:
    pid, ticks = proc.pid, proc_ticks(proc.pid)
    if proc.poll() is None:
        proc.terminate()
    try:
        rc = proc.wait(timeout=4)
    except subprocess.TimeoutExpired:
        proc.kill()
        rc = proc.wait(timeout=4)
    if log:
        log.flush()
        log.close()
    return {"pid": pid, "start_ticks": ticks, "returncode": rc, "reaped": proc.poll() is not None}


def launch_xev(display_name: str, env: dict[str, str], case_dir: Path):
    path = case_dir / "xev.log"
    log = path.open("wb")
    proc = subprocess.Popen(["stdbuf", "-oL", "xev", "-event", "keyboard"], env=env,
                            stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT)
    deadline = time.monotonic() + 8
    try:
        while time.monotonic() < deadline:
            if proc.poll() is not None:
                raise RuntimeError(f"XEV_EXITED:{proc.returncode}")
            content = path.read_text(encoding="utf-8", errors="replace")
            ids = re.search(r"Outer window is 0x([0-9a-fA-F]+),\s*inner window is 0x([0-9a-fA-F]+)", content, re.I)
            if ids:
                return proc, log, path, int(ids.group(1), 16), int(ids.group(2), 16)
            time.sleep(0.05)
        raise RuntimeError("XEV_WINDOW_ID_TIMEOUT")
    except Exception:
        stop_process(proc, log)
        raise


def run_case(case_id: str, requested_layout: str, number: int, out: Path) -> dict:
    case_dir = out / "cases" / case_id
    case_dir.mkdir(parents=True, exist_ok=False)
    display_name = f":{number}"
    env = os.environ.copy()
    env["DISPLAY"] = display_name
    xvfb_args = ["/usr/bin/Xvfb", display_name, "-screen", "0", "800x600x24", "-nolisten", "tcp",
                 "+extension", "XKEYBOARD", "+extension", "XTEST", "-noreset"]
    xvfb_log = (case_dir / "xvfb.log").open("wb")
    xvfb = subprocess.Popen(xvfb_args, env=env, stdin=subprocess.DEVNULL, stdout=xvfb_log, stderr=subprocess.STDOUT)
    anchor = None
    xev = None
    xev_log = None
    backend = None
    row = {"case_id": case_id, "requested_layout": requested_layout, "display": display_name,
           "xvfb_argv": xvfb_args, "xvfb_pid": xvfb.pid, "xvfb_start_ticks": proc_ticks(xvfb.pid),
           "status": "STOP_SETUP_EXCEPTION"}
    try:
        deadline = time.monotonic() + 8
        while time.monotonic() < deadline:
            if xvfb.poll() is not None:
                raise RuntimeError(f"XVFB_EXITED:{xvfb.returncode}")
            try:
                anchor = display.Display(display_name)
                break
            except Exception:
                time.sleep(0.05)
        if anchor is None:
            raise RuntimeError("XVFB_CONNECT_TIMEOUT")
        row["extensions"] = {"XKEYBOARD": bool(anchor.query_extension("XKEYBOARD").present),
                              "XTEST": bool(anchor.has_extension("XTEST"))}
        if not all(row["extensions"].values()):
            row["status"] = "STOP_X11_EXTENSION_MISSING"
            return row

        baseline_query = command(["setxkbmap", "-query"], env)
        row["baseline_query"] = baseline_query
        (case_dir / "baseline.query.txt").write_text(baseline_query["stdout"], encoding="utf-8")
        baseline_dump = xkb_dump(display_name, env, case_dir / "baseline.server.xkb")
        baseline_client = xlib_snapshot(anchor)
        row["baseline_dump_returncode"] = baseline_dump["returncode"]
        row["baseline_dump_sha256"] = sha(baseline_dump["stdout"].encode())
        row["baseline_client"] = baseline_client
        if baseline_query["returncode"] != 0 or layout(baseline_query["stdout"]) != "us" or baseline_dump["returncode"] != 0:
            row["status"] = "STOP_BASELINE_NOT_US_OR_DUMP_FAILED"
            return row

        # Start a private receiver while the anchor connection and -noreset server are live.
        xev, xev_log, xev_path, outer, inner = launch_xev(display_name, env, case_dir)
        row["receiver"] = {"pid": xev.pid, "start_ticks": proc_ticks(xev.pid), "outer_window": outer,
                           "inner_window": inner, "implementation": "xev XLookupString"}

        if requested_layout == "de":
            applied = command(["setxkbmap", "-layout", "de"], env)
            row["apply"] = applied
            dump_json(case_dir / "apply.json", applied)
            after_query = command(["setxkbmap", "-query"], env)
            row["after_query"] = after_query
            (case_dir / "after.query.txt").write_text(after_query["stdout"], encoding="utf-8")
            after_dump = xkb_dump(display_name, env, case_dir / "after.server.xkb")
            row["after_dump_returncode"] = after_dump["returncode"]
            row["after_dump_sha256"] = sha(after_dump["stdout"].encode())
            fresh = display.Display(display_name)
            row["after_client"] = xlib_snapshot(fresh)
            fresh.close()
            row["query_layout"] = layout(after_query["stdout"])
            row["server_dump_changed"] = baseline_dump["stdout"] != after_dump["stdout"]
            row["client_core_map_changed"] = baseline_client["mapping"] != row["after_client"]["mapping"]
            if not (applied["returncode"] == 0 and after_query["returncode"] == 0 and row["query_layout"] == "de"
                    and after_dump["returncode"] == 0 and row["server_dump_changed"]):
                row["status"] = "STOP_GERMAN_LAYOUT_NOT_ACTIVE"
                return row
        else:
            row["query_layout"] = "us"
            row["server_dump_changed"] = False
            row["client_core_map_changed"] = False

        # Preserve full live map, including the expected US/German core-map relation.
        candidate_display = display.Display(display_name)
        row["candidate_client"] = xlib_snapshot(candidate_display)
        candidate_display.close()
        backend = X11Backend(display_name, {"receiver": inner})
        try:
            row["candidate_plan"] = backend._text_plan(FORMULA)
            row["candidate_plan_keycodes"] = [[backend._keycode(key) for key in chord] for chord in row["candidate_plan"]]
            row["candidate_plan_error"] = None
        except X11BackendError as exc:
            row["candidate_plan"] = None
            row["candidate_plan_keycodes"] = None
            row["candidate_plan_error"] = str(exc)

        unsupported_error = None
        try:
            backend.preflight({"ops": [{"op": "focus", "target": "receiver"}, {"op": "text", "text": UNSUPPORTED}]})
        except X11BackendError as exc:
            unsupported_error = str(exc)
        time.sleep(0.15)
        preflight_log = xev_path.read_text(encoding="utf-8", errors="replace")
        (case_dir / "unsupported.preflight.xev.txt").write_text(preflight_log, encoding="utf-8")
        preflight_events = parse_events(preflight_log)
        row["unsupported_control"] = {
            "payload": UNSUPPORTED, "refused": unsupported_error is not None, "error": unsupported_error,
            "emissions_after": backend.emissions,
            "receiver_keypresses_after": sum(e["type"] == "KeyPress" for e in preflight_events),
        }

        if row["candidate_plan_error"] is not None:
            row["status"] = "FAIL_CANDIDATE_TEXT_PLAN"
            row["receiver_events"] = preflight_events
            row["receiver_text"] = ""
            return row

        if not (unsupported_error and "U+20AC" in unsupported_error and backend.emissions == 0
                and row["unsupported_control"]["receiver_keypresses_after"] == 0):
            row["status"] = "FAIL_UNSUPPORTED_PREFLIGHT_EMITTED_OR_ACCEPTED"
            row["receiver_events"] = preflight_events
            row["receiver_text"] = ""
            return row

        valid_error = None
        try:
            backend.preflight({"ops": [{"op": "focus", "target": "receiver"}, {"op": "text", "text": FORMULA}]})
        except X11BackendError as exc:
            valid_error = str(exc)
        if valid_error:
            row["status"] = "FAIL_VALID_FORMULA_PREFLIGHT"
            row["valid_preflight_error"] = valid_error
            return row
        backend.focus("receiver")
        row["emissions_before_text"] = backend.emissions
        backend.text(FORMULA)
        row["emissions_after_text"] = backend.emissions
        deadline = time.monotonic() + 4
        receiver_text = ""
        observed = []
        while time.monotonic() < deadline:
            time.sleep(0.05)
            event_text = xev_path.read_text(encoding="utf-8", errors="replace")
            observed = parse_events(event_text)
            receiver_text = "".join(e["lookup_ascii"] for e in observed if e["type"] == "KeyPress")
            if len(observed) >= 2 * sum(len(chord) for chord in row["candidate_plan"]):
                break
        row["receiver_events"] = observed
        row["receiver_text"] = receiver_text
        expected_text = FORMULA
        expected_count = 2 * sum(len(chord) for chord in row["candidate_plan"])
        row["status"] = "EXECUTED" if receiver_text == expected_text and len(observed) == expected_count else "FAIL_RECEIVER_TEXT_OR_EVENT_COUNT"
    except Exception as exc:
        row["error"] = f"{type(exc).__name__}:{exc}"
    finally:
        if backend is not None:
            try:
                backend.close()
            except Exception as exc:
                row["backend_close_error"] = repr(exc)
        if xev is not None:
            row["xev_process"] = stop_process(xev, xev_log)
            xev_log = None
            if (case_dir / "xev.log").exists():
                row["event_log_sha256"] = sha((case_dir / "xev.log").read_bytes())
        elif xev_log is not None:
            xev_log.close()
        if anchor is not None:
            try:
                anchor.close()
            except Exception:
                pass
        row["xvfb_process"] = stop_process(xvfb, xvfb_log)
        row["xvfb_log_sha256"] = sha((case_dir / "xvfb.log").read_bytes())
    return row


def main() -> int:
    if any(OUT.iterdir()):
        raise SystemExit("STOP_OUTPUT_DIRECTORY_NOT_EMPTY")
    manifest = source_manifest()
    OUT.mkdir(parents=True, exist_ok=True)
    raw = {
        "schema": "agent-interface/issue-3733-german-xkb-text-v3",
        "allocation": ALLOCATION, "source_base": BASE,
        "candidate_blob": manifest["candidate_blob"],
        "candidate_sha256": manifest["candidate_sha256"],
        "source_manifest_sha256": sha((ROOT / "source_manifest.json").read_bytes()),
        "runner_sha256": sha(Path(__file__).read_bytes()),
        "image_ref": IMAGE, "platform": "linux/arm64", "container_network": "none",
        "xvfb_reset_mode": "-noreset", "rows": [],
    }
    for index, (case_id, requested_layout) in enumerate(LAYOUTS):
        row = run_case(case_id, requested_layout, 211 + index, OUT)
        raw["rows"].append(row)
        if row["status"].startswith("STOP_"):
            break
    raw["disposition"] = (
        "STOP" if any(r["status"].startswith("STOP_") for r in raw["rows"])
        else "FAIL" if any(r["status"].startswith("FAIL_") for r in raw["rows"])
        else "EXECUTED_PENDING_INDEPENDENT_AUDIT" if len(raw["rows"]) == len(LAYOUTS)
        else "HOLD_INCOMPLETE"
    )
    # Inventory only completed, stable artifacts; raw.json is written exactly once afterward.
    raw["artifact_sha256"] = {
        p.relative_to(OUT).as_posix(): sha(p.read_bytes())
        for p in sorted(OUT.rglob("*")) if p.is_file()
    }
    dump_json(OUT / "raw.json", raw)
    print(json.dumps({"allocation": ALLOCATION, "disposition": raw["disposition"],
                      "rows": [{"case_id": r["case_id"], "status": r["status"]} for r in raw["rows"]]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
