"""Construction-only V16 session argv adapter for the prepared v39 relay.

This module does not launch a process. Call install() only in a separately
authorized, refreshed source closure after its paths have been custody-checked.
"""
from pathlib import Path
import sys


def build_session_command(args, runtime, session_path, python=sys.executable):
    session = Path(session_path).resolve(strict=True)
    if session.name != "session_map01_v16.py":
        raise ValueError("session path must select session_map01_v16.py")
    fixture = Path(args.load_fixture_manifest).resolve(strict=True)
    return [
        str(python), str(session), "--out", str(Path(runtime).resolve()),
        "--seed", str(args.seed), "--timeout-seconds", "600", "--skill", "1",
        "--load-fixture-manifest", str(fixture),
    ]


def install(controller, session_path):
    """Override only session selection; preserve v39 orchestration and relay."""
    controller.session_command = lambda args, runtime: build_session_command(
        args, runtime, session_path
    )
    return controller
