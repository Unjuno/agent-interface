"""Run v2 scoring logic against the corrected-schema v3 frozen allocation."""
from pathlib import Path

import run_target_handle_model_screen_v2 as shared


HERE = Path(__file__).resolve().parent
shared.ROOT = HERE / "results/target-handle-model-screen-03"
shared.SCHEMA = HERE / "target_action_union_schema_v2.json"


if __name__ == "__main__":
    shared.main()
