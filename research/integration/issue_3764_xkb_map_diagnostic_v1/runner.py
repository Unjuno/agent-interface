"""One-shot, no-input XKB server/client map diagnostic for Issue #3764."""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time

ALLOCATION = "issue3733-german-xkb-map-diagnostic-formal-01"
BASE_COMMIT = "4b2e84b79633281138b6f72c70e98d5fe9a5bf95"
IMAGE = "agent-interface-2972@sha256:69bc215db0514ee1bc4f730cceb296ecef89e4418cea8d4b2fc2ca3101101e27"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def core_map(display_obj):
    info = display_obj.display.info
    rows = display_obj.get_keyboard_mapping(
        info.min_keycode, info.max_keycode - info.min_keycode + 1)
    return {"min_keycode": int(info.min_keycode), "max_keycode": int(info.max_keycode),
            "rows": [[int(keysym) for keysym in row] for row in rows]}


def summarize_symbols(mapping):
    from Xlib import XK
    wanted = {XK.string_to_keysym(name): name
              for name in ("y", "Y", "z", "Z", "equal", "asterisk")}
    found = {name: [] for name in sorted(wanted.values())}
    for offset, row in enumerate(mapping["rows"]):
        for level, symbol in enumerate(row):
            name = wanted.get(int(symbol))
            if name is not None:
                found[name].append({"keycode": mapping["min_keycode"] + offset,
                                    "level": level, "keysym": int(symbol)})
    return found


def layout_matches(query_text, layout):
    return bool(re.search(rf"(?m)^layout:\s+{re.escape(layout)}\s*$", query_text))


def map_fingerprint(mapping):
    encoded = json.dumps(mapping, sort_keys=True, separators=(",", ":")).encode()
    return sha(encoded)


def command(argv, env, timeout=12):
    proc = subprocess.run(argv, env=env, capture_output=True, timeout=timeout)
    return {"argv": argv, "exit": proc.returncode,
            "stdout": proc.stdout.decode("utf-8", "replace"),
            "stderr": proc.stderr.decode("utf-8", "replace")}


def query_core(display_name):
    from Xlib import display
    client = display.Display(display_name)
    try:
        mapping = core_map(client)
        return {"mapping": mapping, "sha256": map_fingerprint(mapping),
                "symbols": summarize_symbols(mapping)}
    finally:
        client.close()


def capture_state(display_name, env, directory, label):
    from Xlib import display
    query = command(["setxkbmap", "-query", "-display", display_name], env)
    server = command(["xkbcomp", "-xkb", display_name, "-"], env, timeout=20)
    (directory / f"{label}.setxkbmap.json").write_text(json.dumps(query, sort_keys=True, indent=2) + "\n")
    (directory / f"{label}.xkbcomp.stdout").write_text(server["stdout"])
    (directory / f"{label}.xkbcomp.stderr").write_text(server["stderr"])
    # Two new client connections provide a repeated direct core-map query.
    first = query_core(display_name)
    second = query_core(display_name)
    (directory / f"{label}.xlib-1.json").write_text(json.dumps(first, sort_keys=True, indent=2) + "\n")
    (directory / f"{label}.xlib-2.json").write_text(json.dumps(second, sort_keys=True, indent=2) + "\n")
    return {"setxkbmap": query, "xkbcomp": {"argv": server["argv"], "exit": server["exit"],
            "stdout_sha256": sha(server["stdout"].encode()),
            "stderr_sha256": sha(server["stderr"].encode())},
            "xlib_1": first, "xlib_2": second}


def stop_server(proc, log_stream):
    pid = proc.pid
    try:
        start_ticks = Path(f"/proc/{pid}/stat").read_text().split()[21]
    except (OSError, IndexError):
        start_ticks = None
    if proc.poll() is None:
        proc.terminate()
    try:
        rc = proc.wait(timeout=4)
    except subprocess.TimeoutExpired:
        proc.kill()
        rc = proc.wait(timeout=4)
    log_stream.flush()
    log_stream.close()
    return {"pid": pid, "start_ticks": start_ticks, "returncode": rc,
            "reaped": proc.poll() is not None}


def file_inventory(root):
    return {p.relative_to(root).as_posix(): sha(p.read_bytes())
            for p in sorted(root.rglob("*")) if p.is_file() and p.name != "raw.json"}


