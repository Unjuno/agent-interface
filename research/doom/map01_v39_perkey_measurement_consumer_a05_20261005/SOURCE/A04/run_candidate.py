from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load frozen module {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> None:
    if (HERE / "RESULT.json").exists():
        raise SystemExit("STOP: A04 candidate output already exists")
    freeze_bytes = (HERE / "FREEZE.json").read_bytes()
    freeze = json.loads(freeze_bytes)
    for relative, digest in freeze["source_sha256"].items():
        actual = hashlib.sha256((HERE / relative).read_bytes()).hexdigest()
        if actual != digest:
            raise SystemExit(f"STOP: frozen source mismatch: {relative}")
    raw_bytes = (HERE / "SOURCE/BRIDGE_RAW_A01.json").read_bytes()
    if hashlib.sha256(raw_bytes).hexdigest() != freeze["input_sha256"]:
        raise SystemExit("STOP: frozen bridge raw mismatch")
    raw = json.loads(raw_bytes)
    projector = load_module("candidate_a04", HERE / "candidate.py")
    consumer = load_module("strict_consumer_a03", HERE / "SOURCE/consumer_a03.py")
    events = projector.project_cleanup(raw)
    candidate_result = consumer.reconstruct(events)
    out = {
        "run_id": freeze["run_id"], "status": "PENDING_INDEPENDENT_AUDIT",
        "input_sha256": hashlib.sha256(raw_bytes).hexdigest(),
        "freeze_sha256": hashlib.sha256(freeze_bytes).hexdigest(),
        "projected_events": events, "candidate": candidate_result,
        "authority_granted": False, "application_effect_observed": False,
        "candidate_invocations": 1,
        "new_os_input": False, "new_gui_or_game": False, "new_model_call": False,
        "scope": freeze["scope"],
    }
    (HERE / "RESULT.json").write_text(json.dumps(out, indent=2, sort_keys=True) + "\n",
                                      encoding="utf-8", newline="\n")
    print(json.dumps(out, sort_keys=True))


if __name__ == "__main__":
    main()
