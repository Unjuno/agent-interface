"""Freeze single-envelope controlled-context target-handle ABBA comparison."""
import hashlib
import json
from pathlib import Path
import subprocess


HERE = Path(__file__).resolve().parent
OUT = HERE / "results/target-handle-model-screen-04"
IMAGE = HERE / "results/chromium-target-handle-pair-01/positive/runtime/014.png"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    OUT.mkdir(parents=True, exist_ok=False)
    (OUT / "empty-workspace").mkdir()
    prompts = {
        "coordinate": (
            "The exact value t991005 is already visible in the Value field of the "
            "attached current 1280x800 Chromium screenshot. Click the visible Save "
            "button once. Set target.kind=absolute, choose absolute screenshot x/y, "
            "and set target_handle='', dx=0, dy=0."
        ),
        "handle": (
            "The exact value t991005 is already in the Value field. Current runtime "
            "evidence: target handle h_save_form names Save; status REVALIDATED; its "
            "exact textured region matched the current fresh observation; permitted "
            "relation is offset [20,9]. Click it once. Set target.kind=handle, x=0, "
            "y=0, target_handle=h_save_form, dx=20, dy=9."
        ),
    }
    for mode, prompt in prompts.items():
        (OUT / f"{mode}-prompt.txt").write_text(prompt, encoding="utf-8", newline="\n")
    sources = [
        "preregister_target_handle_model_screen_v4.py",
        "target_handle_model_runner_v2.py",
        "run_target_handle_model_screen_v4.py",
        "run_target_handle_model_screen_v2.py",
        "gui_action_responder_v1.txt",
        "target_action_envelope_schema_v1.json",
    ]
    node = r"C:\Program Files\nodejs\node.exe"
    cli = Path.home() / "AppData/Roaming/npm/node_modules/@openai/codex/bin/codex.js"
    version = subprocess.run(
        [node, str(cli), "--version"], capture_output=True, text=True, check=True
    ).stdout.strip()
    plan = {
        "status": "preregistered_before_model_calls",
        "study": "target-handle-model-screen-04",
        "predecessors": [
            {"study": "target-handle-model-screen-02",
             "outcome": "rejected before model: const properties lacked type"},
            {"study": "target-handle-model-screen-03",
             "outcome": "rejected before model: root anyOf was not type object"},
        ],
        "change": (
            "single root object and identical action envelope; all fields required; "
            "unused representation fields fixed by prompt and strict parser"
        ),
        "order": ["coordinate", "handle", "handle", "coordinate"],
        "model": "gpt-5.6-luna",
        "effort": "low",
        "fast_mode": "disabled",
        "codex_cli": version,
        "context_controls": [
            "model_instructions_file",
            "identical output schema",
            "identical output field count",
            "project_doc_max_bytes=0",
            "empty workspace",
            "ignore user config and rules",
            "tools disabled",
        ],
        "correctness": {
            "coordinate": "absolute point inside [270,242,312,260] and unused fields empty/zero",
            "handle": "exact h_save_form relation dx=20,dy=9 and unused x/y zero",
        },
        "promotion": {
            "correct": "4/4",
            "within_arm_input_range_max": 128,
            "handle_reported_input_mean_lower": True,
            "handle_derived_uncached_input_mean_lower": True,
        },
        "failure_policy": "retain first four calls; no retries or prompt repair",
        "image_sha256": sha(IMAGE),
        "prompt_sha256": {
            mode: sha(OUT / f"{mode}-prompt.txt") for mode in ("coordinate", "handle")
        },
        "sources": {name: sha(HERE / name) for name in sources},
        "docs": [
            "https://developers.openai.com/api/reference/cli/resources/responses/methods/retrieve",
            "https://developers.openai.com/api/reference/cli/resources/responses/methods/create",
        ],
        "scope": (
            "fixed archived action; no GUI input, causal latency, cost, served identity "
            "or general token claim"
        ),
    }
    (OUT / "plan.json").write_text(
        json.dumps(plan, indent=2) + "\n", encoding="utf-8", newline="\n"
    )
    print(json.dumps(plan, indent=2))


if __name__ == "__main__":
    main()
