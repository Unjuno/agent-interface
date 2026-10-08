"""Additive socket wrapper with a short private AF_UNIX path for OrbStack."""
from pathlib import Path
import sys

import event_socket_v11 as bridge

ENTRY = Path(__file__).with_name("interactive_integrated_efficiency_task1_v2.py")
domain = sys.argv.pop(1)
if domain != "integrated-efficiency-chromium-v1":
    raise SystemExit("domain must be integrated-efficiency-chromium-v1")

# Shared host bind mounts make long absolute paths available to the model
# backend, but Linux AF_UNIX has a short pathname limit. Keep only the private
# control socket in the container's short /tmp; runtime artifacts stay shared.
_temporary_directory = bridge.tempfile.TemporaryDirectory


def _short_socket_directory(*args, **kwargs):
    kwargs["dir"] = "/tmp"
    return _temporary_directory(*args, **kwargs)


bridge.tempfile.TemporaryDirectory = _short_socket_directory
_original_popen = bridge.subprocess.Popen


def _spawn(args, **kwargs):
    args = list(args)
    index = next(i for i, value in enumerate(args)
                 if str(value).endswith("interactive_v27.py"))
    args[index] = str(ENTRY)
    return _original_popen(args, **kwargs)


bridge.subprocess.Popen = _spawn
bridge.main()
