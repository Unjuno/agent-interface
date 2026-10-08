"""Build a deterministic schedule-only trace over the immutable #7418 corpus."""
import hashlib
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
FIXTURE_PATH = HERE.parent / "exception_preserving_skill_7418_t0_20261004" / "fixture.json"
FIXTURE_SHA256 = "1c8b74dfdd8ec7c5a5950133709ae95e40cc687edb12ac128d66f696c79e54fb"
CHECKPOINTS = (3, 6, 9, 12)
SCHEDULES = ("episodic_only", "per_episode", "batch_4", "terminal")


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def build(fixture):
    episodes = fixture["episodes"]
    ids = [episode["id"] for episode in episodes]
    episode_hashes = {episode["id"]: hashlib.sha256(canonical(episode)).hexdigest() for episode in episodes}
    dependencies = {
        "heldout-04": fixture["applicability_oracle"][0]["source_episode_ids"],
        "protected-heldout": fixture["applicability_oracle"][1]["source_episode_ids"],
        "contradictory": fixture["applicability_oracle"][2]["source_episode_ids"],
        "unrepresented": []
    }
    schedules = {}
    for name in SCHEDULES:
        if name == "episodic_only":
            update_prefixes = []
        elif name == "per_episode":
            update_prefixes = list(range(1, len(ids) + 1))
        elif name == "batch_4":
            update_prefixes = [4, 8, 12]
        else:
            update_prefixes = [12]
        updates = []
        for prefix in update_prefixes:
            prefix_ids = ids[:prefix]
            updates.append({"after_episode": prefix,
                            "episode_refs": [{"id": episode_id, "sha256": episode_hashes[episode_id]}
                                             for episode_id in prefix_ids]})
        visibility = []
        for checkpoint in CHECKPOINTS:
            eligible = [update for update in updates if update["after_episode"] <= checkpoint]
            available = ids[:checkpoint] if name == "episodic_only" else (
                eligible[-1]["episode_refs"] and [ref["id"] for ref in eligible[-1]["episode_refs"]]
                if eligible else [])
            latest = eligible[-1]["after_episode"] if eligible else None
            for query_id, required_ids in dependencies.items():
                retrieved = [episode_id for episode_id in required_ids if episode_id in available]
                if not required_ids:
                    evidence_state = "NO_SOURCE_REQUIRED"
                elif len(retrieved) == len(required_ids):
                    evidence_state = "FULL"
                elif retrieved:
                    evidence_state = "PARTIAL"
                else:
                    evidence_state = "NONE"
                visibility.append({"checkpoint": checkpoint, "latest_update_prefix": latest,
                                   "query_id": query_id, "available_episode_ids": list(available),
                                   "required_source_ids": list(required_ids),
                                   "retrieved_source_ids": retrieved, "evidence_state": evidence_state})
        schedules[name] = {"updates": updates, "query_visibility": visibility}
    return {"schema": "issue8406-schedule-harness-a01-v1",
            "fixture_sha256": hashlib.sha256(FIXTURE_PATH.read_bytes()).hexdigest(),
            "source_episode_ids": ids,
            "source_episode_sha256": episode_hashes,
            "query_dependencies": dependencies,
            "schedules": schedules}


def main():
    if len(sys.argv) != 2:
        raise SystemExit("usage: candidate.py RAW.json")
    raw_fixture = FIXTURE_PATH.read_bytes()
    if hashlib.sha256(raw_fixture).hexdigest() != FIXTURE_SHA256:
        raise SystemExit("parent fixture hash mismatch")
    fixture = json.loads(raw_fixture)
    payload = build(fixture)
    blob = (json.dumps(payload, sort_keys=True, indent=2, ensure_ascii=False) + "\n").encode()
    destination = Path(sys.argv[1])
    destination.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(destination, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "wb") as stream:
        stream.write(blob)
    print(json.dumps({"sha256": hashlib.sha256(blob).hexdigest(),
                      "source_episodes": len(payload["source_episode_ids"]),
                      "update_counts": {k: len(v["updates"]) for k, v in payload["schedules"].items()},
                      "visibility_rows": {k: len(v["query_visibility"]) for k, v in payload["schedules"].items()}}, sort_keys=True))


if __name__ == "__main__":
    main()
