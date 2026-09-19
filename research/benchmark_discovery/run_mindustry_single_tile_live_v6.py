"""Run Mindustry single-tile control only after the output-schema gate passes."""
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
LIVE = HERE.parent / "live_control"
sys.path.insert(0, str(LIVE))

from schema_preflight_gate_v1 import require_compatible
import run_mindustry_single_tile_live_v5 as prior

OUT = HERE / "results/mindustry-single-tile-live-06"
CACHE = LIVE / "results/schema-preflight-gate-01/cache"


def resolve(entries):
    return [{"name": entry["name"], "schema": HERE.parent / entry["schema"]} for entry in entries]


def authorize_then_continue(entries, cache_dir, gate_dir, workspace, continuation):
    """Invoke continuation only after every output schema is endpoint compatible."""
    report = require_compatible(resolve(entries), cache_dir, gate_dir, workspace)
    assert report["accepted"] is True
    return report, continuation()


def main():
    plan = json.loads((OUT / "preregistration.json").read_text(encoding="utf-8"))

    def continue_live():
        prior.OUT = OUT
        prior.model_runtime.WORKSPACE = OUT / "empty-workspace"
        return prior.main()

    authorize_then_continue(plan["preflight_schemas"], CACHE, OUT / "schema-preflight",
                            OUT / "empty-workspace", continue_live)


if __name__ == "__main__": main()
