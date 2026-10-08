"""Capture the exact guest facts used for the A05 setup and candidate."""
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import sys


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


packages = subprocess.check_output(
    ["dpkg-query", "-W", "-f=${Package}=${Version}\\n",
     "python3", "python3-xlib", "xvfb", "xserver-common"], text=True
).splitlines()
report = {
    "schema": "v39-x11-event-routing-environment-a05-v1",
    "machine": "v39-x11-routing-a05-20261004",
    "orb_machine_id": "01M42N2F303RHWR42A763DRBNJ",
    "orb_machine_image": {"distro": "ubuntu", "version": "noble", "arch": "arm64"},
    "orb_isolated": True,
    "orb_isolate_network": True,
    "system": platform.platform(),
    "uname": platform.uname()._asdict(),
    "python": sys.version,
    "packages": packages,
    "xvfb_sha256": sha("/usr/bin/Xvfb"),
    "python_xlib_event_source_sha256": sha(
        "/usr/lib/python3/dist-packages/Xlib/protocol/event.py"),
    "candidate_external_network_calls": "none by source inspection",
    "xvfb_tcp": False,
    "effective_cpu_or_memory_cap": "not verified",
}
print(json.dumps(report, indent=2, sort_keys=True))
