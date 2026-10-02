import argparse
import hashlib
import json
from pathlib import Path


ARMS = ("timing_only", "preserved_view", "optional_cue")


def render(case, arm):
    changed = case["before_version"] != case["after_version"]
    if arm == "timing_only":
        view = None
    else:
        view = {
            "task_id": case["task_id"], "window_id": case["window_id"],
            "surface_id": case["surface_id"], "version": case["before_version"],
            "sha256": case["source_view_sha256"], "historical": changed,
        }
    if arm != "optional_cue":
        cue = {"offered": False, "status": "not_offered", "author": None, "text": None}
    elif case["cue"]["status"] == "not_written":
        cue = {"offered": True, "status": "unused", "author": None, "text": None}
    elif case["cue"]["version"] != case["after_version"]:
        cue = {"offered": True, "status": "stale_withheld", "author": "user", "text": None}
    else:
        cue = {"offered": True, "status": "used", "author": "user", "text": case["cue"]["text"]}
    return {
        "case_id": case["case_id"], "arm": arm, "task_id": case["task_id"],
        "window_id": case["window_id"], "surface_id": case["surface_id"],
        "interrupt_id": case["interrupt_id"], "question": case["question"],
        "answers": case["answers"], "priority": case["priority"],
        "delay_ms": 0 if case["priority"] == "emergency_release" else 1000,
        "before_version": case["before_version"], "current_version": case["after_version"],
        "state_change_warning": changed, "source_view": view, "cue": cue,
        "automated_actions": [], "source_view_digest": hashlib.sha256(
            (case["task_id"] + "\n" + case["window_id"] + "\n" + case["source_view_sha256"]).encode("utf-8")
        ).hexdigest(),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    payload = Path(args.fixture).read_bytes()
    fixture = json.loads(payload)
    ids = [case["case_id"] for case in fixture["cases"]]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate case id")
    rows = [render(case, arm) for case in fixture["cases"] for arm in ARMS]
    result = {"schema": "return-to-work-candidate-raw-v1",
              "fixture_sha256": hashlib.sha256(payload).hexdigest(),
              "case_order": ids, "arms": list(ARMS), "rows": rows}
    Path(args.output).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
