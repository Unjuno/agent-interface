"""Independent audit for the retained keycode identity construction result."""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path


HERE = Path(__file__).resolve().parent


def audit():
    freeze = json.loads((HERE / "FREEZE.json").read_text(encoding="utf-8"))
    for line in (HERE / "FILES.sha256").read_text(encoding="utf-8").splitlines():
        expected, name = line.split("  ", 1)
        actual = hashlib.sha256((HERE / name).read_bytes()).hexdigest()
        assert actual == expected, (name, actual, expected)
    source = subprocess.check_output([
        "git", "show", f"{freeze['source_commit']}:{freeze['source_path']}"
    ])
    blob = hashlib.sha1(b"blob " + str(len(source)).encode() + b"\0" + source).hexdigest()
    assert blob == freeze["source_git_blob"], (blob, freeze["source_git_blob"])

    result = json.loads((HERE / "RESULT.json").read_text(encoding="utf-8-sig"))
    arms = result["arms"]
    assert len(arms) == 2
    control, alias = arms
    assert control["mapping"] == {"87": 87, "65": 65}
    assert alias["mapping"] == {"87": 77, "65": 77}
    for arm in arms:
        assert [row["key"] for row in arm["admissions"]] == ["W", "A"]
        assert arm["admission_keycodes"] == [None, None]
        assert arm["release_verified"] is True
        assert arm["reason"] == "cancelled"
    assert control["release_interval_count"] == 2
    assert control["release_keycodes"] == [87, 65]
    assert alias["release_interval_count"] == 1
    assert alias["release_keycodes"] == [77]
    assert "no real X server" in result["scope"]
    return {
        "schema": "map01-cancel-keycode-identity-audit-v1",
        "status": "PASS_SCOPED",
        "source_git_blob": blob,
        "checks": [
            "pinned source blob",
            "local artifact SHA256 inventory",
            "two admissions omit resolved keycode",
            "injective-map two-interval control",
            "alias-map one-interval disposition",
            "scope excludes live input and game qualification",
        ],
    }


if __name__ == "__main__":
    print(json.dumps(audit(), indent=2, sort_keys=True))
