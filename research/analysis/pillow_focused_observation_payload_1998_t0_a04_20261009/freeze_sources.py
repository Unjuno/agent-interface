#!/usr/bin/env python3
"""Create the immutable source hash map immediately before the A04 freeze commit."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
ALLOCATION = "LABEL-CONTROL-AMBIGUITY-1998-T0-A04-20261009"
BASE = "4758a95cd4a0aaa78e9cdc9d774f298d4ccf0e36"
PACKAGE_FILES = (
    "README.md", "PROTOCOL.md", "CONSTRUCTION_LOG.md", "ENVIRONMENT.json",
    "RUN_RECORD.template.json", "build_design.py", "design.json", "candidate.py",
    "auditor.py", "formal_runner.py", "test_construction.py", "freeze_sources.py",
)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    design = json.loads((HERE / "design.json").read_text(encoding="utf-8"))
    source_hashes = {}
    for name in PACKAGE_FILES:
        source_hashes["package/" + name] = digest(HERE / name)
    source_hashes["repo/research/observation_tiles/image_artifact.py"] = digest(
        REPO / "research/observation_tiles/image_artifact.py")
    for item in design["inputs"]:
        source_hashes["repo/" + item["path"]] = item["sha256"]
    for frame in design["frames"]:
        source_hashes["repo/" + frame["source_png_path"]] = frame["source_png_sha256"]
    freeze = {
        "allocation": ALLOCATION,
        "issue": 1998,
        "base_commit": BASE,
        "source_sha256": dict(sorted(source_hashes.items())),
        "pillow_version": "12.3.0",
        "python_version": "3.12.14",
        "compress_level": 6,
        "frame_count": len(design["frames"]),
        "case_count": design["expected_case_count"],
        "candidate_invocation_limit": 1,
        "auditor_invocation_limit": 1,
        "auditor_gate": "candidate exit 0 and complete structural 441-case JSON only",
        "retry_limit": 0,
        "network": "denied by macOS sandbox-exec profile",
        "container_started": False,
        "formal_claim_ceiling": "finite canonical serialized-byte accounting on fixed archived GUI frames; no ROI quality, model/token/latency, live GUI, task effect, or product claim",
    }
    (HERE / "FREEZE.json").write_text(json.dumps(freeze, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"source_entries": len(source_hashes), "frames": freeze["frame_count"],
                      "cases": freeze["case_count"], "freeze_sha256": digest(HERE / "FREEZE.json")}, sort_keys=True))


if __name__ == "__main__":
    main()
