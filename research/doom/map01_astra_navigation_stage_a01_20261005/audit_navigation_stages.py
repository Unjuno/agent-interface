"""Independent raw-source audit for retrospective MAP01 viewpoint annotations."""
import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
RESULT_ROOT = REPO / "research/doom/results/map01-astra-attempt-v1"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    freeze = json.loads((HERE / "FREEZE.json").read_text())
    mismatches = []
    for relative, expected in freeze["inputs"].items():
        path = REPO / relative
        if not path.is_file() or path.stat().st_size != expected["bytes"] or sha(path) != expected["sha256"]:
            mismatches.append({"input": relative, "error": "missing-or-hash-mismatch"})

    annotations = json.loads((HERE / "ANNOTATIONS.json").read_text())
    manifest = json.loads((RESULT_ROOT / "frame-manifest.json").read_text())
    report = json.loads((RESULT_ROOT / "report.json").read_text())
    score = json.loads((RESULT_ROOT / "score.json").read_text())
    video = json.loads((RESULT_ROOT / "video.json").read_text())
    environment = json.loads((RESULT_ROOT / "environment.json").read_text())

    if len(annotations["frames"]) != 13 or len(manifest) != 13:
        mismatches.append({"error": "frame-count-not-13"})
    for i, (annotation, source) in enumerate(zip(annotations["frames"], manifest)):
        if annotation["iteration"] != i or source["iteration"] != i:
            mismatches.append({"iteration": i, "error": "noncontiguous-frame-order"})
        if annotation["file"] != source["file"] or annotation["sha256"] != source["sha256"]:
            mismatches.append({"iteration": i, "error": "annotation-manifest-binding-mismatch"})
        frame_path = RESULT_ROOT / source["file"]
        if not frame_path.is_file() or sha(frame_path) != source["sha256"]:
            mismatches.append({"iteration": i, "error": "frame-hash-mismatch"})
        if not annotation.get("stage") or not annotation.get("cue"):
            mismatches.append({"iteration": i, "error": "missing-stage-or-cue"})

    decisions = report.get("decisions", [])
    if len(decisions) != 13 or [d.get("iteration") for d in decisions] != list(range(13)):
        mismatches.append({"error": "report-decision-join-incomplete"})
    receipts = [t for d in decisions for t in d.get("execution_trace", []) if t.get("role") == "primary"]
    receipt_results = [t.get("receipt", {}).get("result") for t in receipts]
    visible = receipt_results.count("visible_change")
    no_effect = receipt_results.count("no_visible_effect")
    authored = sum(len(d.get("action", {}).get("contingencies", [])) for d in decisions)
    taken = sum(1 for d in decisions if d.get("contingency_branch") is not None)
    if (len(receipts), visible, no_effect, authored, taken) != (26, 25, 1, 8, 0):
        mismatches.append({"error": "command-or-contingency-totals-mismatch"})
    if score.get("map_exit") is not False or score.get("player_dead") is not True or score.get("kill_count") != 1:
        mismatches.append({"error": "terminal-score-mismatch"})
    if (report.get("score", {}).get("map_exit") is not False or
            report.get("score", {}).get("player_dead") is not True or
            report.get("score", {}).get("kill_count") != 1):
        mismatches.append({"error": "report-terminal-score-mismatch"})

    audit = {
        "schema": "map01-astra-navigation-stage-a01-independent-audit-v1",
        "disposition": "PASS_SCOPED_VIEWPOINT_STAGES_HOLD_EXACT_ROUTE" if not mismatches else "FAIL_MISMATCH",
        "frame_annotations_recomputed": len(annotations["frames"]),
        "report_decisions_joined": len(decisions),
        "primary_command_receipts_recomputed": len(receipts),
        "visible_change_receipts_recomputed": visible,
        "no_visible_effect_receipts_recomputed": no_effect,
        "contingencies_authored_recomputed": authored,
        "contingency_branches_taken_recomputed": taken,
        "terminal": {"map_exit": score.get("map_exit"), "player_dead": score.get("player_dead"), "kill_count": score.get("kill_count")},
        "input_count_hash_checked": len(freeze["inputs"]),
        "mismatch_count": len(mismatches),
        "mismatches": mismatches,
        "scope": "hash-bound retrospective visual labels joined to retained report, event stream, video metadata, environment and score; no execution",
        "limits": "viewpoint stages do not establish coordinates, exact route, distance traveled, objective progress, or cause of death; camera rotation and translation both change the view",
    }
    (HERE / "AUDIT.json").write_text(json.dumps(audit, indent=2) + "\n")
    (HERE / "RESULT.json").write_text(json.dumps({
        "schema": "map01-astra-navigation-stage-a01-result-v1",
        "disposition": audit["disposition"],
        "claim": "The retained sequence supports distinct viewpoint-stage labels but does not identify exact route progress.",
        "annotation_method": annotations["label_method"],
        "annotation_count": len(annotations["frames"]),
        "primary_command_receipts": len(receipts),
        "visible_change_receipts": visible,
        "no_visible_effect_receipts": no_effect,
        "contingencies_authored": authored,
        "contingency_branches_taken": taken,
        "terminal": audit["terminal"],
        "video": {"frames": video["frames"], "fps": video["fps"], "playback_seconds": video["playback_seconds"]},
        "environment": {"vizdoom": environment["vizdoom"], "mode": environment["mode"], "map": environment["map"], "skill": environment["skill"]},
        "scope_limit": audit["limits"],
        "audit": "AUDIT.json",
    }, indent=2) + "\n")
    print(json.dumps({k: audit[k] for k in ("disposition", "frame_annotations_recomputed", "primary_command_receipts_recomputed", "mismatch_count")}))
    if mismatches:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
