"""Audit the fresh v3 negative finish control and fixed-Astra success path."""
import hashlib
import json
from pathlib import Path

from PIL import Image

import audit_openttd_matched_v2 as shared
from append_checkpoint_v1 import load
from received_continuation_v1 import advance, start

HERE = Path(__file__).resolve().parent
BASE = HERE / "results/timing-envelope-openttd-matched-03"
shared.BASE = BASE


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit_negative():
    root = BASE / "negative-control"
    control = BASE / "negative-control-supervisor"
    runtime = root / "runtime"
    for directory in (root, control):
        for name, digest in read(directory / "plan.json")["sources"].items():
            shared.source_with_hash(HERE / name, digest)
    manifest = read(runtime / "manifest.json")
    for name, digest in manifest["sources"].items():
        shared.source_with_hash(HERE.parent / name, digest)

    endpoint = read(root / "endpoint.json")
    events = [json.loads(line) for line in (runtime / "events.jsonl").read_text().splitlines()]
    state = start(endpoint["socket"])

    def replay(exchange):
        nonlocal state
        request, reply = exchange["request"], exchange["reply"]
        assert request["after"] == state["cursor"]
        assert reply["records"] == events[request["after"]:reply["cursor"]]
        state = advance(state, endpoint["socket"], request["after"], reply)
        expected = exchange["state"]["continuation"] if "state" in exchange else exchange["continuation"]
        assert state == expected

    initial = read(root / "initial.json")
    replay(initial)
    assert load(root / "journal.jsonl")["continuation"] == initial["continuation"]
    finish = read(root / "finish.json")
    replay(finish)
    assert not (root / "calls.json").exists()
    assert not list(root.glob("model-*")) and not list(root.glob("applied-*.json"))

    failure = read(root / "failure-evaluation.json")
    evaluation = next(row for row in finish["reply"]["records"] if row["event"] == "independent_evaluation")
    assert failure["evaluation"] == evaluation and evaluation["success"] is False
    assert failure["failure_mode"] == "visual_verify_false_positive"
    assert failure["journal_calls"] == 0 and failure["proposals_executed"] == 0
    result = read(control / "result.json")
    assert result["success"] is True and result["failure_outcome"] == failure

    observations = [row for row in events if row.get("event") == "observation"]
    artifacts = sorted(runtime.glob("*.ait"))
    assert len(observations) == len(artifacts)
    decoder = shared.Decoder("live-control")
    for event, artifact in zip(observations, artifacts):
        decoded = decoder.accept(artifact.read_bytes())
        with Image.open(runtime / Path(event["image"]).name) as image:
            assert (image.width, image.height, image.mode, image.tobytes()) == (
                decoded.width, decoded.height, decoded.mode, decoded.pixels
            )
    assert not Path(endpoint["socket"]).exists() and not Path(endpoint["cancel_socket"]).exists()
    return {
        "audit_passed": True,
        "model_calls": 0,
        "durable_input_calls": 0,
        "runtime_exact_frames": len(observations),
        "failure_mode": failure["failure_mode"],
        "independent_checks": evaluation["checks"],
        "save_sha256": manifest["save_sha256"],
        "task": read(root / "ready.json")["task"],
        "supervisor_wall_ms": result["supervisor_wall_ms"],
    }


def main():
    prereg = read(BASE / "preregistration.json")
    assert prereg["status"] == "PREREGISTERED_BEFORE_EXECUTION"
    assert prereg["execution_order"] == ["negative-control", "fixed-astra"]
    for name, digest in prereg["sources"].items():
        shared.source_with_hash(HERE / name, digest)
    negative = audit_negative()
    positive = shared.audit_arm("fixed-astra")
    assert positive["hard_success"] is True
    assert negative["save_sha256"] == positive["save_sha256"]
    assert negative["task"] == positive["task"]
    report = {
        "audit_passed": True,
        "preregistered": True,
        "negative_control": negative,
        "fixed_astra": positive,
        "scope": "fresh v3 negative finish integration and one fresh fixed-Astra episode; no population or human-speed claim",
        "audit_sha256": sha(Path(__file__)),
        "shared_audit_dependency_sha256": sha(HERE / "audit_openttd_matched_v2.py"),
    }
    (BASE / "audit.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
