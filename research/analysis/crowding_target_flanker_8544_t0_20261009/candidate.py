#!/usr/bin/env python3
"""Emit the frozen no-model fixture responses for Issue #8544 T0."""
import argparse
import itertools
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def build(spec):
    f = spec["factors"]
    classes_by_presence = spec["planted_endpoint_classes_by_presence"]
    rows = []
    axes = (f["target_present"], f["spacing_px"], f["eccentricity_proxy_px"], f["target_size_px"], f["flanker_similarity"], f["placement"], f["seeds"])
    for present, spacing, eccentricity, size, similarity, placement, seed in itertools.product(*axes):
      for endpoint in classes_by_presence["present" if present else "absent"]:
        fixture_id = f"p{int(present)}-s{spacing}-e{eccentricity}-z{size}-{similarity}-{placement}-seed{seed}-{endpoint}"
        templates = spec["response_templates"]
        if endpoint == "correct_rejection":
            response = {"status":"not_found","identity":None,"point":None,"schema_valid":True}
        elif endpoint == "false_alarm":
            response = {"status":"found","identity":"phantom_target","point":[520,380],"schema_valid":True}
        else:
            response = templates[endpoint]
        rows.append({
            "fixture_id": fixture_id,
            "target_present": present,
            "spacing_px": spacing,
            "eccentricity_proxy_px": eccentricity,
            "target_size_px": size,
            "flanker_similarity": similarity,
            "placement": placement,
            "global_control_count": f["global_control_count"],
            "seed": seed,
            "split": "held_out" if seed in f["held_out_seeds"] else "development",
            "planted_endpoint_class": endpoint,
            "response": response
        })
    return {"schema": "issue-8544-candidate-raw-v1", "allocation": spec["allocation"], "rows": rows, "authority": "NONE"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--spec", default=str(ROOT / "spec.json"))
    ap.add_argument("--output", default=str(ROOT / "results/candidate.raw.json"))
    args = ap.parse_args()
    out = Path(args.output)
    if out.exists():
        raise SystemExit("refusing existing formal output")
    raw = build(json.loads(Path(args.spec).read_text()))
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(raw, sort_keys=True, separators=(",", ":")) + "\n")
    print(json.dumps({"allocation": raw["allocation"], "fixtures": len(raw["rows"]), "output": str(out)}, sort_keys=True))


if __name__ == "__main__":
    main()
