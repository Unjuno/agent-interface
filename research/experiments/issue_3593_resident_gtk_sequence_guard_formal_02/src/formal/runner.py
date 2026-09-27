from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import time

from Xlib import X, display
from Xlib.ext import xtest

from policies_original import Resident as UpstreamResident
from policies_guarded import Resident as GuardedResident
from traces import TRACES


DISPLAY_NAME = ":201"
SOCKET = Path("/tmp/.X11-unix/X201")
OUT = Path("/evidence")
POLICIES = {"UPSTREAM_RESIDENT": UpstreamResident, "SEQUENCE_GUARDED": GuardedResident}


def start_ticks(pid: int) -> str | None:
    try:
        text = Path(f"/proc/{pid}/stat").read_text(encoding="ascii")
        end = text.rfind(")")
        return text[end + 2 :].split()[19]
    except (FileNotFoundError, IndexError):
        return None


def wait_title(window, title: str, timeout: float = 1.5) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if window.get_wm_name() == title:
            return True
        time.sleep(0.01)
    return window.get_wm_name() == title


def find_fixture(root):
    deadline = time.monotonic() + 6
    while time.monotonic() < deadline:
        for window in root.query_tree().children:
            try:
                if (window.get_wm_name() or "").startswith("resident-fixture:"):
                    if window.get_attributes().map_state == X.IsViewable:
                        return window
            except Exception:
                continue
        time.sleep(0.02)
    raise RuntimeError("viewable GTK fixture window not found")


def frame_bytes(window, conn):
    geometry = window.get_geometry()
    conn.sync()
    pixels = window.get_image(0, 0, geometry.width, geometry.height, X.ZPixmap, 0xFFFFFFFF).data
    return int(geometry.width), int(geometry.height), pixels


