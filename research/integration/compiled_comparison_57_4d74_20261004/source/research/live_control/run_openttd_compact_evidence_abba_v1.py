"""Run the preregistered fixed-evidence full-versus-compact ABBA comparison."""
import json
import shutil
from pathlib import Path

from evidence_target_contract_v1 import validate
from openttd_compact_hover_sheet_v1 import build
import run_openttd_active_evidence_pair_v1 as base


HERE = Path(__file__).resolve().parent
OUT = HERE / "results/openttd-compact-evidence-abba-01"
PRIOR = HERE / "results/openttd-active-evidence-pair-02/2-stable-seed991004"
base.WORKSPACE = OUT / "empty-workspace"


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def main():
    plan = read(OUT / "preregistration.json")
    for name, digest in plan["sources"].items():
        assert base.sha(HERE / name) == digest, name
    for name, digest in plan["fixed_evidence"].items():
        assert base.sha(HERE / name) == digest, name

    stable = read(PRIOR / "result.json")
    readiness = stable["hover_readiness"]
    full_source = PRIOR / "hover-presentation.png"
    full = OUT / "full-presentation.png"
    shutil.copy2(full_source, full)
    compact = OUT / "compact-presentation.png"
    compact_manifest = build(readiness, PRIOR / "runtime", compact)
    base.dump(OUT / "compact-manifest.json", compact_manifest)

    results = []
    for name in plan["execution_order"]:
        condition = plan["condition_by_call"][name]
        image = full if condition == "full" else compact
        model = base.model_call(
            OUT, name, plan["common_prompt"], image,
            "evidence_target_reference_responder_v2.txt",
            "evidence_target_contract_schema_v2.json")
        binding = validate(model["typed"], readiness)
        correct = binding["point"] == [485, 51] and binding["receipt"]["receipt_index"] == 5
        results.append({
            "name": name, "condition": condition, "image": str(image),
            "image_sha256": base.sha(image), "image_bytes": image.stat().st_size,
            "model": model, "binding": binding, "correct": correct})
        base.dump(OUT / "partial-results.json", results)

    full_rows = [row for row in results if row["condition"] == "full"]
    compact_rows = [row for row in results if row["condition"] == "compact"]
    mean = lambda rows, key: sum(row["model"]["usage"][key] for row in rows) / len(rows)
    full_mean = mean(full_rows, "input_tokens")
    compact_mean = mean(compact_rows, "input_tokens")
    gate = {
        "all_four_strict_correct": all(row["correct"] for row in results),
        "compact_two_of_two_correct": all(row["correct"] for row in compact_rows),
        "full_two_of_two_correct": all(row["correct"] for row in full_rows),
        "compact_mean_reported_input_tokens_lower": compact_mean < full_mean,
    }
    gate["passed"] = all(gate.values())
    report = {
        "results": results,
        "reported_input_tokens": {
            row["name"]: row["model"]["usage"]["input_tokens"] for row in results},
        "mean_reported_input_tokens": {"full": full_mean, "compact": compact_mean},
        "mean_reduction_tokens": full_mean - compact_mean,
        "mean_reduction_fraction": (full_mean - compact_mean) / full_mean,
        "promotion_gate": gate,
        "decision": ("RETAIN_COMPACT_VERIFIED_EVIDENCE_PRESENTATION"
                     if gate["passed"] else "HOLD_AND_PRESERVE_COMPACT_EVIDENCE_ABBA"),
        "scope": plan["scope"],
    }
    base.dump(OUT / "report.json", report)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
