"""Prepare immutable candidate-visible inputs; this script never runs WSLc."""
import argparse
import copy
import hashlib
import json
import shutil
from pathlib import Path

from independent_audit import audit_package, read_json


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--package", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--source-main-sha", required=True)
    args = parser.parse_args()
    result = audit_package(args.package)
    if result["errors"]:
        raise SystemExit("parent audit failed: " + repr(result["errors"]))
    root = args.output.resolve()
    root.mkdir(parents=True, exist_ok=False)
    inputs = root / "input"
    inputs.mkdir()
    for name in ("candidate.py", "contract.json"):
        shutil.copyfile(args.package / "candidate_input" / name, inputs / name)
    fixture = read_json(args.package / "candidate_input/candidate_fixture.json")
    changed = copy.deepcopy(fixture)
    for index, row in enumerate(changed["rows"], 1):
        row["id"] = f"case_{index:02d}"
    (inputs / "candidate_fixture.json").write_text(
        json.dumps(changed, separators=(",", ":")) + "\n", encoding="utf-8")
    hashes = {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in sorted(inputs.iterdir())}
    proposal = {
        "state": "NOT_RUN_PENDING_WSLC_DISPOSITION", "candidate_invocations": 0,
        "source_main_sha": args.source_main_sha,
        "parent_manifest_sha256": result["parent_manifest_sha256"],
        "input_sha256": hashes, "changed_fields": ["rows[*].id"],
        "image_reference": "python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f",
        "cached_image_id_observed": "sha256:9e87977b867847e186d066f531ef783b006d582a985c341c269446088d90f2c4",
        "cached_platform_observed": "linux/amd64",
        "command": [
            "wslc", "run", "--rm", "--pull", "never", "--network", "none",
            "--cpus", "1", "--memory", "128M", "--user", "65534:65534",
            "--mount", f"type=bind,source={inputs},target=/candidate,readonly",
            "python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f",
            "python", "-B", "/candidate/candidate.py",
            "/candidate/candidate_fixture.json", "/candidate/contract.json",
        ],
        "output_method": "Host capture_run.py saves stdout/stderr to a new output directory.",
        "memory_enforcement_claimed": False, "retries": 0,
    }
    (root / "PROPOSAL.json").write_text(json.dumps(proposal, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"state": proposal["state"], "input_files": len(hashes),
                      "candidate_invocations": 0, "output": str(root)}))


if __name__ == "__main__":
    main()

