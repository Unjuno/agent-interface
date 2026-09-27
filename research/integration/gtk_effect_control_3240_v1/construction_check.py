"""No-input GTK/Xvfb readiness probe for the #3240 image."""
import json
import os
from pathlib import Path
import re
import select
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[3]
FIXTURE = ROOT / "research/integration/golden_v3_second_domain_2246_v1/gtk_fixture_app.py"


def main():
    out = Path(tempfile.mkdtemp(prefix="gtk3240-construction-"))
    xvfb = subprocess.Popen(
        ["Xvfb", "-displayfd", "1", "-screen", "0", "640x360x24",
         "-nolisten", "tcp", "-ac"], stdout=subprocess.PIPE,
        stderr=(out / "xvfb.stderr").open("wb"), text=True)
    fixture = None
    decoy = None
    result = {"scope": "GTK startup/readiness only; no GUI input",
              "input_sent": False, "model_calls": 0, "provider_calls": 0}
    try:
        if not select.select([xvfb.stdout], [], [], 10)[0]:
            raise TimeoutError("Xvfb readiness timeout")
        display_number = xvfb.stdout.readline().strip()
        if not display_number.isdigit():
            raise RuntimeError("Xvfb did not return display identity")
        env = dict(os.environ, DISPLAY=":" + display_number)
        meta = out / "meta.json"
        fixture = subprocess.Popen(
            [sys.executable, str(FIXTURE), "--mode", "useful", "--meta", str(meta),
             "--effect", str(out / "effect.json")],
            env=env, stdout=(out / "fixture.stdout").open("wb"),
            stderr=(out / "fixture.stderr").open("wb"))
        deadline = time.monotonic() + 10
        while not meta.exists():
            if fixture.poll() is not None or time.monotonic() >= deadline:
                raise TimeoutError("GTK fixture metadata readiness timeout")
            time.sleep(0.02)
        decoy_meta = out / "decoy-meta.json"
        decoy = subprocess.Popen(
            [sys.executable, str(ROOT / "research/integration/gtk_effect_control_3240_v1/fixture_render_decoy.py"),
             "--meta", str(decoy_meta), "--text", "gtk3240"],
            env=env, stdout=(out / "decoy.stdout").open("wb"),
            stderr=(out / "decoy.stderr").open("wb"))
        deadline = time.monotonic() + 10
        while not decoy_meta.exists():
            if decoy.poll() is not None or time.monotonic() >= deadline:
                raise TimeoutError("render-only decoy readiness timeout")
            time.sleep(0.02)
        target_xid = json.loads(meta.read_text(encoding="utf-8"))["window_id"]
        decoy_xid = json.loads(decoy_meta.read_text(encoding="utf-8"))["window_id"]
        target_prop = subprocess.run(
            ["xprop", "-id", str(target_xid), "_NET_WM_PID", "WM_NAME", "WM_CLASS"],
            env=env, check=True, text=True, capture_output=True, timeout=5).stdout
        decoy_prop = subprocess.run(
            ["xprop", "-id", str(decoy_xid), "_NET_WM_PID", "WM_NAME", "WM_CLASS"],
            env=env, check=True, text=True, capture_output=True, timeout=5).stdout
        target_geom = subprocess.run(
            ["xwininfo", "-id", str(target_xid)], env=env, check=True,
            text=True, capture_output=True, timeout=5).stdout
        decoy_geom = subprocess.run(
            ["xwininfo", "-id", str(decoy_xid)], env=env, check=True,
            text=True, capture_output=True, timeout=5).stdout
        def geometry(text):
            fields = {}
            for name in ("Width", "Height", "Absolute upper-left X", "Absolute upper-left Y"):
                match = re.search(r"^\s*" + re.escape(name) + r":\s*(-?\d+)", text, re.MULTILINE)
                fields[name] = int(match.group(1)) if match else None
            return fields
        subprocess.run(["xwd", "-silent", "-id", str(target_xid), "-out", str(out / "target.xwd")],
                       env=env, check=True, capture_output=True, timeout=5)
        subprocess.run(["xwd", "-silent", "-id", str(decoy_xid), "-out", str(out / "decoy.xwd")],
                       env=env, check=True, capture_output=True, timeout=5)
        result.update({"decision": "PASS_GTK_READINESS_ONLY",
                       "display": env["DISPLAY"],
                       "fixture_pid": fixture.pid,
                       "meta": json.loads(meta.read_text(encoding="utf-8")),
                       "decoy_pid": decoy.pid,
                       "decoy_meta": json.loads(decoy_meta.read_text(encoding="utf-8")),
                       "window_props": [target_prop, decoy_prop],
                       "target_geometry": geometry(target_geom),
                       "decoy_geometry": geometry(decoy_geom),
                       "geometry_matches": geometry(target_geom) == geometry(decoy_geom),
                       "xwd_bytes": [(out / "target.xwd").stat().st_size,
                                     (out / "decoy.xwd").stat().st_size],
                       "effect_file_absent": not (out / "effect.json").exists()})
        print(json.dumps(result, sort_keys=True), flush=True)
    except Exception as exc:
        result.update({"decision": "STOP_GTK_READINESS", "error": repr(exc)})
        print(json.dumps(result, sort_keys=True), flush=True)
        raise
    finally:
        if decoy is not None and decoy.poll() is None:
            decoy.terminate()
            decoy.wait(timeout=5)
        if fixture is not None and fixture.poll() is None:
            fixture.terminate()
            fixture.wait(timeout=5)
        if xvfb.poll() is None:
            xvfb.terminate()
            xvfb.wait(timeout=5)


if __name__ == "__main__":
    main()
