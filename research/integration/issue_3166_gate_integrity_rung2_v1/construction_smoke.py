"""Non-formal one-action GTK/X11 construction smoke; never reads formal output."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, "/repo")
from runtime.cli_v1.golden_v3 import dispatch_golden_v3

display = ":152"
env = os.environ.copy()
env["DISPLAY"] = display
root = Path(tempfile.mkdtemp(prefix="issue3166-rung2-smoke-"))
xvfb = subprocess.Popen(["Xvfb", display, "-screen", "0", "800x400x24", "-nolisten", "tcp", "-ac"],
                        env=env, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
fixture = None
try:
    time.sleep(0.25)
    meta, effect, events = root / "meta.json", root / "effect.json", root / "events.jsonl"
    app = Path("/repo/research/integration/golden_v3_second_domain_2246_v1/gtk_fixture_app.py")
    fixture = subprocess.Popen(["/usr/bin/python3", "-B", str(app), "--mode", "useful",
                                "--meta", str(meta), "--effect", str(effect), "--events", str(events)],
                               env=env, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
    deadline = time.monotonic() + 8
    while not meta.exists() and time.monotonic() < deadline:
        if fixture.poll() is not None:
            raise RuntimeError(f"fixture exited: {fixture.stderr.read()[-1000:]}")
        time.sleep(0.02)
    info = json.loads(meta.read_text(encoding="utf-8"))
    result = dispatch_golden_v3({
        "schema": "agent-interface/program-v1", "program_id": "construction-smoke",
        "source": {"observation_seq": 1, "binding_revision": 1},
        "authority": {"lease_id": "construction-smoke",
                      "expires_at_ns": time.monotonic_ns() + 5_000_000_000},
        "terminal": {"release_all_required": True},
        "ops": [{"op": "focus", "target": "fixture"},
                {"op": "key_chord", "keys": ["CTRL", "s"]},
                {"op": "release_all"}],
    }, {"fixture": int(info["window_id"])}, current_observation_seq=1,
       current_binding_revision=1, display_name=display)
    time.sleep(0.1)
    actual = json.loads(effect.read_text(encoding="utf-8"))
    if result.get("native_status") != "completed" or actual != {"saved": True, "text": ""}:
        raise RuntimeError("construction action/effect mismatch")
    print(json.dumps({"result": "CONSTRUCTION_GTK_X11_EFFECT_AND_RELEASE_PASS",
                      "native_status": result.get("native_status"), "effect": actual,
                      "emissions": result.get("raw_dispatch", {}).get("result", {})
                      .get("execution", {}).get("program_emissions")} , sort_keys=True))
finally:
    if fixture is not None and fixture.poll() is None:
        try:
            subprocess.run(["xdotool", "windowclose", str(json.loads(meta.read_text())["window_id"])],
                           env=env, timeout=2, check=False, stdout=subprocess.DEVNULL,
                           stderr=subprocess.DEVNULL)
            fixture.wait(timeout=3)
        except Exception:
            fixture.terminate()
            try:
                fixture.wait(timeout=2)
            except subprocess.TimeoutExpired:
                fixture.kill()
                fixture.wait(timeout=2)
    xvfb.terminate()
    xvfb.wait(timeout=3)
