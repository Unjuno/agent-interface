"""Independent audit for the retained no-op release receipt construction."""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
COMMIT = "6a22a43ce6ed3a3acc687c561e0dfcc37a5f294b"


def audit():
    for line in (HERE / "FILES.sha256").read_text(encoding="utf-8").splitlines():
        expected, name = line.split("  ", 1)
        actual = hashlib.sha256((HERE / name).read_bytes()).hexdigest()
        assert actual == expected, (name, actual, expected)
    freeze = json.loads((HERE / "FREEZE.json").read_text(encoding="utf-8"))
    for path, expected in freeze["sources"].items():
        source = subprocess.check_output(["git", "show", f"{COMMIT}:{path}"])
        actual = hashlib.sha1(b"blob " + str(len(source)).encode() + b"\0" + source).hexdigest()
        assert actual == expected, (path, actual, expected)
    result = json.loads((HERE / "RESULT.json").read_text(encoding="utf-8-sig"))
    assert result["sources"] == freeze["sources"]
    assert result["synthetic_keysym_map"] == {"W": 77, "A": 77}
    assert result["first_up_receipt"]["x11_release_and_sync_completed_before_return"] is True
    assert result["second_up_receipt"]["x11_release_and_sync_completed_before_return"] is True
    assert result["calls_after_first_up"]["key_release_requests"] == 1
    assert result["calls_after_second_up"]["key_release_requests"] == 1
    assert result["calls_after_first_up"]["sync_calls"] == 3
    assert result["calls_after_second_up"]["sync_calls"] == 3
    assert result["second_call_added_key_release_request"] == 0
    assert result["second_call_added_sync"] == 0
    return {
        "schema": "map01-v11-noop-release-receipt-audit-v1",
        "status": "PASS_SCOPED",
        "checks": [
            "artifact SHA256 inventory",
            "pinned V10/V11 source blobs",
            "second receipt claims release and sync",
            "second call performs neither a KeyRelease request nor sync",
            "scope excludes real input and game behavior",
        ],
    }


if __name__ == "__main__":
    print(json.dumps(audit(), indent=2, sort_keys=True))
