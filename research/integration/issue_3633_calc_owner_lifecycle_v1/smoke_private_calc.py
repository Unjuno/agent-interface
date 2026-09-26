"""Pre-allocation readiness smoke; does not signal or test process groups."""
import os
import struct
import subprocess
import tempfile
import time
from pathlib import Path

display = ":143"
root = Path(tempfile.mkdtemp(prefix="issue3644-smoke-"))
for name in ("home", "config", "cache", "runtime", "lo"):
    (root / name).mkdir(mode=0o700)
auth = root / "Xauthority"
number, key, data = b"143", b"MIT-MAGIC-COOKIE-1", bytes.fromhex("a14f22b98d054bd38740a7990c56c260")
auth.write_bytes(struct.pack("!HH", 256, 0) + struct.pack("!H", len(number)) + number
                 + struct.pack("!H", len(key)) + key + struct.pack("!H", len(data)) + data)
os.chmod(auth, 0o600)
env = os.environ.copy()
env.update(DISPLAY=display, XAUTHORITY=str(auth), HOME=str(root / "home"),
           XDG_CONFIG_HOME=str(root / "config"), XDG_CACHE_HOME=str(root / "cache"),
           XDG_RUNTIME_DIR=str(root / "runtime"), SAL_USE_VCLPLUGIN="gen", GDK_BACKEND="x11")
xvfb = subprocess.Popen(["Xvfb", display, "-screen", "0", "1600x1000x24", "-ac"],
                        env=env, stdout=(root / "xvfb.log").open("wb"), stderr=subprocess.STDOUT,
                        start_new_session=True)
lo = None
try:
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline and not Path("/tmp/.X11-unix/X143").exists():
        time.sleep(.05)
    if not Path("/tmp/.X11-unix/X143").exists():
        raise SystemExit("STOP: Xvfb socket missing")
    lo = subprocess.Popen(["libreoffice", "--norestore", "--nofirststartwizard",
                           f"-env:UserInstallation=file://{root / 'lo'}", "--calc"],
                          env=env, stdout=(root / "libreoffice.log").open("wb"), stderr=subprocess.STDOUT,
                          start_new_session=True)
    deadline = time.monotonic() + 20
    found = []
    while time.monotonic() < deadline:
        search = subprocess.run(["xdotool", "search", "--onlyvisible", "--name", ".*"],
                                env=env, text=True, capture_output=True)
        for xid in search.stdout.splitlines():
            title = subprocess.run(["xdotool", "getwindowname", xid], env=env,
                                   text=True, capture_output=True).stdout.strip()
            if "libreoffice calc" in title.casefold():
                pid = subprocess.run(["xdotool", "getwindowpid", xid], env=env,
                                     text=True, capture_output=True).stdout.strip()
                found.append((int(xid), title, int(pid) if pid.isdigit() else None))
        if found:
            break
        if lo.poll() is not None:
            break
        time.sleep(.2)
    if len(found) != 1 or not found[0][2]:
        print((root / "xvfb.log").read_text(errors="replace"))
        print((root / "libreoffice.log").read_text(errors="replace"))
        raise SystemExit(f"STOP: expected unique Calc window owner, observed {found!r}; root={root}")
    print({"decision": "READY_FOR_FORMAL_ALLOCATION", "xid_title_pid": found[0],
           "launcher_pid": lo.pid, "launcher_pgid": os.getpgid(lo.pid),
           "owner_pgid": os.getpgid(found[0][2]), "display": display})
finally:
    if lo is not None:
        try:
            os.killpg(lo.pid, 15)
            lo.wait(timeout=4)
        except (ProcessLookupError, subprocess.TimeoutExpired):
            pass
    if xvfb.poll() is None:
        xvfb.terminate()
    try:
        xvfb.wait(timeout=3)
    except subprocess.TimeoutExpired:
        pass
