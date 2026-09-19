"""Audit the frozen target-handle ABBA screen without rerunning model calls."""
import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE / "results/target-handle-model-screen-01"
IMAGE = HERE / "results/chromium-target-handle-pair-01/positive/runtime/014.png"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def mean(values):
    return sum(values) / len(values)


def main():
    plan = json.loads((ROOT / "plan.json").read_text(encoding="utf-8"))
    report = json.loads((ROOT / "report.json").read_text(encoding="utf-8"))
    source_checks = {
        name: sha(HERE / name) == expected
        for name, expected in plan["sources"].items()
    }
    prompt_checks = {
        mode: sha(ROOT / f"{mode}-prompt.txt") == expected
        for mode, expected in plan["prompt_sha256"].items()
    }
    results = report["results"]
    coordinate = [row for row in results if row["mode"] == "coordinate"]
    handle = [row for row in results if row["mode"] == "handle"]
    coordinate_mean = mean([row["usage"]["input_tokens"] for row in coordinate])
    handle_mean = mean([row["usage"]["input_tokens"] for row in handle])
    coordinate_uncached_mean = mean([
        row["usage"]["input_tokens"] - row["usage"]["cached_input_tokens"]
        for row in coordinate
    ])
    handle_uncached_mean = mean([
        row["usage"]["input_tokens"] - row["usage"]["cached_input_tokens"]
        for row in handle
    ])
    audit = {
        "study": plan["study"],
        "order_matches": [row["mode"] for row in results] == plan["order"],
        "source_hashes_match": source_checks,
        "prompt_hashes_match": prompt_checks,
        "image_hash_matches": sha(IMAGE) == plan["image_sha256"],
        "calls": len(results),
        "correct": sum(bool(row["correct"]) for row in results),
        "reported_input_tokens": {
            "coordinate": [row["usage"]["input_tokens"] for row in coordinate],
            "handle": [row["usage"]["input_tokens"] for row in handle],
            "coordinate_mean": coordinate_mean,
            "handle_mean": handle_mean,
            "handle_minus_coordinate_mean": handle_mean - coordinate_mean,
        },
        "derived_non_cached_input_tokens": {
            "coordinate_mean": coordinate_uncached_mean,
            "handle_mean": handle_uncached_mean,
            "handle_minus_coordinate_mean": handle_uncached_mean - coordinate_uncached_mean,
        },
        "promotion_gate": {
            "all_four_correct": len(results) == 4 and all(row["correct"] for row in results),
            "handle_reported_input_mean_lower": handle_mean < coordinate_mean,
            "passed": len(results) == 4 and all(row["correct"] for row in results)
                      and handle_mean < coordinate_mean,
        },
        "interpretation": (
            "The fixed-state correctness screen passes, but the preregistered promotion "
            "gate fails. The second identical handle call reports 54,244 input tokens, "
            "including 42,240 cached, so the caller context is not controlled tightly "
            "enough to attribute token differences to image omission. Retain without retry."
        ),
    }
    if not (audit["order_matches"] and audit["image_hash_matches"]
            and all(source_checks.values()) and all(prompt_checks.values())):
        raise RuntimeError("frozen evidence audit failed")
    (ROOT / "audit.json").write_text(json.dumps(audit, indent=2) + "\n",
                                     encoding="utf-8", newline="\n")
    print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    main()
