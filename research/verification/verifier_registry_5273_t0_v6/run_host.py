"""Offline host runner for construction and audit only; it never dispatches."""

import copy
import hashlib
import json
from pathlib import Path

import candidate


ROOT = Path(__file__).resolve().parent
CORPUS = ROOT / "cases.json"


def run():
    raw = CORPUS.read_bytes()
    frozen = json.loads(raw)
    output = []
    for case in frozen["cases"]:
        payload = {key: copy.deepcopy(case[key])
                   for key in ("ir", "assignments", "registry", "resources")}
        output.append({"case_id": case["case_id"], "input": payload,
                       "decision": candidate.preflight(**payload)})
    return {"schema": "verifier_registry_5273_t0_v6.raw.v1",
            "corpus_sha256": hashlib.sha256(raw).hexdigest(),
            "invocation": "HOST_OFFLINE_CONSTRUCTION_ONLY",
            "dispatch_count": 0, "rows": output}


if __name__ == "__main__":
    path = ROOT / "raw_host.json"
    path.write_text(json.dumps(run(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote {path}")
