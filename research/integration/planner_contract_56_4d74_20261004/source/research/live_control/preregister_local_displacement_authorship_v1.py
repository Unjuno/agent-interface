"""Freeze a matched Luna/Astra local-postcondition authorship probe."""
import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
OUT = HERE / "results/local-displacement-authorship-01"
IMAGE = HERE / "results/local-displacement-x11-02/target/001.png"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    OUT.mkdir(parents=True, exist_ok=False)
    prompt = """You are authoring a read-only local visual postcondition for an already admitted GUI program.

Task: the large red rectangle in the attached 1280x800 Inkscape screenshot must move exactly 24 screen pixels to the right with no vertical displacement before a later Save step may run. The screenshot is source observation sequence 1. Select a compact, spatially detailed RGB patch around the large red rectangle so an immutable patch matcher can locate the same object after movement. The patch uses [x,y,width,height], each dimension 4..96, and must fit the screenshot. Do not select a toolbar swatch or other red icon.

Return exactly one JSON object and no markdown or explanation. Use exactly these fields and fixed values except for the patch box and postcondition_id:
{"op":"local_displacement_postcondition","postcondition_id":"short nonempty identifier","source_sequence":1,"box":[x,y,width,height],"target_delta":[24,0],"tolerance_px":1,"required_samples":2,"sample_interval_ms":50,"timeout_ms":500,"on_unmet":"needs_decision"}

This object cannot issue input, prove semantic task success or grant authority. It only gates a later step that was already admitted from this source observation.
"""
    (OUT / "prompt.txt").write_text(prompt, encoding="utf-8")
    sources = [
        "preregister_local_displacement_authorship_v1.py",
        "run_local_displacement_authorship_v1.py",
        "parse_local_displacement_author_v1.py",
        "local_displacement_postcondition_v1.py", "visual_anchor.py",
        "model_pair_runner_v2.py",
    ]
    plan = {
        "status": "preregistered_before_model_execution",
        "question": "can the model author a strict target patch from one presented source frame whose condition accepts retained exact 24px samples and rejects retained exact 20px samples",
        "order": ["luna-1", "astra-1", "astra-2", "luna-2"],
        "routes": {"luna": {"model": "gpt-5.6-luna", "effort": "low"},
                   "astra": {"model": "gpt-6-astra", "effort": "medium"}},
        "image": str(IMAGE), "image_sha256": sha(IMAGE),
        "prompt_sha256": sha(OUT / "prompt.txt"),
        "source_sequence": 1,
        "retained_evaluation": {
            "target": "local-displacement-x11-02/target observations 7 and 8; independently reconstructed delta [24,0]",
            "partial": "local-displacement-x11-02/partial observations 8 and 9; independently reconstructed delta [20,0]",
        },
        "primary_endpoint": "strict parse and local evaluator: target met, partial not met",
        "secondary_endpoints": ["box", "target overlap", "reported input/cached/output tokens", "runner wall time"],
        "decision_rule": "advance a route only if both first outputs parse strictly and each authored condition returns met on both target samples and non-met on both partial samples; otherwise hold that route; no retries or replacement",
        "interpretation": "fixed-context model authorship feasibility over retained frames; no live model-controlled input, speed, population, generalization or promotion claim",
        "sources": {name: sha(HERE / name) for name in sources},
    }
    (OUT / "preregistration.json").write_text(json.dumps(plan, indent=2) + "\n")
    print(json.dumps(plan, indent=2))


if __name__ == "__main__":
    main()
