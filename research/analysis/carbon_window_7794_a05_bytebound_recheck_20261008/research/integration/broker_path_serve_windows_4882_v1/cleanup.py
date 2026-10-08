"""Remove only the two live junctions after their targets match the freeze."""
from __future__ import annotations

import json
import os
from pathlib import Path
import sys
import tempfile


def cleanup(fixture: Path) -> dict:
    fixture = fixture.resolve(strict=True)
    temp_root = Path(tempfile.gettempdir()).resolve(strict=True)
    if fixture.parent != temp_root or not fixture.name.startswith("broker-path-serve-windows-4882-05-"):
        raise ValueError("fixture is outside this allocation temp namespace")
    repo = fixture / "repo"
    expected = ((repo / "in-junction", repo / "internal"),
                (repo / "external-junction", fixture / "outside"))
    rows = []
    for link, target in expected:
        if not link.exists() and not link.is_junction():
            rows.append({"entry": link.name, "status": "ABSENT"})
        elif not link.is_junction() or link.resolve(strict=True) != target.resolve(strict=True):
            rows.append({"entry": link.name, "status": "REFUSED_IDENTITY_MISMATCH"})
        else:
            os.rmdir(link)
            rows.append({"entry": link.name, "status": "REMOVED_VERIFIED_JUNCTION"})
    return {"schema": "broker_path_serve_windows_4882_cleanup_v1", "results": rows,
            "fixture_tree_removed": False,
            "scope": "two verified junction entries only; no recursive deletion"}


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: cleanup.py FIXTURE_DIR")
    print(json.dumps(cleanup(Path(sys.argv[1])), sort_keys=True))
