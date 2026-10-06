#!/usr/bin/env python3
"""Audit the one-shot CLI outcome without exposing local raw logs."""
from pathlib import Path
import hashlib
import json
import subprocess

ROOT = Path(__file__).resolve().parent
PRIVATE = ROOT / "private"
expected_inputs = {
    "repair-01.png": "8ff56201d9ce921189b054f842ea2a0b55cb5a0b851e104ac041d0911d7ed919",
    "repair-02.png": "8ff56201d9ce921189b054f842ea2a0b55cb5a0b851e104ac041d0911d7ed919",
    "repair-03.png": "8ff56201d9ce921189b054f842ea2a0b55cb5a0b851e104ac041d0911d7ed919",
    "repair-04.png": "11a6fcba5a2ab6357e0385648a44f1b7efabbfd2c0c6c46e7db7b5a496873fd0",
}
sha = lambda b: hashlib.sha256(b).hexdigest()
for name, digest in expected_inputs.items():
    assert sha((ROOT / "input" / name).read_bytes()) == digest
assert sha((ROOT / "PROMPT.txt").read_bytes()) == "880fe52cefd86e7c585b371e8ad6277a426a37b4cfa87bc990e08535f27a3134"

stdout = (PRIVATE / "raw.stdout.jsonl").read_bytes()
stderr = (PRIVATE / "raw.stderr").read_bytes()
receipt = json.loads((PRIVATE / "local_receipt.json").read_text())
assert (PRIVATE / "G23_ATTEMPTED.lock").exists()
assert receipt["exit_code"] == 1 and not stdout
assert b"No prompt provided via stdin." in stderr
assert sha(stdout) == receipt["stdout_sha256"]
assert sha(stderr) == receipt["stderr_sha256"]

version = subprocess.run(["codex", "--version"], capture_output=True, text=True, check=True).stdout.strip()
result = {
    "run_id": "CALC-VLM-PSM-REPAIR-3311-20261004-G23",
    "status": "STOP_CLI_PROMPT_NOT_DELIVERED",
    "candidate_commit": "5799d8e42fc10628253c76a246c99496e3d7eeda",
    "cli_version": version,
    "requested_model": "gpt-6.1-sol",
    "requested_reasoning_effort": "medium",
    "cli_exit_code": 1,
    "completed_assistant_final_responses": 0,
    "inference_completed": False,
    "sanitized_diagnostic": "No prompt provided via stdin.",
    "prompt_sha256": "880fe52cefd86e7c585b371e8ad6277a426a37b4cfa87bc990e08535f27a3134",
    "inputs_sha256": expected_inputs,
    "stdout_sha256": sha(stdout),
    "stderr_sha256": sha(stderr),
    "stdout_bytes": len(stdout),
    "stderr_bytes": len(stderr),
    "raw_logs_retained_locally": True,
    "retry_performed": False,
    "audit": "PASS: frozen inputs match; one attempt marker and raw hashes agree; CLI stopped before producing any response.",
    "claim_scope": "No model recognition result. Inference was not completed; no accuracy or desktop-control claim is supported.",
}
(ROOT / "RESULT.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
print("PASS: one-shot STOP receipt and frozen input hashes verified")
