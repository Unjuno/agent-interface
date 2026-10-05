"""Synthetic endpoint-scoped packet presenter for Issue #7436 T0."""

import copy
import hashlib
import json
import random
import uuid


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def make_packets(fixture, seed):
    rng = random.Random(seed)
    packets = []
    escrow = {}
    for row in fixture["cases"]:
        episode_id = str(uuid.UUID(int=rng.getrandbits(128)))
        pointer = "evidence:" + hashlib.sha256(episode_id.encode()).hexdigest()[:16]
        packets.append({
            "episode_id": episode_id,
            "stratum": row["stratum"],
            "evidence": copy.deepcopy(row["evidence"]),
            "rubric": copy.deepcopy(fixture["rubric"]),
            "evidence_pointer": pointer,
        })
        escrow[episode_id] = {
            "source_id": row["source_id"],
            "route": row["route"],
            "artifact_path": row["artifact_path"],
            "filename": row["filename"],
            "metadata": copy.deepcopy(row["metadata"]),
        }
    rng.shuffle(packets)
    return {"seed": seed, "order": [p["episode_id"] for p in packets], "packets": packets}, escrow


def synthetic_scores(blinded):
    """A deterministic protocol probe, not human or empirical adjudication."""
    scores = []
    for packet in blinded["packets"]:
        event = packet["evidence"]["event"]
        score = "useful" if event == "cue_visible" else "not_useful" if event == "collateral_delta" else "uncertain"
        scores.append({
            "episode_id": packet["episode_id"],
            "score": score,
            "uncertainty": "low" if score != "uncertain" else "high",
            "evidence_pointer": packet["evidence_pointer"],
        })
    return scores


class Custodian:
    def __init__(self, escrow):
        self._escrow = copy.deepcopy(escrow)
        self._commit = None

    def reveal(self, scores=None):
        if self._commit is None or scores is None:
            raise PermissionError("route map is escrowed until score commitment")
        digest = hashlib.sha256(canonical(scores).encode()).hexdigest()
        if digest != self._commit:
            raise ValueError("score commitment mismatch")
        return copy.deepcopy(self._escrow)

    def commit_scores(self, scores, packet_ids, packet_pointers):
        if self._commit is not None:
            raise ValueError("scores already committed")
        if [row.get("episode_id") for row in scores] != packet_ids:
            raise ValueError("score order or episode coverage mismatch")
        if len(set(packet_ids)) != len(packet_ids):
            raise ValueError("duplicate packet id")
        if any(set(row) != {"episode_id", "score", "uncertainty", "evidence_pointer"} for row in scores):
            raise ValueError("score schema mismatch")
        if any(row.get("score") not in {"useful", "not_useful", "uncertain"} for row in scores):
            raise ValueError("score outside frozen rubric")
        if any(row.get("uncertainty") not in {"low", "medium", "high"} for row in scores):
            raise ValueError("uncertainty outside frozen rubric")
        if any(row.get("evidence_pointer") != packet_pointers.get(row.get("episode_id")) for row in scores):
            raise ValueError("score evidence pointer mismatch")
        self._commit = hashlib.sha256(canonical(scores).encode()).hexdigest()
        return {"status": "committed", "score_sha256": self._commit, "count": len(scores)}
