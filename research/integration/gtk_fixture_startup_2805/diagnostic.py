"""No-input GTK fixture startup diagnostic for #2805."""
from __future__ import annotations
import json, os, subprocess, sys, time
from pathlib import Path

def run(out: Path, timeout: float = 8.0) -> dict[str, object]:
    out.mkdir(parents=True, exist_ok=True)
    display = ":99"
    xvfb = subprocess.Popen(
        ["Xvfb", display, "-screen", "0", "640x360x24", "-nolisten", "tcp", "-ac"],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
    )
    fixture = None
    started = time.monotonic()
    meta = out / "meta.json"
    try:
        socket = Path("/tmp/.X11-unix/X99")
        while not socket.exists() and xvfb.poll() is None and time.monotonic() - started < timeout:
            time.sleep(0.02)
        socket_ready = socket.exists()
        env = dict(os.environ, DISPLAY=display)
        fixture = subprocess.Popen(
            [
                sys.executable,
                "research/integration/golden_v3_second_domain_2246_v1/gtk_fixture_app.py",
                "--mode", "useful",
                "--meta", str(meta),
                "--effect", str(out / "effect.json"),
                "--events", str(out / "events.jsonl"),
            ],
            env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        )
        deadline = time.monotonic() + timeout
        while not meta.exists() and fixture.poll() is None and time.monotonic() < deadline:
            time.sleep(0.02)
        alive_at_meta = meta.exists() and fixture.poll() is None
        if fixture.poll() is None:
            fixture.terminate()
        fixture_stdout, fixture_stderr = fixture.communicate(timeout=5)
        xvfb.terminate()
        xvfb_stdout, xvfb_stderr = xvfb.communicate(timeout=5)
        result = {
            "decision": "PASS_GTK_FIXTURE_STARTUP_DIAGNOSTIC" if socket_ready and alive_at_meta else "STOP_GTK_FIXTURE_STARTUP",
            "display": display,
            "x_socket_ready": socket_ready,
            "meta_present": meta.exists(),
            "fixture_alive_at_meta": alive_at_meta,
            "fixture_exit_code": fixture.returncode,
            "xvfb_exit_code": xvfb.returncode,
            "elapsed_ms": round((time.monotonic() - started) * 1000, 3),
            "fixture_stdout": fixture_stdout,
            "fixture_stderr": fixture_stderr,
            "xvfb_stdout": xvfb_stdout,
            "xvfb_stderr": xvfb_stderr,
        }
        (out / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return result
    finally:
        if fixture is not None and fixture.poll() is None:
            fixture.kill()
        if xvfb.poll() is None:
            xvfb.kill()

if __name__ == "__main__":
    result = run(Path(sys.argv[1]))
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if result["decision"] == "PASS_GTK_FIXTURE_STARTUP_DIAGNOSTIC" else 1)
