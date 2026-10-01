"""No-input X11 visibility/capture construction probe for Issue #4466."""
import hashlib
import json
import os
from pathlib import Path
import select
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[3]
TARGET_APP = ROOT / "research/integration/golden_v3_second_domain_2246_v1/gtk_fixture_app.py"
DECOY_APP = ROOT / "research/integration/gtk_effect_control_3240_v1/fixture_render_decoy.py"


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def run(env, argv, timeout=5):
    return subprocess.run(argv, env=env, check=True, text=True, capture_output=True, timeout=timeout).stdout


def launch_xvfb(out):
    proc = subprocess.Popen(
        ["Xvfb", "-displayfd", "1", "-screen", "0", "800x400x24", "-nolisten", "tcp", "-ac"],
        stdout=subprocess.PIPE, stderr=(out / "xvfb.stderr").open("wb"), text=True)
    if not select.select([proc.stdout], [], [], 10)[0]:
        raise RuntimeError("Xvfb startup timeout")
    display_number = proc.stdout.readline().strip()
    if not display_number.isdigit():
        raise RuntimeError("Xvfb display identity missing")
    return proc, ":" + display_number


def private_env(display, name):
    home = Path("/tmp") / ("gtk4466-" + name)
    for path in (home, home / ".config", home / ".cache", home / ".local" / "share"):
        path.mkdir(parents=True, exist_ok=True)
    return dict(os.environ, DISPLAY=display, HOME=str(home), XDG_CONFIG_HOME=str(home / ".config"),
                XDG_CACHE_HOME=str(home / ".cache"), XDG_DATA_HOME=str(home / ".local" / "share"),
                GSETTINGS_BACKEND="memory", NO_AT_BRIDGE="1")


def launch_fixture(script, role, out, env, extra):
    meta = out / (role + "-meta.json")
    proc = subprocess.Popen(["/usr/bin/python3", str(script), "--meta", str(meta), *extra], env=env,
                            stdout=(out / (role + ".stdout")).open("wb"),
                            stderr=(out / (role + ".stderr")).open("wb"))
    deadline = time.monotonic() + 10
    while not meta.exists():
        if proc.poll() is not None or time.monotonic() >= deadline:
            raise RuntimeError(role + " fixture readiness failed")
        time.sleep(0.02)
    return proc, json.loads(meta.read_text(encoding="utf-8"))


def inspect_window(env, xid):
    from Xlib import X, display as xdisplay
    connection = xdisplay.Display(env["DISPLAY"])
    focus_reply = connection.get_input_focus()
    focus = focus_reply.focus
    focus_value = focus.id if hasattr(focus, "id") else focus
    focus_id = str(focus_value)
    connection.close()
    return {
        "xid": int(xid),
        "xprop": run(env, ["xprop", "-id", str(xid), "_NET_WM_PID", "WM_NAME", "WM_CLASS", "_NET_WM_STATE"]),
        "xwininfo": run(env, ["xwininfo", "-id", str(xid), "-all"]),
        "root_tree": run(env, ["xwininfo", "-root", "-tree"]),
        "root_active_window": run(env, ["xprop", "-root", "_NET_ACTIVE_WINDOW"]),
        "input_focus_xid": focus_id,
        "input_focus_special": "PointerRoot" if focus_value == X.PointerRoot else ("None" if focus_value == X.NONE else None),
        "input_focus_revert_to": focus_reply.revert_to,
    }


def snapshot(stage, env, xid):
    started = time.monotonic_ns()
    window = inspect_window(env, xid)
    ended = time.monotonic_ns()
    return {"stage": stage, "captured_started_ns": started,
            "captured_ended_ns": ended, "window": window}