def main():
    output = Path(sys.argv[1]).resolve()
    if output.exists() and any(output.iterdir()):
        raise SystemExit("STOP_OUTPUT_NOT_EMPTY")
    output.mkdir(parents=True, exist_ok=True)
    import Xlib
    result = {"schema": "agent-interface/issue3764-xkb-map-diagnostic-v1",
              "allocation": ALLOCATION, "base_commit": BASE_COMMIT,
              "runner_sha256": sha(Path(__file__).read_bytes()),
              "image": IMAGE, "platform": "linux/arm64",
              "python": sys.version, "xlib_version": str(getattr(Xlib, "__version__", "unknown")),
              "network": "none", "rows": [], "disposition": "STOP"}
    layouts = [("de-01", "de"), ("de-02", "de"), ("de-03", "de"), ("us-control", "us")]
    errors = []
    for index, (case_id, layout) in enumerate(layouts):
        case_dir = output / "cases" / case_id
        case_dir.mkdir(parents=True)
        display_name = f":{171 + index}"
        env = dict(os.environ, DISPLAY=display_name)
        log_stream = (case_dir / "xvfb.log").open("wb")
        xvfb_argv = ["Xvfb", display_name, "-screen", "0", "800x600x24",
                     "-nolisten", "tcp", "-noreset"]
        server = subprocess.Popen(xvfb_argv,
                                  stdout=log_stream, stderr=subprocess.STDOUT, env=env)
        row = {"case_id": case_id, "layout": layout, "display": display_name,
               "xvfb_pid": server.pid, "xvfb_argv": xvfb_argv, "status": "IN_PROGRESS"}
        try:
            ready = False
            for _ in range(80):
                if server.poll() is not None:
                    break
                probe = subprocess.run(["xdpyinfo", "-display", display_name], env=env,
                                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=2)
                if probe.returncode == 0:
                    ready = True
                    break
                time.sleep(0.1)
            if not ready:
                row["status"] = "STOP_XVFB_NOT_READY"
                row["xvfb_exit_before_ready"] = server.poll()
                errors.append(row["status"])
                continue
            row["baseline"] = capture_state(display_name, env, case_dir, "baseline")
            if row["baseline"]["setxkbmap"]["exit"] != 0 or row["baseline"]["xkbcomp"]["exit"] != 0:
                row["status"] = "STOP_BASELINE_QUERY_FAILED"
                errors.append(row["status"])
                continue
            baseline_layout = row["baseline"]["setxkbmap"]["stdout"]
            if not layout_matches(baseline_layout, "us"):
                row["status"] = "STOP_BASELINE_LAYOUT_NOT_US"
                errors.append(row["status"])
                continue
            if layout == "de":
                row["apply"] = command(["setxkbmap", "-display", display_name, "-layout", "de"], env)
                time.sleep(0.25)
                if row["apply"]["exit"] != 0:
                    row["status"] = "STOP_GERMAN_APPLY_FAILED"
                    errors.append(row["status"])
                    continue
            else:
                row["apply"] = {"argv": None, "exit": 0,
                                "stdout": "US control; no layout mutation applied", "stderr": ""}
            row["after"] = capture_state(display_name, env, case_dir, "after")
            if row["after"]["setxkbmap"]["exit"] != 0 or row["after"]["xkbcomp"]["exit"] != 0:
                row["status"] = "STOP_AFTER_QUERY_FAILED"
                errors.append(row["status"])
                continue
            row["comparison"] = {
                "xkbcomp_dump_changed": row["baseline"]["xkbcomp"]["stdout_sha256"] != row["after"]["xkbcomp"]["stdout_sha256"],
                "xlib_core_map_changed": row["baseline"]["xlib_1"]["sha256"] != row["after"]["xlib_1"]["sha256"],
                "xlib_fresh_connections_agree_baseline": row["baseline"]["xlib_1"]["sha256"] == row["baseline"]["xlib_2"]["sha256"],
                "xlib_fresh_connections_agree_after": row["after"]["xlib_1"]["sha256"] == row["after"]["xlib_2"]["sha256"],
                "server_layout_after": row["after"]["setxkbmap"]["stdout"],
                "server_layout_matches_requested": layout_matches(
                    row["after"]["setxkbmap"]["stdout"], layout),
                "symbols_baseline": row["baseline"]["xlib_1"]["symbols"],
                "symbols_after": row["after"]["xlib_1"]["symbols"]}
            row["status"] = "CAPTURED"
        except Exception as exc:
            row["status"] = "STOP_DIAGNOSTIC_EXCEPTION"
            row["error"] = f"{type(exc).__name__}:{exc}"
            errors.append(row["status"])
        finally:
            row["xvfb_cleanup"] = stop_server(server, log_stream)
            row["case_artifacts_sha256"] = file_inventory(case_dir)
            result["rows"].append(row)
            (output / "raw.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
        if row["status"] != "CAPTURED":
            break
    if len(result["rows"]) == len(layouts) and all(r["status"] == "CAPTURED" for r in result["rows"]):
        # Diagnostic PASS means all independent capture paths completed and fresh clients agree;
        # it deliberately does not require German to alter core mappings.
        if not all(r["comparison"]["xlib_fresh_connections_agree_baseline"] and
                   r["comparison"]["xlib_fresh_connections_agree_after"] for r in result["rows"]):
            result["disposition"] = "STOP_FRESH_CLIENT_QUERY_DISAGREEMENT"
        elif not all(r["comparison"]["server_layout_matches_requested"] for r in result["rows"]):
            result["disposition"] = "STOP_SERVER_LAYOUT_MISMATCH"
        elif any(r["comparison"]["xkbcomp_dump_changed"] != r["comparison"]["xlib_core_map_changed"]
                 for r in result["rows"] if r["layout"] == "de"):
            result["disposition"] = "STOP_SERVER_CLIENT_MAP_DISAGREEMENT"
        else:
            result["disposition"] = "PASS_DIAGNOSTIC"
    else:
        result["disposition"] = errors[0] if errors else "STOP_INCOMPLETE_ROWS"
    result["errors"] = errors
    result["artifact_sha256"] = file_inventory(output)
    (output / "raw.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    print(json.dumps({"allocation": ALLOCATION, "disposition": result["disposition"],
                      "rows": [{"case_id": r["case_id"], "status": r["status"],
                                "comparison": r.get("comparison")} for r in result["rows"]]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
