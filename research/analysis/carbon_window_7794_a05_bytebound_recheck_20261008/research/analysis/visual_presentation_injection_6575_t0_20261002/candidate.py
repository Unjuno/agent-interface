"""Single deterministic presentation-transform candidate invocation."""
from __future__ import annotations
import hashlib, json, sys
from pathlib import Path
from ppm import crop, decode

ROOT = Path(__file__).parent
SPEC = json.loads((ROOT / "fixtures.json").read_text())
FREEZE = json.loads((ROOT / "FREEZE.json").read_text())

def sha(raw: bytes) -> str: return hashlib.sha256(raw).hexdigest()

def visible(rect, required):
    x0, y0, x1, y1 = rect
    a, b, c, d = required
    return x0 <= a and y0 <= b and x1 >= c and y1 >= d

def main(outdir: str):
    if FREEZE.get("status") != "AUTHORIZED" or not FREEZE.get("resource_assignment_record"):
        raise RuntimeError("missing exact #5085 assignment; candidate invocation refused")
    for rel, expected in FREEZE["source_sha256"].items():
        if sha((ROOT / rel).read_bytes()) != expected:
            raise RuntimeError(f"frozen source hash mismatch: {rel}")
    out = Path(outdir); out.mkdir(parents=True, exist_ok=False)
    rows = []
    for condition in SPEC["conditions"]:
        src_path = ROOT / "sources" / f"{condition}.ppm"
        source = src_path.read_bytes()
        sw, sh, _ = decode(source)
        source_hash = sha(source)
        for arm in SPEC["arms"]:
            if arm == "FULL": views = [("full", source)]
            elif arm == "FULL+CONTEXT_CROP":
                views = [("full", source), ("context", crop(source, SPEC["context_crop"]))]
            elif arm == "SHAM_CROP":
                views = [("full", source), ("sham", crop(source, SPEC["sham_crop"]))]
            else:
                views = [("crop", crop(source, SPEC["context_crop"]))]
            accepted = True
            reason = "accepted"
            if arm == "CROP_ONLY":
                for key in ("task_target", "safety_cue"):
                    if not visible(SPEC["context_crop"], SPEC["required_regions"][key]):
                        accepted, reason = False, "required_region_hidden"
                        break
            refs = []
            for label, payload in views:
                name = f"{condition}__{arm.replace('+','_')}__{label}.ppm"
                (out / name).write_bytes(payload)
                w, h, _ = decode(payload)
                refs.append({"label": label, "file": name, "sha256": sha(payload), "width": w, "height": h})
            rows.append({"condition": condition, "arm": arm, "accepted": accepted,
                         "reason": reason, "source_sha256": source_hash,
                         "source_dimensions": [sw, sh], "views": refs})
        for negative in SPEC["negative_crops"]:
            neg_ok = all(visible(negative["rectangle"], SPEC["required_regions"][key])
                         for key in ("task_target", "safety_cue"))
            rows.append({"condition": condition, "arm": "CROP_ONLY_NEGATIVE",
                         "negative": negative["name"], "rectangle": negative["rectangle"], "accepted": neg_ok,
                         "reason": "accepted" if neg_ok else "required_region_hidden", "source_sha256": source_hash,
                         "source_dimensions": [sw, sh], "views": []})
    result = {"schema": "visual-presentation-t0-candidate-v1", "rows": rows}
    (out / "candidate.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    return 0

if __name__ == "__main__": raise SystemExit(main(sys.argv[1]))