def parse_xwd(path):
    data = path.read_bytes()
    if len(data) < 100:
        raise RuntimeError("short XWD: " + str(path))
    words = [int.from_bytes(data[i:i + 4], "big") for i in range(0, 100, 4)]
    header_size, version = words[:2]
    width, height, byte_order, bits_per_pixel, bytes_per_line = words[4], words[5], words[7], words[11], words[12]
    ncolors = words[19]
    masks = words[14:17]
    offset = header_size + ncolors * 12
    if version != 7 or bits_per_pixel % 8 or offset + height * bytes_per_line != len(data):
        raise RuntimeError("unsupported or inconsistent XWD: " + str(path))
    nbytes = bits_per_pixel // 8
    byteorder = "little" if byte_order == 0 else "big"
    rgb_mask = masks[0] | masks[1] | masks[2]
    raw_pixels = []
    rgb = []
    for y in range(height):
        for x in range(width):
            i = offset + y * bytes_per_line + x * nbytes
            raw_pixels.append(int.from_bytes(data[i:i + nbytes], byteorder))
            rgb.append(raw_pixels[-1] & rgb_mask)
    colors = len(set(rgb))
    rgb_bytes = b"".join(value.to_bytes(4, "little") for value in rgb)
    return {"sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data), "width": width,
            "height": height, "depth": words[3], "byte_order": byte_order,
            "bits_per_pixel": bits_per_pixel, "bytes_per_line": bytes_per_line,
            "rgb_masks": [hex(mask) for mask in masks], "rgb_colors": colors,
            "rgb_sha256": hashlib.sha256(rgb_bytes).hexdigest(),
            "raw_pixels": raw_pixels, "rgb": rgb}


def capture(env, out, role, stage, index, xid):
    path = out / f"{stage}-{role}-{index:02d}.xwd"
    started = time.monotonic_ns()
    subprocess.run(["xwd", "-silent", "-id", str(xid), "-out", str(path)], env=env,
                   check=True, capture_output=True, timeout=10)
    ended = time.monotonic_ns()
    parsed = parse_xwd(path)
    parsed.pop("rgb")
    parsed.pop("raw_pixels")
    return {"role": role, "stage": stage, "index": index, "xid": int(xid),
            "started_ns": started, "ended_ns": ended, "artifact": path.name, **parsed}


