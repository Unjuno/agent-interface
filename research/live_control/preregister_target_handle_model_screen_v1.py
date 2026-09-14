"""Freeze an ABBA model/token screen for coordinate grounding versus handle use."""
import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
OUT = HERE / "results/target-handle-model-screen-01"
IMAGE = HERE / "results/chromium-target-handle-pair-01/positive/runtime/014.png"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    OUT.mkdir(parents=True, exist_ok=False)
    coordinate = """You control the final action on an isolated Chromium form. The exact value t991005 is already visible in the Value field. Use the attached current 1280x800 screenshot to click the visible Save button once. Return ONLY one JSON object with exactly these fields: {\"op\":\"pointer_click\",\"x\":INTEGER,\"y\":INTEGER,\"button\":1,\"duration_ms\":80}. Coordinates are absolute screenshot pixels. No prose, markdown, tools or shell."""
    handle = """You control the final action on an isolated Chromium form. The exact value t991005 is already in the Value field. Current runtime evidence: target handle h_save_form names Save; status REVALIDATED; exact textured region matched on the current fresh observation; permitted relation is offset [20,9]; ordinary admission is still required. Use that handle once. Return ONLY one JSON object with exactly these fields: {\"op\":\"pointer_click_target\",\"target_handle\":\"h_save_form\",\"offset\":[20,9],\"button\":1,\"duration_ms\":80}. Do not output coordinates, prose, markdown, tools or shell."""
    (OUT / "coordinate-prompt.txt").write_text(coordinate, encoding="utf-8", newline="\n")
    (OUT / "handle-prompt.txt").write_text(handle, encoding="utf-8", newline="\n")
    sources = ["preregister_target_handle_model_screen_v1.py",
               "target_handle_model_runner_v1.py", "run_target_handle_model_screen_v1.py"]
    plan = {"status": "preregistered_before_model_calls",
        "study": "target-handle-model-screen-01", "order": ["coordinate", "handle", "handle", "coordinate"],
        "model": "gpt-5.6-luna", "effort": "low", "fast_mode": "disabled",
        "task": "choose the final Save action for the same archived moved Chromium form containing t991005",
        "coordinate_arm": "attached exact live frame; infer absolute Save point",
        "handle_arm": "no image; exact REVALIDATED handle record and permitted relation",
        "correctness": {"coordinate": "point inside [270,242,312,260]",
                        "handle": "exact h_save_form action and [20,9] relation"},
        "primary_metrics": ["correct calls", "reported input/cached/output tokens", "runner duration"],
        "promotion": "advance to matched fresh live execution only if4/4 strict outputs are correct and handle mean reported input tokens are lower",
        "failure_policy": "retain first four calls; no retries or prompt repair",
        "image_sha256": sha(IMAGE),
        "prompt_sha256": {"coordinate": sha(OUT / "coordinate-prompt.txt"),
                          "handle": sha(OUT / "handle-prompt.txt")},
        "sources": {name: sha(HERE / name) for name in sources},
        "scope": "four fixed-state model calls; handle arm intentionally omits image after runtime revalidation; no new GUI input, causal latency, live task, cost or general token claim"}
    (OUT / "plan.json").write_text(json.dumps(plan, indent=2) + "\n",
                                    encoding="utf-8", newline="\n")
    print(json.dumps(plan, indent=2))


if __name__ == "__main__":
    main()
