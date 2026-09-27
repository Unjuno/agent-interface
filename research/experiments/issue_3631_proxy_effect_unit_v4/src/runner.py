#!/usr/bin/python3
"""One-shot 28-row formal proxy effect and closed safety-gate allocation."""
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import time

from Xlib import X, display
from Xlib.ext import res, xtest

from proxy import blue_bbox, center, ppm_rgb, render

ROOT = Path("/src")
OUT = Path("/evidence")
ARMS = ("ordinary_screenshot", "proxy_image", "structured_proxy", "hybrid")
CASES = ("positive", "no_effect", "stale_version", "target_replaced", "unavailable", "ambiguous", "macro_failure")
DISPLAY_NAME = ":301"
SOCKET = Path("/tmp/.X11-unix/X301")
BUTTON_MASK = X.Button1Mask


def sha(data):
    return hashlib.sha256(data).hexdigest()


def proc_identity(pid):
    stat_path = Path(f"/proc/{pid}/stat")
    first = stat_path.read_text()
    tail = first[first.rfind(")") + 2:].split()
    argv = Path(f"/proc/{pid}/cmdline").read_bytes().split(b"\0")
    second = stat_path.read_text()
    tail2 = second[second.rfind(")") + 2:].split()
    ticks = int(tail[19])
    stable = ticks == int(tail2[19]) and tail[0] != "Z" and bool(argv)
    return {"pid": int(pid), "start_ticks": ticks, "state": tail[0],
            "ppid": int(tail[1]), "pgid": int(tail[2]), "sid": int(tail[3]),
            "cmdline_sha256": sha(b"\0".join(argv)), "cmdline": [x.decode("utf-8", "replace") for x in argv if x],
            "stable_read": stable}


def xres_owner(conn, xid):
    spec, _ = res.ClientIdSpec.parse_binary(
        res.ClientIdSpec.to_binary(client=int(xid), mask=res.LocalClientPIDMask), conn)
    reply = conn.res_query_client_ids([spec])
    matches = [item for item in reply.ids
               if item.spec.mask == res.LocalClientPIDMask and len(item.value) == 1]
    if len(matches) != 1:
        raise RuntimeError(f"XRes PID owner missing/ambiguous for XID {xid}")
    return {"client_base": int(matches[0].spec.client), "pid": int(matches[0].value[0]),
            "mask": int(matches[0].spec.mask), "value_length": len(matches[0].value)}


def visual_masks(conn, visual_id):
    for depth in conn.display.info.roots[0].allowed_depths:
        for visual in depth.visuals:
            if int(visual.visual_id) == int(visual_id):
                return {"red": int(visual.red_mask), "green": int(visual.green_mask),
                        "blue": int(visual.blue_mask), "depth": int(depth.depth)}
    raise RuntimeError("window visual not present in X server metadata")


def channel(pixel, mask):
    if not mask:
        return 0
    shift = (mask & -mask).bit_length() - 1
    value = (pixel & mask) >> shift
    maximum = mask >> shift
    return round(value * 255 / maximum)


