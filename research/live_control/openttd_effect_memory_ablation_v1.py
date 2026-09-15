"""Frozen archived OpenTTD effect-decision memory ablation."""
import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
PLAN = HERE / "openttd_effect_memory_ablation_v1_prereg.json"
INPUTS = HERE / "results/openttd-action-effect-memory-inputs-01"
OUT = HERE / "results/openttd-effect-memory-ablation-01"


def read(path): return json.loads(Path(path).read_text(encoding="utf-8"))
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def prompt(receipt):
    points = ", ".join(f"({p['x']},{p['y']})" for p in receipt["drag_points"])
    return (
        f"Context {receipt['context']}. Review the already-issued road-building drag through {points}. "
        f"Image 1 is exact current observation sequence {receipt['current_sequence']} after a separate "
        f"observation-only inspection. When three images are present, Image 2 is the full frame before "
        f"the action at sequence {receipt['before_sequence']} and Image 3 is the full frame immediately "
        f"after it at sequence {receipt['after_sequence']}. When exactly two images are present, Image 2 "
        "is a bounded three-panel sheet labelled before, after, and absolute RGB difference x4. When only "
        "Image 1 is present there is no archived visual memory. The prior drag completed with verified "
        "empty release. Pixel differences do not by themselves establish success. Decide whether the "
        "intended road segment is visibly observed in the current screen. Never repeat the drag."
    )


def images_for(root, arm):
    images = [root / "current.png"]
    if arm == "full_history": images += [root / "before.png", root / "after.png"]
    elif arm == "action_crop": images += [root / "action-effect-crop.png"]
    elif arm != "no_memory": raise ValueError("unknown arm")
    return images


def main():
    from openttd_effect_model_v1 import invoke

    plan = read(PLAN)
    if OUT.exists(): raise FileExistsError(OUT)
    for name, digest in plan["source_sha256"].items():
        if sha(HERE / name) != digest: raise ValueError("source hash changed: " + name)
    if sha(INPUTS / "manifest.json") != plan["input_manifest_sha256"]:
        raise ValueError("input manifest changed")
    manifest = read(INPUTS / "manifest.json")
    for entry in manifest["contexts"]:
        root = INPUTS / entry["name"]
        if sha(root / "receipt.json") != entry["receipt_sha256"]:
            raise ValueError("input receipt changed: " + entry["name"])
        receipt = read(root / "receipt.json")
        for label, artifact in receipt["artifacts"].items():
            if sha(root / label) != artifact["sha256"] or (root / label).stat().st_size != artifact["bytes"]:
                raise ValueError("input artifact changed: " + entry["name"] + "/" + label)
    OUT.mkdir(); (OUT / "prereg.json").write_bytes(PLAN.read_bytes())
    (OUT / "schema-preflight-workspace").mkdir()
    first = INPUTS / plan["contexts"][0]
    preflight_prompt = prompt(read(first / "receipt.json"))
    try:
        preflight = invoke(OUT / "schema-preflight", preflight_prompt, [first / "current.png"],
                           OUT / "schema-preflight-workspace")
    except Exception as error:
        preflight = {"status": "FAILED", "error": f"{type(error).__name__}: {error}"}
        report = {"schema": "openttd-effect-memory-ablation-report-v1", "completed": False,
                  "schema_preflight": preflight, "results": [], "formal_pass": False,
                  "allocation_retries": 0, "decision": "INCOMPLETE_RETAIN_FIRST_OUTCOME"}
        (OUT / "preflight.json").write_text(json.dumps(preflight, indent=2) + "\n", encoding="utf-8")
        (OUT / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        return 2
    (OUT / "preflight.json").write_text(json.dumps(preflight, indent=2) + "\n", encoding="utf-8")
    results = []
    for scheduled in plan["schedule"]:
        case = OUT / scheduled["name"]; case.mkdir(); (case / "empty-workspace").mkdir()
        root = INPUTS / scheduled["context"]; receipt = read(root / "receipt.json")
        images = images_for(root, scheduled["arm"]); text = prompt(receipt)
        row = {**scheduled, "status": "STARTED", "retry_count": 0,
               "ground_truth": receipt["independent_ground_truth"],
               "prompt_sha256": hashlib.sha256(text.encode()).hexdigest(),
               "images": [{"path": path.relative_to(HERE).as_posix(), "sha256": sha(path)} for path in images]}
        try:
            row["model"] = invoke(case / "model", text, images, case / "empty-workspace")
            decision = row["model"]["decision"]
            row["correct"] = decision["status"] == receipt["independent_ground_truth"]
            row["safe_next_action"] = decision["next_action"] == "advance_without_repeat"
            row["status"] = "COMPLETED"
        except Exception as error:
            row.update(status="FAILED", error=f"{type(error).__name__}: {error}")
        (case / "result.json").write_text(json.dumps(row, indent=2) + "\n", encoding="utf-8")
        results.append(row)
        if row["status"] != "COMPLETED": break
    completed = len(results) == len(plan["schedule"]) and all(r["status"] == "COMPLETED" for r in results)
    report = {"schema": "openttd-effect-memory-ablation-report-v1", "completed": completed,
              "schema_preflight": preflight, "results": results, "formal_pass": completed,
              "allocation_retries": 0, "decision": "INCOMPLETE_RETAIN_FIRST_OUTCOME"}
    if completed:
        stats = {arm: {"correct": sum(r["correct"] for r in results if r["arm"] == arm),
                       "safe_next_action": sum(r["safe_next_action"] for r in results if r["arm"] == arm),
                       "input_tokens": sum(r["model"]["usage"]["input_tokens"] for r in results if r["arm"] == arm),
                       "images": sum(r["model"]["visible_images_submitted"] for r in results if r["arm"] == arm)}
                 for arm in plan["arms"]}
        report["stats"] = stats
        crop, full, none = stats["action_crop"], stats["full_history"], stats["no_memory"]
        eligible = (crop["correct"] == 2 and crop["safe_next_action"] == 2
                    and crop["correct"] >= full["correct"] and crop["correct"] >= none["correct"]
                    and crop["input_tokens"] < full["input_tokens"])
        if eligible and none["correct"] == 2:
            report["decision"] = "CROP_REPLACES_FULL_HISTORY_ONLY;_NO_DEFAULT_MEMORY_CHANGE"
        elif eligible:
            report["decision"] = "CROP_ELIGIBLE_FOR_FRESH_HISTORY_NEEDED_TRANSFER"
        else:
            report["decision"] = "DO_NOT_TRANSFER_CROP"
    (OUT / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"completed": completed, "formal_pass": report["formal_pass"],
                      "decision": report["decision"]}, indent=2))
    return 0 if completed else 2


if __name__ == "__main__": raise SystemExit(main())
