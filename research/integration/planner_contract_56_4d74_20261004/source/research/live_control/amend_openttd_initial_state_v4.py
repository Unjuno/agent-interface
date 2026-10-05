"""Record a pre-execution implementation-only correction to the v4 preregistration."""
import hashlib
import json
import os
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE / "results/timing-envelope-openttd-matched-04"
PREREGISTRATION = ROOT / "preregistration.json"
TARGET = HERE.parent / "openttd_task/interactive_v7.py"
ORIGINAL_SHA256 = "c691768d886d2d03e38b46efb039951e6cdeb09d81035a4c0c6264482c8fe480"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


assert PREREGISTRATION.exists()
assert PREREGISTRATION.stat().st_mtime_ns < TARGET.stat().st_mtime_ns
plan = {
    "study": "timing-envelope-openttd-matched-04",
    "status": "AMENDED_BEFORE_EXECUTION",
    "reason": (
        "Static inspection found that four initial-score assertions used descriptive "
        "names rather than the fixed guarded_score.py result keys."
    ),
    "scope": "implementation-only key-name repair; no GUI episode or model call had started",
    "original_source_sha256": ORIGINAL_SHA256,
    "corrected_source_sha256": digest(TARGET),
    "changes": {
        "target_only_has_road": "target_owned_roads",
        "target_connected_both_directions": "bidirectional_connections",
        "forbidden_row_has_no_road": "forbidden_row_clear",
        "surrounding_road_owner_unchanged": "unchanged",
    },
    "unchanged": [
        "execution order",
        "task and canonical save",
        "pre-opened road-toolbar factor",
        "fixed Astra medium route",
        "nine-turn bound",
        "hard success gate",
        "primary measurements",
        "failure and interpretation rules",
    ],
    "amendment_script_sha256": digest(Path(__file__)),
}
path = ROOT / "preregistration-amendment.json"
temporary = path.with_suffix(".json.tmp")
temporary.write_text(json.dumps(plan, indent=2) + "\n", encoding="utf-8")
os.replace(temporary, path)
print(path)
