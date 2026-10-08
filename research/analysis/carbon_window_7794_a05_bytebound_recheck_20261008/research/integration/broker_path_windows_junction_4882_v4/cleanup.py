"""Remove only verified junction entries; retain the surrounding temp fixture."""
from __future__ import annotations

import json
import os
from pathlib import Path
import sys
import tempfile


def cleanup(fixture: Path) -> dict:
    fixture = fixture.resolve(strict=True)
    temp_root = Path(tempfile.gettempdir()).resolve(strict=True)
    if fixture.parent != temp_root or not fixture.name.startswith("broker-path-junction-4882-04-"):
        raise ValueError("fixture is outside the exact allocation temp namespace")
    repo = fixture / "repo"
    expected = ((repo / "in-junction", repo / "internal"),
                (repo / "external-junction", fixture / "outside"))
    results = []
    for link, target in expected:
        if not link.exists() and not link.is_junction():
            results.append({"entry": link.name, "status": "ABSENT"})
            continue
        if not link.is_junction() or link.resolve(strict=True) != target.resolve(strict=True):
            results.append({"entry": link.name, "status": "REFUSED_IDENTITY_MISMATCH"})
            continue
        os.rmdir(link)
        results.append({"entry": link.name, "status": "REMOVED_VERIFIED_JUNCTION"})
    return {"schema": "broker_path_windows_junction_4882_v4_cleanup_v1",
            "results": results, "fixture_tree_removed": False,
            "scope": "two exact junction directory entries only; no recursive deletion"}


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: cleanup.py FIXTURE_DIR")
    print(json.dumps(cleanup(Path(sys.argv[1])), sort_keys=True))
