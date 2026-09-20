"""Task-1 fixture adapter with a short Chromium profile path for X11 Linux."""
from __future__ import annotations

import os
from pathlib import Path
import shutil

from integrated_efficiency_fixture_v1 import Fixture

_ACTIVE: dict[str, Fixture] = {}


def prepare(session, app: str, seed: int, chromium: str):
    if app != "chromium":
        raise ValueError("integrated efficiency runtime supports chromium only")
    fixture = Fixture(Path(session.tmp) / "integrated-fixture", seed)
    goals = fixture.goals()
    profile = f"/tmp/a2849-chromium-{session.display_num}"
    args = [
        chromium, "--no-sandbox", "--disable-gpu", "--disable-dev-shm-usage",
        "--no-first-run", "--no-default-browser-check",
        "--disable-background-networking", "--disable-component-update",
        "--disable-sync", "--password-store=basic",
        f"--user-data-dir={profile}", "about:blank",
    ]
    # Chromium creates additional Unix sockets below TMPDIR; keep those short
    # while Python/session artifacts continue using the shared evidence mount.
    session.env["TMPDIR"] = "/tmp"
    with (Path(session.tmp) / "application.log").open("w") as log:
        session.spawn(args, stdout=log, stderr=log)
    try:
        session.wait_window("about:blank", 20.0)
    except Exception:
        log_path = Path(session.tmp) / "application.log"
        if log_path.exists():
            shutil.copy2(log_path, Path(os.environ["ISSUE_2849_STARTUP_DIR"])
                         / "chromium-startup.log")
        raise
    session.focus("about:blank")
    goal = {
        "schema": "integrated_efficiency_goal_v1", "seed": seed, "tasks": goals,
        "url": goals[0]["url"], "token": goals[0]["token"],
        "setup_readiness_captures": 0,
    }
    _ACTIVE[str(fixture.history)] = fixture
    return goal, fixture.history, fixture.server


def evaluate(app: str, output: Path, goal: dict):
    if app != "chromium":
        raise ValueError("integrated efficiency runtime supports chromium only")
    fixture = _ACTIVE.get(str(output))
    if fixture is None:
        return {"schema": "integrated_efficiency_oracle_v1", "success": False,
                "reason": "fixture_registry_missing"}
    expected = [(row["task_id"], row["token"], row["layout"])
                for row in fixture.tasks]
    declared = [(row["task_id"], row["token"], row["layout"])
                for row in goal["tasks"]]
    if expected != declared:
        return {"schema": "integrated_efficiency_oracle_v1", "success": False,
                "reason": "goal_fixture_mismatch"}
    return fixture.evaluate()