def key_is_up(conn, code: int) -> bool:
    keymap = conn.query_keymap()
    return not bool(keymap[code // 8] & (1 << (code % 8)))


def run_row(policy_name: str, case: str, events: list[dict], effect_mode: str) -> dict:
    row = {"policy": policy_name, "case": case, "effect_mode": effect_mode,
           "events": events, "prefixes": [], "emitted_event_indices": [],
           "key_release_reads": [], "prefix_effect_counts": [], "error": None}
    xvfb = app = conn = window = None
    try:
        if SOCKET.exists():
            raise RuntimeError("fixed private Xvfb socket already exists")
        env = {**os.environ, "DISPLAY": DISPLAY_NAME, "EFFECT_MODE": effect_mode}
        xvfb = subprocess.Popen(["/usr/bin/Xvfb", DISPLAY_NAME, "-screen", "0", "640x480x24", "-nolisten", "tcp"],
                                stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        row.update(xvfb_pid=xvfb.pid, xvfb_start_ticks=start_ticks(xvfb.pid))
        deadline = time.monotonic() + 6
        while not SOCKET.exists() and time.monotonic() < deadline:
            if xvfb.poll() is not None:
                raise RuntimeError("Xvfb exited before socket appeared")
            time.sleep(0.02)
        if not SOCKET.exists():
            raise RuntimeError("Xvfb socket did not appear")

        conn = display.Display(DISPLAY_NAME)
        root = conn.screen().root
        app = subprocess.Popen(["python3", "-B", "/src/formal/fixture.py"], env=env,
                               stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        row.update(fixture_pid=app.pid, fixture_start_ticks=start_ticks(app.pid))
        window = find_fixture(root)
        window.set_input_focus(X.RevertToParent, X.CurrentTime)
        conn.sync()
        time.sleep(0.08)
        focus = conn.get_input_focus().focus
        if focus not in (window, window.id):
            raise RuntimeError(f"fixture focus mismatch: {focus}")
        row["focus_verified"] = True
        width, height, before = frame_bytes(window, conn)
        code = conn.keysym_to_keycode(0x20)
        policy = POLICIES[policy_name]()
        prior_action_count = 0
        pressed = 0
        for index, event in enumerate(events):
            policy.step(dict(event))
            delta = policy.actions[prior_action_count:]
            prior_action_count = len(policy.actions)
            emitted = [action for action in delta if action[0] == "emit"]
            for _action in emitted:
                xtest.fake_input(conn, X.KeyPress, code)
                conn.sync()
                xtest.fake_input(conn, X.KeyRelease, code)
                conn.sync()
                pressed += 1
                row["emitted_event_indices"].append(index)
                released = key_is_up(conn, code)
                row["key_release_reads"].append(released)
                if not released:
                    raise RuntimeError("Space key remained down after release")
            expected_visible = pressed if effect_mode == "on" else 0
            if not wait_title(window, f"resident-fixture:{expected_visible}"):
                raise RuntimeError("GTK effect/title failed to settle before next event")
            if not emitted:
                expected_visible = pressed if effect_mode == "on" else 0
                if not wait_title(window, f"resident-fixture:{expected_visible}"):
                    raise RuntimeError("GTK no-effect prefix failed to remain stable")
            row["prefix_effect_counts"].append(expected_visible)
            row["prefixes"].append({"index": index, "event": event,
                                    "action_delta": [list(x) for x in delta],
                                    "actions_so_far": [list(x) for x in policy.actions],
                                    "visible_title": window.get_wm_name(),
                                    "visible_effect_count": int((window.get_wm_name() or "resident-fixture:0").split(":")[-1]),
                                    "space_key_up": key_is_up(conn, code)})

        expected_final = pressed if effect_mode == "on" else 0
        if not wait_title(window, f"resident-fixture:{expected_final}"):
            raise RuntimeError("final GTK title/effect count mismatch")
        after_w, after_h, after = frame_bytes(window, conn)
        stem = f"{policy_name}__{case}__{effect_mode}"
        before_name, after_name = stem + "__before.raw", stem + "__after.raw"
        (OUT / "frames" / before_name).write_bytes(before)
        (OUT / "frames" / after_name).write_bytes(after)
        row.update(width=width, height=height, after_width=after_w, after_height=after_h,
                   bytes_per_frame=len(before), before_path="frames/" + before_name,
                   after_path="frames/" + after_name,
                   before_sha256=hashlib.sha256(before).hexdigest(),
                   after_sha256=hashlib.sha256(after).hexdigest(),
                   window_pixels_changed=before != after,
                   action_count=pressed, transport_count=pressed,
                   task_effect_count=expected_final, gui_title=window.get_wm_name(),
                   key_release_verified=len(row["key_release_reads"]) == pressed and all(row["key_release_reads"]))
    except Exception as exc:
        row["error"] = f"{type(exc).__name__}: {exc}"
    finally:
        if conn is not None:
            try:
                conn.close()
            except Exception:
                pass
        if app is not None:
            app.terminate()
            try:
                app.wait(timeout=4)
            except subprocess.TimeoutExpired:
                app.kill()
                app.wait(timeout=2)
            row.update(fixture_exit_code=app.returncode, fixture_reaped=app.poll() is not None)
        if xvfb is not None:
            xvfb.terminate()
            try:
                xvfb.wait(timeout=4)
            except subprocess.TimeoutExpired:
                xvfb.kill()
                xvfb.wait(timeout=2)
            deadline = time.monotonic() + 4
            while SOCKET.exists() and time.monotonic() < deadline:
                time.sleep(0.02)
            row.update(xvfb_exit_code=xvfb.returncode, xvfb_reaped=xvfb.poll() is not None,
                       socket_disappeared=not SOCKET.exists())
    return row


def main():
    if any(OUT.iterdir()):
        raise RuntimeError("fresh formal evidence directory must be empty")
    (OUT / "frames").mkdir()
    rows = []
    for case, events in TRACES.items():
        for policy in POLICIES:
            for effect in ("on", "off"):
                rows.append(run_row(policy, case, events, effect))
    raw = {
        "allocation_id": "issue3588-resident-gtk-sequence-guard-formal-02",
        "issue": 3593,
        "source_commit": os.environ["OBSTAC_SOURCE_COMMIT"],
        "image_id": os.environ["OBSTAC_IMAGE_ID"],
        "freeze_sha256": hashlib.sha256(Path("/freeze.json").read_bytes()).hexdigest(),
        "source_manifest_sha256": hashlib.sha256(Path("/source_manifest.json").read_bytes()).hexdigest(),
        "formal_invocations": 1,
        "reruns": 0,
        "trace_names": list(TRACES),
        "rows": rows,
    }
    canonical = json.dumps(raw, sort_keys=True, separators=(",", ":")).encode()
    raw["result_sha256"] = hashlib.sha256(canonical).hexdigest()
    (OUT / "raw.json").write_text(json.dumps(raw, sort_keys=True, indent=2) + "\n")
    print(json.dumps({"allocation_id": raw["allocation_id"], "rows": len(rows),
                      "errors": sum(r["error"] is not None for r in rows),
                      "all_key_releases": all(r.get("key_release_verified") for r in rows),
                      "all_cleanup": all(r.get("fixture_reaped") and r.get("xvfb_reaped") and r.get("socket_disappeared") for r in rows),
                      "result_sha256": raw["result_sha256"]}, sort_keys=True))


if __name__ == "__main__":
    main()
