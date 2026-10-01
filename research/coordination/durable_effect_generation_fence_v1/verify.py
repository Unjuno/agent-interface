import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).parent


def load(name):
    return json.loads((ROOT / name).read_text())


def fp(payload):
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


result = load("result.json")
baseline = load("receiver_baseline.json")
fenced = load("receiver_fenced.json")
old = load("request_old.json")
current = load("request_current.json")
replay = load("request_replay.json")
conflict = load("request_conflict.json")

assert result["decision"] == "PASS_DURABLE_EFFECT_GENERATION_FENCE_SCOPED"
assert baseline["policy"] == "idempotency_only"
assert baseline["accepted_generation"] == 2
assert baseline["effect_count"] == 2
assert [e["generation"] for e in baseline["effects"]] == [1, 2]
assert baseline["receipts"]["cmd-old-010"]["fingerprint"] == fp(old["payload"])
assert baseline["receipts"]["cmd-new-010"]["fingerprint"] == fp(current["payload"])

assert fenced["policy"] == "generation_fenced"
assert fenced["accepted_generation"] == 2
assert fenced["effect_count"] == 1
assert len(fenced["effects"]) == 1
assert fenced["effects"][0]["request_id"] == "cmd-new-010"
assert fenced["effects"][0]["generation"] == 2
assert fenced["receipts"]["cmd-new-010"]["fingerprint"] == fp(current["payload"])
assert old["generation"] != fenced["accepted_generation"]
assert replay == current
assert fp(conflict["payload"]) != fp(current["payload"])
assert conflict["request_id"] == current["request_id"]
assert result["fenced"]["old_generation_write"] is False
assert result["fenced"]["exact_replay_write"] is False
assert result["fenced"]["same_id_changed_payload_write"] is False
assert result["fenced"]["stale_generation_effects"] == 0
print("PASS")
