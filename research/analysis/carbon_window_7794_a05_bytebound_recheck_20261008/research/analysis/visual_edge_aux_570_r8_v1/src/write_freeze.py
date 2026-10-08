#!/usr/bin/env python3
"""Create a pre-inference SHA freeze; never include outputs or freeze itself."""
import hashlib
import json
import sys
from pathlib import Path


root = Path(__file__).resolve().parents[1]
base = sys.argv[1]
main_recheck = sys.argv[2]
files = sorted([*(root / "src").glob("*.py"), *(root / "inputs").glob("*")])
checksums = {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in files if p.is_file()}
obj = {
    "format": "visual-edge-aux-570-r8-freeze-v1",
    "issue": 4885,
    "allocation": "visual-edge-aux-570-r8-20260927-01",
    "branch": "research/visual-edge-aux-570-r8-20260927",
    "additive_path": "research/analysis/visual_edge_aux_570_r8_v1/",
    "base_main": base,
    "pre_run_main_recheck": main_recheck,
    "disjoint_main_paths_since_base": ["research/integration/broker_path_confinement_4876_v3/", "research/system1/needle_role_c_support64_replication_4884_v1/"],
    "formal_calls": 24,
    "construction_calls": 4,
    "images": {
        "ollama": {"tag": "ollama/ollama:0.34.4", "id": "sha256:8262851b2846b87c649eddf3e76beb270c52f4d1bc94559f47efde16b0841551", "platform": "linux/amd64"},
        "helper": {"tag": "agent-interface-real-robustness-2912:cpu", "id": "sha256:c429dd941b668e2689a99ecc6b9717093647489e755cdbd8eb6e1594e4497aaf"},
    },
    "model": {"name": "qwen2.5vl:3b", "digest": "fb90415cde1ef08aa669ae74b082d49b158729b6db1ab183c941417d507e71a1", "quantization": "Q4_K_M"},
    "gpu": {"name": "NVIDIA GeForce RTX 3080 Laptop GPU", "vram_mib": 16384, "cuda_inference": True},
    "inputs": json.loads((root / "inputs" / "manifest.json").read_text(encoding="utf-8")),
    "sha256": checksums,
    "formal_status_at_freeze": "NOT_RUN",
    "retries_permitted": 0,
}
(root / "FREEZE.json").write_text(json.dumps(obj, sort_keys=True, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"sha256_entries": len(checksums), "manifest_sha256": checksums["inputs/manifest.json"]}, sort_keys=True))
