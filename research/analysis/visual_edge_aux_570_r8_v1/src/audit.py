#!/usr/bin/env python3
"""Independent raw-only verifier/scorer; never imports the runner."""
from __future__ import annotations

import argparse
import base64
import hashlib
import io
import json
import math
from pathlib import Path

from PIL import Image, ImageChops, ImageFilter, ImageOps

EXPECTED_FORMAT = {
    "type": "object",
    "properties": {
        "present": {"type": "boolean"},
        "point": {"anyOf": [{"type": "array", "items": {"type": "integer"}, "minItems": 2, "maxItems": 2}, {"type": "null"}]},
    },
    "required": ["present", "point"], "additionalProperties": False,
}


def canon(x):
    return json.dumps(x, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def sha(b):
    return hashlib.sha256(b).hexdigest()


def load_jsonl(path):
    return [json.loads(x) for x in Path(path).read_text(encoding="utf-8").splitlines() if x.strip()]


def model_vram(ps):
    return any(x.get("name") == "qwen2.5vl:3b" and int(x.get("size_vram", 0)) > 0 for x in ps.get("models", []))


def audit(manifest, records, split, samples, baseline_mib):
    errors, scored = [], []
    rows = [r for r in manifest["rows"] if r["split"] == split]
    expected = {(r["case_id"], arm) for r in rows for arm in ("RAW", "EDGE")}
    observed = [(r.get("case_id"), r.get("arm")) for r in records]
    if len(records) != len(expected) or set(observed) != expected or len(set(observed)) != len(observed):
        errors.append("call_cardinality_or_identity")
    expected_order = []
    for i, row in enumerate(rows):
        expected_order.extend([(row["case_id"], arm) for arm in (("RAW", "EDGE") if i % 2 == 0 else ("EDGE", "RAW"))])
    if observed != expected_order:
        errors.append("paired_counterbalance_order")
    byid = {r["case_id"]: r for r in rows}
    for rec in records:
        cid, arm = rec.get("case_id"), rec.get("arm")
        row = byid.get(cid)
        if row is None:
            errors.append(f"unknown_case:{cid}"); continue
        if rec.get("split") != split or arm not in ("RAW", "EDGE"):
            errors.append(f"split_or_arm:{cid}"); continue
        req = rec.get("request", {})
        if sha(canon(req)) != rec.get("request_sha256"):
            errors.append(f"request_hash:{cid}:{arm}")
        if req.get("model") != "qwen2.5vl:3b" or req.get("options", {}).get("seed") != row["seed"]:
            errors.append(f"model_or_seed:{cid}:{arm}")
        if req.get("options") != {"temperature": 0, "seed": row["seed"], "top_p": 1, "top_k": 1, "num_ctx": 8192, "num_predict": 128} or req.get("stream") is not False or req.get("keep_alive") != "10m":
            errors.append(f"decoding_options:{cid}:{arm}")
        if req.get("format") != EXPECTED_FORMAT:
            errors.append(f"response_format:{cid}:{arm}")
        if rec.get("response", {}).get("model") != "qwen2.5vl:3b":
            errors.append(f"response_model:{cid}:{arm}")
        messages = req.get("messages", [])
        if len(messages) != 1 or messages[0].get("content") != row["prompt"]:
            errors.append(f"prompt_binding:{cid}:{arm}")
        else:
            imgs = messages[0].get("images", [])
            try:
                raw = base64.b64decode(imgs[0], validate=True)
                if sha(raw) != row["source_sha256"]:
                    errors.append(f"source_image_binding:{cid}:{arm}")
                if arm == "RAW" and len(imgs) != 1:
                    errors.append(f"raw_image_count:{cid}")
                if arm == "EDGE":
                    edge = base64.b64decode(imgs[1], validate=True)
                    if len(imgs) != 2 or sha(edge) != row["edge_sha256"]:
                        errors.append(f"edge_image_binding:{cid}")
                    else:
                        src_im = Image.open(io.BytesIO(raw)).convert("RGB")
                        edge_im = Image.open(io.BytesIO(edge)).convert("RGB")
                        expected_edge = ImageOps.autocontrast(ImageOps.grayscale(src_im).filter(ImageFilter.FIND_EDGES)).convert("RGB")
                        if src_im.size != (row["width"], row["height"]) or ImageChops.difference(edge_im, expected_edge).getbbox() is not None:
                            errors.append(f"edge_transform_mismatch:{cid}")
            except Exception:
                errors.append(f"image_decode:{cid}:{arm}")
        start, end = rec.get("start_ns", 0), rec.get("end_ns", 0)
        if not (isinstance(start, int) and isinstance(end, int) and 0 < start < end):
            errors.append(f"call_interval:{cid}:{arm}")
        elif not any(start <= s.get("timestamp_ns", 0) <= end and s.get("memory_used_mib", 0) > baseline_mib for s in samples):
            errors.append(f"gpu_sample_overlap:{cid}:{arm}")
        if not (model_vram(rec.get("ollama_ps_pre", {})) or model_vram(rec.get("ollama_ps_post", {}))):
            errors.append(f"ollama_gpu_placement:{cid}:{arm}")
        content = rec.get("response", {}).get("message", {}).get("content", "")
        try:
            answer = json.loads(content)
            if set(answer) != {"present", "point"} or not isinstance(answer["present"], bool):
                raise ValueError("schema")
            point = answer["point"]
            if point is not None and (not isinstance(point, list) or len(point) != 2 or any(type(v) is not int for v in point)):
                raise ValueError("point")
            if answer["present"] and point is None:
                raise ValueError("present_without_point")
            if not answer["present"] and point is not None:
                raise ValueError("absent_with_point")
        except Exception:
            errors.append(f"response_schema:{cid}:{arm}"); continue
        hit = False
        norm_error = 1.0
        if row["present"] and answer["present"] and point is not None:
            x, y = point
            if not (0 <= x < row["width"] and 0 <= y < row["height"]):
                errors.append(f"point_outside_canvas:{cid}:{arm}")
            x1, y1, x2, y2 = row["target_box"]
            hit = x1 <= x <= x2 and y1 <= y <= y2
            dx = max(x1 - x, 0, x - x2)
            dy = max(y1 - y, 0, y - y2)
            norm_error = math.hypot(dx, dy) / math.hypot(row["width"], row["height"])
        scored.append({"case_id": cid, "arm": arm, "present_truth": row["present"], "answer_present": answer["present"], "point": point, "positive_hit": hit, "absent_abstain": (not row["present"] and answer == {"present": False, "point": None}), "normalized_region_error": norm_error})
    byarm = {}
    for arm in ("RAW", "EDGE"):
        a = [x for x in scored if x["arm"] == arm]
        positives = [x for x in a if x["present_truth"]]
        absents = [x for x in a if not x["present_truth"]]
        byarm[arm] = {
            "positive_hits": sum(x["positive_hit"] for x in positives), "positive_n": len(positives),
            "absent_abstentions": sum(x["absent_abstain"] for x in absents), "absent_n": len(absents),
            "mean_normalized_region_error": (sum(x["normalized_region_error"] for x in positives) / len(positives)) if positives else None,
        }
    decision = "HOLD_AUDIT_OR_GPU" if errors else "CONSTRUCTION_AUDIT_PASS"
    if split == "formal" and not errors:
        raw, edge = byarm["RAW"], byarm["EDGE"]
        if edge["positive_hits"] < raw["positive_hits"] or edge["absent_abstentions"] < raw["absent_abstentions"]:
            decision = "REJECT_EDGE_HURTS_CORRECTNESS"
        elif raw["mean_normalized_region_error"] - edge["mean_normalized_region_error"] >= 0.05:
            decision = "PASS_EDGE_AUX_SCOPED"
        else:
            decision = "REJECT_NO_MATERIAL_EDGE_GAIN"
    return {"format": "visual-edge-aux-570-r8-audit-v1", "split": split, "decision": decision, "errors": errors, "metrics": byarm, "scored_rows": scored, "expected_calls": len(expected), "observed_calls": len(records), "gpu_baseline_mib": baseline_mib}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--records", required=True)
    ap.add_argument("--samples", required=True)
    ap.add_argument("--baseline-mib", type=int, required=True)
    ap.add_argument("--split", choices=["construction", "formal"], required=True)
    ap.add_argument("--output", required=True)
    a = ap.parse_args()
    manifest = json.loads(Path(a.manifest).read_text(encoding="utf-8"))
    samples = load_jsonl(a.samples)
    result = audit(manifest, load_jsonl(a.records), a.split, samples, a.baseline_mib)
    Path(a.output).write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"decision": result["decision"], "errors": result["errors"], "metrics": result["metrics"]}, sort_keys=True))


if __name__ == "__main__":
    main()