def compare(a, b, out):
    left, right = parse_xwd(out / a["artifact"]), parse_xwd(out / b["artifact"])
    if (left["width"], left["height"], left["rgb_masks"]) != (right["width"], right["height"], right["rgb_masks"]):
        raise RuntimeError("incompatible XWD geometry/masks")
    changed = [i for i, (x, y) in enumerate(zip(left["rgb"], right["rgb"])) if x != y]
    raw_changed = sum(x != y for x, y in zip(left["raw_pixels"], right["raw_pixels"]))
    width = left["width"]
    coords = [(i % width, i // width) for i in changed]
    bbox = None if not coords else [min(x for x, _ in coords), min(y for _, y in coords),
                                    max(x for x, _ in coords), max(y for _, y in coords)]
    return {"left": a["artifact"], "right": b["artifact"],
            "left_rgb_sha256": left["rgb_sha256"], "right_rgb_sha256": right["rgb_sha256"],
            "changed_rgb_pixels": len(changed), "changed_raw_pixel_values": raw_changed,
            "changed_ignored_bits_only": raw_changed - len(changed),
            "total_pixels": width * left["height"], "bbox": bbox}


def move_window(display, xid, x, y):
    from Xlib import X, display as xdisplay
    connection = xdisplay.Display(display)
    window = connection.create_resource_object("window", int(xid))
    window.configure(x=x, y=y, stack_mode=X.Above)
    connection.sync()
    connection.close()
    return {"xid": int(xid), "requested_x": x, "requested_y": y,
            "stack_mode": "Above", "display_sync_completed": True}


def stop_all(processes):
    results = []
    for role, proc in reversed(processes):
        if proc.poll() is None:
            proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=3)
        results.append({"role": role, "pid": proc.pid, "returncode": proc.returncode})
    return results


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--allocation", choices=["issue4466-visibility-construction-v1",
                                                   "issue4466-visibility-formal01"], required=True)
    args = parser.parse_args()
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    processes = []
    captures = []
    states = []
    try:
        xvfb, display = launch_xvfb(out)
        processes.append(("xvfb", xvfb))
        target_env = private_env(display, "target")
        target, target_meta = launch_fixture(TARGET_APP, "target", out, target_env,
                                             ["--effect", str(out / "target-effect.json"),
                                              "--events", str(out / "target-events.jsonl")])
        processes.append(("target", target))
        target_xid = target_meta["window_id"]
        states.append({"stage": "target_only", "target": snapshot("target_only", target_env, target_xid)})
        for i in range(1, 4):
            captures.append(capture(target_env, out, "target", "target_only", i, target_xid))
            time.sleep(0.25)

        decoy_env = private_env(display, "decoy")
        decoy, decoy_meta = launch_fixture(DECOY_APP, "decoy", out, decoy_env,
                                           ["--text", "gtk3240"])
        processes.append(("decoy", decoy))
        decoy_xid = decoy_meta["window_id"]
        states.append({"stage": "decoy_overlapping", "target": snapshot("decoy_overlapping", target_env, target_xid),
                       "decoy": snapshot("decoy_overlapping", decoy_env, decoy_xid)})
        for i in range(1, 4):
            captures.append(capture(target_env, out, "target", "decoy_overlapping", i, target_xid))
            captures.append(capture(decoy_env, out, "decoy", "decoy_overlapping", i, decoy_xid))
            time.sleep(0.25)

        decoy_reposition = move_window(display, decoy_xid, 400, 0)
        states.append({"stage": "decoy_moved", "target": snapshot("decoy_moved", target_env, target_xid),
                       "decoy": snapshot("decoy_moved", decoy_env, decoy_xid)})
        for i in range(1, 4):
            captures.append(capture(target_env, out, "target", "decoy_moved", i, target_xid))
            captures.append(capture(decoy_env, out, "decoy", "decoy_moved", i, decoy_xid))
            time.sleep(0.25)

        comparisons = []
        for stage in ("target_only", "decoy_overlapping", "decoy_moved"):
            target_rows = [row for row in captures if row["role"] == "target" and row["stage"] == stage]
            for first, second in zip(target_rows, target_rows[1:]):
                comparisons.append(compare(first, second, out))
        transition_comparisons = [
            compare(next(row for row in captures if row["role"] == "target" and row["stage"] == "target_only" and row["index"] == 3),
                    next(row for row in captures if row["role"] == "target" and row["stage"] == "decoy_overlapping" and row["index"] == 1), out),
            compare(next(row for row in captures if row["role"] == "target" and row["stage"] == "decoy_overlapping" and row["index"] == 3),
                    next(row for row in captures if row["role"] == "target" and row["stage"] == "decoy_moved" and row["index"] == 1), out),
        ]
        summary = {"status": "RUN_COMPLETED_PENDING_INDEPENDENT_AUDIT" if args.allocation.endswith("formal01") else "CONSTRUCTION_COMPLETED_FOR_REVIEW",
                   "allocation": args.allocation,
                   "display": display, "target_xid": target_xid, "decoy_xid": decoy_xid,
                   "target_effect_exists": (out / "target-effect.json").exists(),
                   "target_events_exist": (out / "target-events.jsonl").exists(),
                   "captures": captures, "within_stage_target_comparisons": comparisons,
                   "stage_transition_target_comparisons": transition_comparisons,
                   "decoy_reposition": decoy_reposition,
                   "state_snapshots": states, "model_calls": 0, "provider_calls": 0,
                   "input_emitter_processes": []}
        write_json(out / "run-summary.json", summary)
    finally:
        cleanup = stop_all(processes)
        write_json(out / "cleanup.json", cleanup)
    print(json.dumps({"summary": str(out / "run-summary.json"), "captures": len(captures),
                      "cleanup": cleanup}, indent=2))


if __name__ == "__main__":
    main()
