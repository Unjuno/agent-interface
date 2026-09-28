from __future__ import annotations

import hashlib
import json
import platform
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    freeze_path = ROOT / "FREEZE.json"
    freeze_bytes = freeze_path.read_bytes()
    freeze = json.loads(freeze_bytes)
    errors = []
    sources = {name: sha(ROOT / name) for name in freeze["sources"]}
    if sources != freeze["sources"]:
        errors.append("source_hash_mismatch")
    references = {name: sha(REPO / path) for name, path in freeze["reference_sources"].items()}
    if references != freeze["reference_sources_sha256"]:
        errors.append("reference_hash_mismatch")
    inputs = {name: sha(REPO / path) for name, path in freeze["inputs"].items()}
    if inputs != freeze["inputs_sha256"]:
        errors.append("input_hash_mismatch")
    branch = subprocess.check_output(["git", "-C", str(REPO), "branch", "--show-current"], text=True).strip()
    head = subprocess.check_output(["git", "-C", str(REPO), "rev-parse", "HEAD"], text=True).strip()
    main = subprocess.check_output(["git", "-C", str(REPO), "rev-parse", "origin/main"], text=True).strip()
    if branch != freeze["expected_branch"]:
        errors.append("branch_mismatch")
    if main != freeze["base_commit"]:
        errors.append("current_main_mismatch")
    expected_source = str(REPO.resolve())
    for label in ("construction", "formal", "audit"):
        command = freeze[f"{label}_command"]
        source_token = f"source={expected_source},target=/repo,readonly"
        if source_token not in command:
            errors.append(f"{label}_host_bind_mismatch")
        if "--network none" not in command or "--read-only" not in command:
            errors.append(f"{label}_container_safety_flags")
    for relative in freeze["output_paths"].values():
        if (ROOT / relative).exists():
            errors.append(f"output_path_not_empty:{relative}")
    report = {
        "allocation": freeze["allocation"],
        "status": "PASS_STATIC_PREFLIGHT" if not errors else "STOP_STATIC_PREFLIGHT",
        "errors": errors,
        "base_commit": freeze["base_commit"],
        "branch": branch,
        "head_commit": head,
        "freeze_sha256": hashlib.sha256(freeze_bytes).hexdigest(),
        "source_hashes": sources,
        "reference_hashes": references,
        "input_hashes": inputs,
        "host_platform": platform.platform(),
        "host_machine": platform.machine(),
        "container_invocation": False,
    }
    print(json.dumps(report, sort_keys=True, separators=(",", ":")))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
