"""Capture actual A02 guest and dependency identity."""
import importlib.metadata
import json
import platform
import subprocess
import sys

result = subprocess.run(["dpkg-query", "-W", "-f=${Package}=${Version}\\n",
                        "xvfb", "python3-xlib"], text=True,
                       capture_output=True, check=False)
print(json.dumps({
    "schema": "v39-x11-event-routing-environment-a03-v1",
    "platform": platform.platform(),
    "uname": platform.uname()._asdict(),
    "python": sys.version,
    "python_executable": sys.executable,
    "python_xlib_version": importlib.metadata.version("python-xlib"),
    "packages_exit": result.returncode,
    "packages_stdout": result.stdout,
    "packages_stderr": result.stderr,
}, indent=2, sort_keys=True))