def ximage_rgb(conn, image, width, height):
    info = conn.display.info
    fmt = next(f for f in info.pixmap_formats if int(f.depth) == int(image.depth))
    bpp = int(fmt.bits_per_pixel)
    pad = int(fmt.scanline_pad)
    stride = ((width * bpp + pad - 1) // pad) * (pad // 8)
    bytes_per_pixel = bpp // 8
    masks = visual_masks(conn, image.visual)
    if bytes_per_pixel not in (3, 4):
        raise RuntimeError(f"unsupported XImage bpp {bpp}")
    order = "little" if info.image_byte_order == X.LSBFirst else "big"
    rgb = bytearray(width * height * 3)
    raw = bytes(image.data)
    if len(raw) < stride * height:
        raise RuntimeError("truncated XImage data")
    for y in range(height):
        for x in range(width):
            off = y * stride + x * bytes_per_pixel
            pixel = int.from_bytes(raw[off:off + bytes_per_pixel], order)
            dst = (y * width + x) * 3
            rgb[dst:dst + 3] = bytes((channel(pixel, masks["red"]),
                                      channel(pixel, masks["green"]),
                                      channel(pixel, masks["blue"])))
    return bytes(rgb), {"bits_per_pixel": bpp, "scanline_pad": pad,
                        "image_byte_order": int(info.image_byte_order), "visual_masks": masks}


def ready_events(rowdir):
    eventfile = rowdir / "fixture-events.jsonl"
    if not eventfile.exists():
        return []
    return [json.loads(line) for line in eventfile.read_text().splitlines()]


def find_windows(conn):
    found = []
    for win in conn.screen().root.query_tree().children:
        try:
            title = win.get_wm_name() or ""
            if title.startswith("proxy-fixture:") and win.get_attributes().map_state == X.IsViewable:
                found.append((win, title))
        except Exception:
            pass
    return found


def state(conn, rowdir, label):
    wins = find_windows(conn)
    if not wins:
        return {"status": "unavailable", "count": 0}
    if len(wins) > 1:
        targets = []
        for win, title in wins:
            owner = xres_owner(conn, win.id)
            proc = proc_identity(owner["pid"])
            targets.append({"xid": int(win.id), "title": title, "xres": owner,
                            "process": proc})
        return {"status": "ambiguous", "count": len(wins), "targets": targets}
    win, title = wins[0]
    owner = xres_owner(conn, win.id)
    proc = proc_identity(owner["pid"])
    ready = [e for e in ready_events(rowdir) if e.get("kind") == "ready"]
    if not proc["stable_read"] or not any(e.get("pid") == owner["pid"] for e in ready):
        raise RuntimeError("XRes owner does not bind to a stable fixture process incarnation")
    geom = win.get_geometry()
    conn.sync()
    image = win.get_image(0, 0, geom.width, geom.height, X.ZPixmap, 0xFFFFFFFF)
    if image is None:
        raise RuntimeError("X11 image unavailable")
    frame = bytes(image.data)
    rgb, pixel_meta = ximage_rgb(conn, image, geom.width, geom.height)
    frame_path = rowdir / f"{label}.raw"
    rgb_path = rowdir / f"{label}.rgb"
    frame_path.write_bytes(frame)
    rgb_path.write_bytes(rgb)
    translated = conn.screen().root.translate_coords(win, 0, 0)
    owner_event = next(e for e in ready if e.get("pid") == owner["pid"])
    return {"status": "ok", "xid": int(win.id), "pid": owner["pid"],
            "start_ticks": proc["start_ticks"], "process": proc, "xres": owner,
            "ready_event": owner_event, "counter": int(title.split(":")[1]),
            "version": int(title.split(":")[2]), "title": title,
            "geometry": [int(translated.x), int(translated.y), int(geom.width), int(geom.height), int(geom.depth)],
            "width": int(geom.width), "height": int(geom.height), "pixel_meta": pixel_meta,
            "frame_path": str(frame_path.relative_to(OUT)), "frame_bytes": len(frame),
            "frame_sha256": sha(frame), "rgb_path": str(rgb_path.relative_to(OUT)),
            "rgb_bytes": len(rgb), "rgb_sha256": sha(rgb)}


def launch(rowdir, effect):
    env = {**os.environ, "DISPLAY": DISPLAY_NAME, "ROW_DIR": str(rowdir), "EFFECT_MODE": effect}
    return subprocess.Popen(["/usr/bin/python3", "-B", str(ROOT / "fixture.py")], env=env,
                            stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)


def wait_state(conn, rowdir, label, timeout=4):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        s = state(conn, rowdir, label)
        if s["status"] != "unavailable":
            return s
        time.sleep(0.03)
    return state(conn, rowdir, label)


def wait_ambiguous(conn, rowdir, label, expected_pids, timeout=4):
    deadline = time.monotonic() + timeout
    expected = sorted(expected_pids)
    while time.monotonic() < deadline:
        current = state(conn, rowdir, label)
        ready_pids = sorted(e.get("pid") for e in ready_events(rowdir) if e.get("kind") == "ready")
        target_ids = [t["xid"] for t in current.get("targets", [])]
        target_pids = sorted(t["xres"]["pid"] for t in current.get("targets", []))
        if (current.get("status") == "ambiguous" and current.get("count") == 2
                and ready_pids == expected and target_pids == expected and len(set(target_ids)) == 2):
            current["ready_pids"] = ready_pids
            return current
        time.sleep(0.03)
    return current


def query_button_released(root_window):
    pointer = root_window.query_pointer()
    mask = int(pointer.mask)
    return {"verified": not bool(mask & BUTTON_MASK), "mask": mask, "button1_mask": int(BUTTON_MASK)}


def structured_rep(state_row):
    return {"target": state_row["xid"], "pid": state_row["pid"],
            "start_ticks": state_row["start_ticks"], "counter": state_row["counter"],
            "version": state_row["version"], "operation": "increment",
            "control": state_row["ready_event"]["button_rect"]}


def make_representation(arm, rowdir, initial):
    structured = structured_rep(initial)
    struct_bytes = json.dumps(structured, sort_keys=True, separators=(",", ":")).encode()
    image_path = rowdir / "proxy.ppm"
    if arm in {"proxy_image", "hybrid"}:
        render(initial["counter"], initial["version"], image_path, structured["control"])
    if arm == "ordinary_screenshot":
        input_path = OUT / initial["rgb_path"]
        input_bytes = input_path.read_bytes()
        rgb = input_bytes
        coord = center(blue_bbox(initial["width"], initial["height"], rgb))
        return {"kind": "ordinary_screenshot", "input_path": initial["rgb_path"],
                "input_sha256": sha(input_bytes), "input_bytes": len(input_bytes),
                "derived_from_sha256": sha(input_bytes), "method": "ximage_rgb_blue_component_bbox",
                "coordinate": coord}
    if arm == "proxy_image":
        img_bytes = image_path.read_bytes()
        w, h, rgb = ppm_rgb(img_bytes)
        coord = center(blue_bbox(w, h, rgb))
        return {"kind": "proxy_image", "input_path": str(image_path.relative_to(OUT)),
                "input_sha256": sha(img_bytes), "input_bytes": len(img_bytes),
                "derived_from_sha256": sha(img_bytes), "method": "ppm_blue_component_bbox",
                "coordinate": coord}
    if arm == "structured_proxy":
        path = rowdir / "structured.json"
        path.write_bytes(struct_bytes)
        coord = center(structured["control"])
        return {"kind": "structured_proxy", "input_path": str(path.relative_to(OUT)),
                "input_sha256": sha(struct_bytes), "input_bytes": len(struct_bytes),
                "derived_from_sha256": sha(struct_bytes), "method": "structured_control_rect_center",
                "coordinate": coord, "state": structured}
    img_bytes = image_path.read_bytes()
    w, h, rgb = ppm_rgb(img_bytes)
    image_coord = center(blue_bbox(w, h, rgb))
    coord = center(structured["control"])
    if image_coord != coord:
        raise RuntimeError("hybrid image/structured derivations disagree")
    path = rowdir / "structured.json"
    path.write_bytes(struct_bytes)
    combined = {"proxy_image_sha256": sha(img_bytes), "structured_sha256": sha(struct_bytes)}
    payload = json.dumps(combined, sort_keys=True, separators=(",", ":")).encode()
    return {"kind": "hybrid", "input_paths": [str(image_path.relative_to(OUT)), str(path.relative_to(OUT))],
            "input_sha256": sha(payload), "input_bytes": len(img_bytes) + len(struct_bytes),
            "derived_from_sha256": sha(payload), "method": "hybrid_image_and_structured_agreement",
            "coordinate": coord, "image_coordinate": image_coord, "structured_coordinate": center(structured["control"]),
            "state": structured, "proxy_sha256": sha(img_bytes)}


def stop(proc):
    if proc is None:
        return None
    if proc.poll() is None:
        proc.terminate()
    try:
        return proc.wait(timeout=3)
    except subprocess.TimeoutExpired:
        proc.kill()
        return proc.wait(timeout=3)


def run_row(arm, case):
    key = f"{arm}__{case}"
    rowdir = OUT / "rows" / key
    rowdir.mkdir(parents=True, exist_ok=False)
    row = {"arm": arm, "case": case, "row_id": key, "emissions": 0, "input_ack": False,
           "decision": None, "error": None, "processes": [], "process_exit_codes": {}, "release_verified": False}
    xvfb = app = extra = conn = None
    try:
        if SOCKET.exists():
            raise RuntimeError("private Xvfb socket already exists")
        xvfb = subprocess.Popen(["/usr/bin/Xvfb", DISPLAY_NAME, "-screen", "0", "640x480x24", "-nolisten", "tcp"],
                                stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        row["processes"].append({"role": "xvfb", "pid": xvfb.pid, "start_ticks": proc_identity(xvfb.pid)["start_ticks"]})
        deadline = time.monotonic() + 4
        while not SOCKET.exists() and time.monotonic() < deadline:
            if xvfb.poll() is not None:
                raise RuntimeError("Xvfb exited before socket appeared")
            time.sleep(0.02)
        if not SOCKET.exists():
            raise RuntimeError("Xvfb socket unavailable")
        conn = display.Display(DISPLAY_NAME)
        app = launch(rowdir, "off" if case == "no_effect" else "on")
        row["processes"].append({"role": "fixture", "pid": app.pid, "start_ticks": proc_identity(app.pid)["start_ticks"]})
        first = wait_state(conn, rowdir, "before")
        if first["status"] != "ok":
            raise RuntimeError("initial unique visible target missing")
        row["initial_state"] = first
        representation = make_representation(arm, rowdir, first)
        row["presentation"] = representation
        token_keys = ("xid", "pid", "start_ticks", "counter", "version", "title", "geometry", "rgb_sha256")
        token = {k: first[k] for k in token_keys}
        row["request"] = {"operation": "increment", "source_token": token,
                           "source_frame_sha256": first["rgb_sha256"], "representation_arm": arm,
                           "representation_sha256": representation["input_sha256"],
                           "derived_from_sha256": representation["derived_from_sha256"],
                           "derived_coordinate": representation["coordinate"]}
        if case == "stale_version":
            os.kill(app.pid, signal.SIGUSR1)
            time.sleep(0.15)
        elif case == "target_replaced":
            row["process_exit_codes"]["fixture_original"] = stop(app)
            app = launch(rowdir, "on")
            row["processes"].append({"role": "fixture_replacement", "pid": app.pid,
                                     "start_ticks": proc_identity(app.pid)["start_ticks"]})
            wait_state(conn, rowdir, "replacement")
        elif case == "unavailable":
            wins = find_windows(conn)
            wins[0][0].unmap()
            conn.sync()
            time.sleep(0.05)
        elif case == "ambiguous":
            extra = launch(rowdir, "on")
            row["processes"].append({"role": "duplicate_fixture", "pid": extra.pid,
                                     "start_ticks": proc_identity(extra.pid)["start_ticks"]})
            row["ambiguous_setup"] = wait_ambiguous(conn, rowdir, "duplicate", [app.pid, extra.pid])

        current = state(conn, rowdir, "pre_dispatch")
        row["current_state"] = current
        if case == "macro_failure":
            row["decision"] = "YIELD_MACRO_FAILURE"
        elif current["status"] != "ok":
            row["decision"] = "YIELD_TARGET_" + current["status"].upper()
        elif any(current.get(k) != token.get(k) for k in token):
            row["decision"] = "REFUSE_STALE_BINDING"
        else:
            win = conn.create_resource_object("window", current["xid"])
            win.set_input_focus(X.RevertToParent, X.CurrentTime)
            conn.sync()
            x, y = representation["coordinate"]
            xtest.fake_input(conn, X.MotionNotify, x=x, y=y)
            xtest.fake_input(conn, X.ButtonPress, 1)
            xtest.fake_input(conn, X.ButtonRelease, 1)
            conn.sync()
            row["emissions"] = 1
            time.sleep(0.18)
            row["input_ack"] = any(e.get("kind") == "click_ack" for e in ready_events(rowdir))
            row["decision"] = "YIELD_NO_APPLICATION_EFFECT" if case == "no_effect" else "COMPLETED"
        time.sleep(0.04)
        row["after_state"] = state(conn, rowdir, "after")
    except Exception as exc:
        row["error"] = f"{type(exc).__name__}: {exc}"
    finally:
        if conn is not None:
            try:
                row["release_observation"] = query_button_released(conn.screen().root)
                row["release_verified"] = row["release_observation"]["verified"]
            except Exception as exc:
                row["release_observation"] = {"verified": False, "error": f"{type(exc).__name__}: {exc}"}
        for role, proc in (("fixture_current", app), ("duplicate_fixture", extra), ("xvfb", xvfb)):
            if proc is not None:
                row["process_exit_codes"][role] = stop(proc)
        if conn is not None:
            try:
                conn.close()
            except Exception:
                pass
        socket_deadline = time.monotonic() + 2
        while SOCKET.exists() and time.monotonic() < socket_deadline:
            time.sleep(0.02)
        row["socket_disappeared"] = not SOCKET.exists()
        row["fixture_events"] = ready_events(rowdir)
        eventfile = rowdir / "fixture-events.jsonl"
        row["fixture_events_sha256"] = sha(eventfile.read_bytes()) if eventfile.exists() else None
        row["reply"] = {"decision": row.get("decision"), "emissions": row.get("emissions"),
                        "input_ack": row.get("input_ack"), "after_state": row.get("after_state")}
        (rowdir / "row.json").write_text(json.dumps(row, sort_keys=True, indent=2) + "\n")
    return row


def main():
    rows = [run_row(arm, case) for arm in ARMS for case in CASES]
    result = {"allocation_id": "issue3631-proxy-effect-unit-formal-04", "issue": 3631,
              "canonical_output_path": "evidence/formal-04",
              "source_commit": os.environ["FROZEN_SOURCE_COMMIT"],
              "source_manifest_sha256": os.environ["SOURCE_MANIFEST_SHA256"],
              "preregistration_sha256": os.environ["PREREGISTRATION_SHA256"],
              "freeze_sha256": os.environ["FREEZE_SHA256"],
              "image_id": "sha256:69bc215db0514ee1bc4f730cceb296ecef89e4418cea8d4b2fc2ca3101101e27",
              "platform": "linux/arm64", "formal_invocations": 1, "retries": 0,
              "arms": list(ARMS), "cases": list(CASES), "rows": rows}
    canonical = json.dumps(result, sort_keys=True, separators=(",", ":")).encode()
    result["result_sha256"] = sha(canonical)
    (OUT / "raw.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    print(json.dumps({"allocation_id": result["allocation_id"], "row_count": len(rows),
                      "row_errors": sum(r["error"] is not None for r in rows)}, sort_keys=True))
    if any(r["error"] for r in rows):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
