"""Independent stdlib audit of retained local zero-model preflight evidence."""
import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
ARTIFACTS = HERE / "artifacts"
RUN = ARTIFACTS / "preflight-zero-model-v4"
EXPECTED_WAD = "a8772e088847032510d97ba2312406a6998f21cbab44d4ff10696faa9c0ecd4b"
MAX_CLOCK_WIDTH_NS = 1_000_000_000


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    report = read_json(RUN / "report.json")
    assert report["iterations"] == 0
    assert report["planner_turns"] == 0
    assert report["model_wall_seconds"] == 0.0
    assert report["program_admissions"] == 0
    assert report["current_input_authority_true_at_decision_close"] == 0
    assert report["score"] == {
        "event": "post_control_score", "evaluator_score_withheld": True}

    journal = [json.loads(line) for line in
               (RUN / "planner-protocol.jsonl").read_text(encoding="utf-8").splitlines()]
    sent_methods = [row["message"].get("method") for row in journal
                    if row.get("direction") == "sent"]
    assert "thread/start" in sent_methods
    assert "turn/start" not in sent_methods
    assert "turn/steer" not in sent_methods

    runtime = RUN / "runtime"
    environment = read_json(runtime / "environment.json")
    assert environment["vizdoom"] == "1.3.0"
    assert environment["mode"] == "Mode.ASYNC_SPECTATOR"
    assert environment["map"] == "MAP01" and environment["skill"] == 1
    assert environment["ticrate"] == 35 and environment["loaded_fixture"] is None
    assert environment["iwad_sha256"] == EXPECTED_WAD

    events = [json.loads(line) for line in
              (runtime / "events.jsonl").read_text(encoding="utf-8").splitlines()]
    typed = [row for row in events if row.get("event") == "typed_observation"]
    assert len(typed) == 3
    assert len(report["typed_artifact_reconciliations"]) == 3
    assert report["typed_artifact_reconciled"] == 3
    assert report["typed_artifact_reconciliation_failures"] == 0
    assert all(row["matched"] is True and
               row["frame_rgb_sha256"] == row["artifact_rgb_sha256"]
               for row in report["typed_artifact_reconciliations"])

    probe = read_json(runtime / "submit-clock-zero-decision.json")
    assert probe["sample_count"] == 3 and probe["same_session"] is True
    assert probe["uncertainty_width_ns"] <= MAX_CLOCK_WIDTH_NS
    assert probe["input_authority"] == "observe_only" and probe["model_turns"] == 0
    assert probe["accepted"]["event"] == "accepted"
    assert probe["terminal"]["status"] == "completed"
    release = probe["terminal"]["release"]
    assert release["verified"] is True
    assert release["buttons_down"] == [] and release["keys_down"] == []
    assert probe["executor_accepted_ns"] >= probe["runtime_sent_ns"]
    assert probe["acceptance_minus_translated_send_ns"] == (
        probe["executor_accepted_ns"] - probe["runtime_sent_ns"])

    owner_events = read_json(runtime / "owner-events.json")
    assert len(owner_events) == 3
    assert all(row["verified"] is True and row["buttons_down"] == [] and
               row["keys_down"] == [] for row in owner_events)

    sources = read_json(runtime / "sources.json")
    assert len(sources) == 20
    for relative, expected in sources.items():
        path = REPO / "research" / relative
        assert path.is_file(), f"missing runtime source: {relative}"
        assert sha256(path) == expected, f"runtime source hash mismatch: {relative}"

    print("PASS_LOCAL_ZERO_MODEL_STARTUP_RELEASE_AUDIT")
    print("planner_turns=0 typed_observations=3 verified_empty_owner_releases=3")
    print(f"clock_uncertainty_ns={probe['uncertainty_width_ns']}")
    print(f"runtime_source_hashes={len(sources)}/{len(sources)}")


if __name__ == "__main__":
    main()
