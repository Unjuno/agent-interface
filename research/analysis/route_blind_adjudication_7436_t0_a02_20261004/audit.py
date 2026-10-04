"""Independent raw-only audit of Issue #7436 T0 outputs and mutations."""

import copy
import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
CANARIES = (
    "ROUTE_ALPHA_EXPECTED_WINNER", "ROUTE_BETA_BASELINE",
    "CANDIDATE_FAST_ROUTE_ALPHA", "CANDIDATE_BASELINE_ROUTE_BETA",
    "BRANCH_GUARDED_ALPHA", "BRANCH_BASELINE_BETA", "PREDICTED_WINNER_ALPHA",
)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def reject_if_invalid(raw, expected, paths):
    assert raw["status"] == "CANDIDATE_COMPLETE"
    blinded = raw["blinded"]
    assert blinded["seed"] == 7436002
    assert len(blinded["packets"]) == 6
    assert len(set(blinded["order"])) == 6
    assert blinded["order"] == [p["episode_id"] for p in blinded["packets"]]
    assert blinded == expected
    packet_json = canonical(blinded)
    assert all(secret not in packet_json for secret in CANARIES)
    assert all("score" not in p for p in blinded["packets"])
    assert raw["precommit_reveal"] == "DENIED"
    assert raw["commitment"]["status"] == "committed"
    assert raw["commitment"]["count"] == 6
    assert raw["commitment"]["score_sha256"] == hashlib.sha256(canonical(raw["scores"]).encode()).hexdigest()
    ids = set(blinded["order"])
    assert {s["episode_id"] for s in raw["scores"]} == ids
    pointers = {p["episode_id"]: p["evidence_pointer"] for p in blinded["packets"]}
    assert all(s["evidence_pointer"] == pointers[s["episode_id"]] for s in raw["scores"])
    assert all(s["score"] in {"useful", "not_useful", "uncertain"} for s in raw["scores"])
    assert all(s["uncertainty"] in {"low", "medium", "high"} for s in raw["scores"])
    assert set(raw["postcommit_revealed_mapping"]) == ids
    assert len(paths) == 1 and paths[0].name == "candidate.json"
    assert all(secret not in str(paths[0]) for secret in CANARIES)


def main():
    fixture = json.loads((HERE / "fixture.json").read_text(encoding="utf-8"))
    raw = json.loads((HERE / "results" / "candidate.json").read_text(encoding="utf-8"))
    # Reconstruct expected packet bytes independently; do not import presenter.py.
    import random
    import uuid
    rng = random.Random(7436002)
    expected_packets = []
    for row in fixture["cases"]:
        episode_id = str(uuid.UUID(int=rng.getrandbits(128)))
        pointer = "evidence:" + hashlib.sha256(episode_id.encode()).hexdigest()[:16]
        expected_packets.append({"episode_id": episode_id, "stratum": row["stratum"],
                                 "evidence": row["evidence"], "rubric": fixture["rubric"],
                                 "evidence_pointer": pointer})
    rng.shuffle(expected_packets)
    expected = {"seed": 7436002, "order": [p["episode_id"] for p in expected_packets], "packets": expected_packets}
    reject_if_invalid(raw, expected, [HERE / "results" / "candidate.json"])

    # Verify reproducibility and seed sensitivity without importing candidate code.
    import random
    import uuid
    def order_for(seed):
        rr = random.Random(seed)
        ids = [str(uuid.UUID(int=rr.getrandbits(128))) for _ in fixture["cases"]]
        rr.shuffle(ids)
        return ids
    assert order_for(7436002) == raw["blinded"]["order"]
    assert order_for(7436003) != raw["blinded"]["order"]

    mutations = {}
    def mutated(name, action):
        trial = copy.deepcopy(raw)
        action(trial)
        mutations[name] = trial
    mutated("metadata_route_leak", lambda x: x["blinded"]["packets"][0].update(metadata={"route": CANARIES[0]}))
    mutated("filename_branch_leak", lambda x: x["blinded"].update(packet_filenames=["CANDIDATE_FAST_ROUTE_ALPHA.json"]))
    mutated("path_route_leak", lambda x: x["blinded"].update(packet_output_paths=["packets/ROUTE_ALPHA_EXPECTED_WINNER/packet.json"]))
    mutated("summary_winner_leak", lambda x: x["blinded"]["packets"][0].update(summary="PREDICTED_WINNER_ALPHA"))
    mutated("order_tamper", lambda x: x["blinded"]["order"].reverse())
    def change_score(x):
        current = x["scores"][0]["score"]
        x["scores"][0]["score"] = "uncertain" if current != "uncertain" else "useful"
    mutated("score_commit_tamper", change_score)
    mutated("evidence_pointer_tamper", lambda x: x["scores"][0].update(evidence_pointer="evidence:wrong"))
    mutated("missing_packet", lambda x: x["blinded"]["packets"].pop())
    effective = rejected = 0
    for name, trial in mutations.items():
        assert canonical(trial) != canonical(raw), name + " was a no-op"
        effective += 1
        try:
            reject_if_invalid(trial, expected, [HERE / "results" / "candidate.json"])
        except (AssertionError, KeyError, TypeError, ValueError):
            rejected += 1
    assert effective == rejected == 8
    report = {"status": "PASS_METHOD_SCOPED", "base_packet_check": "PASS",
              "seed_reproducible": True, "different_seed_changes_order": True,
              "precommit_reveal_denied": True, "mutations_effective": effective,
              "mutations_rejected": rejected, "scope": "synthetic packet/custody method only"}
    (HERE / "results" / "audit.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("PASS_METHOD_SCOPED packets=6 seed_reproducible=yes mutations=8/8 rejected=8/8")


if __name__ == "__main__":
    main()
