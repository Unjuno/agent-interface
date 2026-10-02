import pathlib
import subprocess
import sys
import time

marker = pathlib.Path("/tmp/child.started")
child = pathlib.Path("/tmp/fake.py")
source = (
    "#!" + sys.executable + "\n"
    "import pathlib,sys,time\n"
    "pathlib.Path(sys.argv[1]).write_text('started')\n"
    "time.sleep(3)\n"
)
child.write_text(source, encoding="utf-8")
child.chmod(0o755)
proc = subprocess.Popen([str(child), str(marker)])
deadline = time.monotonic() + 2
while not marker.exists() and time.monotonic() < deadline:
    time.sleep(0.005)
assert marker.exists(), "parent did not observe child-start marker"
assert marker.read_text(encoding="utf-8") == "started"
proc.kill()
proc.wait(timeout=2)
print("CONSTRUCTION_MARKER_PASS", proc.returncode)
