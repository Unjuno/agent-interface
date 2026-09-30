from __future__ import annotations

import argparse
import hashlib
import json
import base64
from pathlib import Path


MODEL = "qwen2.5vl:3b"
DIGEST = "fb90415cde1ef08aa669ae74b082d49b158729b6db1ab183c941417d507e71a1"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def iou(a, b):
    if not isinstance(a, list) or len(a) != 4 or not all(isinstance(x, int) for x in a):
        return 0.0
    x1, y1 = max(a[0], b[0]), max(a[1], b[1])
    x2, y2 = min(a[2], b[2]), min(a[3], b[3])
    inter = max(0, x2-x1) * max(0, y2-y1)
    area_a = max(0, a[2]-a[0]) * max(0, a[3]-a[1])
    area_b = max(0, b[2]-b[0]) * max(0, b[3]-b[1])
    union = area_a + area_b - inter
    return inter / union if union else 0.0


def audit(root: Path) -> dict:
    errors = []
    pre = json.loads((root / "data" / "PREFORMAL.json").read_text(encoding="utf-8"))
    samples = [json.loads(line) for line in (root / "sampler.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    baseline = json.loads((root / "baseline.json").read_text(encoding="utf-8"))
    if not samples:
        errors.append("no_gpu_samples")
    baseline_used = baseline.get("memory_used_mib")
    results = []
    for case in pre["formal_cases"]:
        path = root / "formal" / f"{case['case_id']}.json"
        if not path.is_file():
            errors.append(f"missing:{case['case_id']}")
            continue
        rec = json.loads(path.read_text(encoding="utf-8"))
        if rec.get("error"):
            errors.append(f"request_error:{case['case_id']}")
            continue
        img = (root / "data" / case["image_path"]).read_bytes()
        if sha(img) != case["image_sha256"] or rec.get("image_sha256") != case["image_sha256"]:
            errors.append(f"image_hash:{case['case_id']}")
        if rec.get("model") != MODEL or rec.get("expected_digest") != DIGEST:
            errors.append(f"model_identity:{case['case_id']}")
        req = rec.get("request", {})
        if req.get("model") != MODEL or req.get("stream") is not False:
            errors.append(f"request_binding:{case['case_id']}")
        if req.get("options") != {"temperature": 0, "seed": case["seed"], "num_predict": 128}:
            errors.append(f"options:{case['case_id']}")
        if len(req.get("messages", [])) != 1 or req["messages"][0].get("content") != pre["prompt"]:
            errors.append(f"prompt:{case['case_id']}")
        try:
            encoded_image = req["messages"][0]["images"][0]
            if sha(base64.b64decode(encoded_image, validate=True)) != case["image_sha256"]:
                errors.append(f"request_image:{case['case_id']}")
        except (KeyError, IndexError, ValueError, TypeError):
            errors.append(f"request_image:{case['case_id']}")
        try:
            returned = json.loads(rec["response"]["message"]["content"])
        except (TypeError, KeyError, json.JSONDecodeError):
            errors.append(f"response_json:{case['case_id']}")
            continue
        if not isinstance(returned.get("present"), bool):
            errors.append(f"response_present_type:{case['case_id']}")
            continue
        if set(returned) != {"present", "box"}:
            errors.append(f"response_schema:{case['case_id']}")
        hit = False
        abstain = returned["present"] is False and returned.get("box") is None
        if case["present"]:
            hit = returned["present"] is True and iou(returned.get("box"), case["target_box"]) >= 0.5
            if returned["present"] and not hit:
                errors.append(f"positive_box_invalid:{case['case_id']}")
        elif not abstain:
            errors.append(f"absent_not_abstained:{case['case_id']}")
        start, end = rec.get("started_utc_ns", 0), rec.get("ended_utc_ns", 0)
        overlap = [s for s in samples if start <= s.get("utc_ns", -1) <= end]
        placement = [s for s in overlap if isinstance(s.get("memory_used_mib"), int)
                     and isinstance(baseline_used, int) and s["memory_used_mib"] > baseline_used
                     and "gpu" in s.get("ollama_ps_stdout", "").lower()]
        if not placement:
            errors.append(f"gpu_placement_interval:{case['case_id']}")
        results.append({"case_id": case["case_id"], "positive_hit": hit, "absent_abstain": abstain,
                        "iou": iou(returned.get("box"), case["target_box"]) if case["present"] else None,
                        "placement_samples": len(placement), "response": returned})
    positive = sum(r["positive_hit"] for r in results if r["case_id"].startswith("positive-"))
    absent = sum(r["absent_abstain"] for r in results if r["case_id"].startswith("absent-"))
    complete = len(results) == 8
    decision = "PASS_DIAGNOSTIC_SCOPED" if complete and not errors and positive >= 5 and absent == 2 else (
        "FAIL_EASY_LAYOUT_CAPABILITY_NOT_ESTABLISHED" if complete and not errors and positive < 5 else "HOLD_AUDIT_OR_GPU_GATE")
    return {"schema": "visual-encoding-570-local-r4-audit-v1", "decision": decision,
            "formal_complete": complete, "positive_hits": positive, "positive_total": 6,
            "absent_abstentions": absent, "absent_total": 2, "errors": errors, "rows": results}


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--root", type=Path, required=True)
    p.add_argument("--out", type=Path)
    args = p.parse_args()
    result = audit(args.root)
    data = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.write_text(data, encoding="utf-8")
    print(data, end="")


if __name__ == "__main__":
    main()

