"""Audit that the first v23 allocation is retained as a pre-GUI failure."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    plan = read(HERE / "map01_cover_threat_v23_live_v1_prereg.json")
    failure = read(HERE / "results/map01-cover-threat-v23-live-01/failure.json")
    assert plan["status"] == "PREREGISTERED_BEFORE_FIRST_MODEL_CALL"
    assert plan["allocation_id"] == failure["allocation_id"]
    for path, expected in plan["source_sha256"].items():
        assert sha(HERE.parents[1] / path) == expected, path
    assert failure["disposition"] == "RETAINED_PRE_GUI_ENVIRONMENT_FAILURE"
    assert failure["rerun"] is False
    assert failure["model_calls_started"] == 0 and failure["gui_ready"] is False
    assert failure["input_programs_admitted"] == 0
    assert failure["controller_exit_code"] == 1
    assert failure["environment_diagnosis"]["default_python_vizdoom_available"] is False
    assert failure["environment_diagnosis"]["repository_target_vizdoom_version"] == "1.3.0"
    print({"passed": True, "disposition": failure["disposition"],
           "model_calls": 0, "input_programs": 0})


if __name__ == "__main__":
    main()
