"""Setup-only Xvfb and focused-client check; sends no input events."""
import json
import os
from pathlib import Path
import select
import subprocess
import tempfile

from Xlib import X, display


def main():
    with tempfile.TemporaryDirectory(prefix="v39-x11-a02-setup-") as directory:
        auth = Path(directory) / "empty.Xauthority"
        auth.write_bytes(b"")
        env = dict(os.environ, XAUTHORITY=str(auth))
        server = subprocess.Popen(
            ["Xvfb", "-displayfd", "1", "-screen", "0", "640x480x24",
             "-nolisten", "tcp", "-ac"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env)
        observer = app = None
        report = {"schema": "v39-x11-event-routing-setup-a03-v1", "input_events_sent": 0}
        try:
            ready, _, _ = select.select([server.stdout], [], [], 5)
            if not ready:
                raise RuntimeError("Xvfb startup timeout")
            number = server.stdout.readline().strip()
            if not number.isdecimal():
                raise RuntimeError("Xvfb displayfd malformed")
            observer = display.Display(":" + number)
            app = display.Display(":" + number)
            screen = app.screen()
            window = screen.root.create_window(
                10, 10, 120, 80, 0, screen.root_depth, X.InputOutput,
                X.CopyFromParent, event_mask=X.KeyPressMask | X.KeyReleaseMask)
            window.map()
            window.set_input_focus(X.RevertToParent, X.CurrentTime)
            app.sync()
            observer.sync()
            focus = observer.get_input_focus().focus
            focus_id = focus.id if hasattr(focus, "id") else focus
            bitmap = bytes(observer.query_keymap())
            report.update({"display_number": number, "window_id": window.id,
                           "focus_id": focus_id, "focus_matches_window": focus_id == window.id,
                           "keymap_length": len(bitmap), "all_keys_up": not any(bitmap)})
        finally:
            if app is not None:
                app.close()
            if observer is not None:
                observer.close()
            running = server.poll() is None
            if running:
                server.terminate()
            try:
                _, stderr = server.communicate(timeout=3)
            except subprocess.TimeoutExpired:
                server.kill()
                _, stderr = server.communicate(timeout=3)
                raise RuntimeError("Xvfb needed forced kill during setup")
            report.update({"xvfb_running_before_stop": running,
                           "xvfb_returncode_after_stop": server.returncode,
                           "xvfb_stderr": stderr})
    print(json.dumps(report, indent=2, sort_keys=True))
    if not (report["focus_matches_window"] and report["keymap_length"] == 32
            and report["all_keys_up"] and report["input_events_sent"] == 0):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
