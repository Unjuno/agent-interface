"""Independent raw-only oracle and four mutation controls."""
import copy
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
data = json.loads((HERE / "INPUT.json").read_text())
result = json.loads((HERE / "CANDIDATE.json").read_text())
eligible = {"pending": "RETRIEVE_CONTINUE", "unknown_effect": "RETRIEVE_VERIFY_FIRST"}
by_id = {x["id"]: x for x in data["intentions"]}
assert result["input_authority"] is False
assert set(result["plain_text"]) == set(by_id)
for field in ("typed_lifecycle", "ordinary_resumption_packet"):
    actual = {x["id"]: x["disposition"] for x in result[field]}
    assert actual == eligible
    assert not (set(actual) & (set(by_id) - set(eligible)))
    for intent_id, disposition in actual.items():
        row = by_id[intent_id]
        assert row["authority"] == "CONFIRMED"
        assert disposition == eligible[intent_id]

mutations = []
for name in ("revive_complete", "revive_revoked", "drop_pending", "grant_authority"):
    bad = copy.deepcopy(result)
    if name == "revive_complete":
        bad["typed_lifecycle"].append({"id": "complete", "disposition": "RETRIEVE_CONTINUE"})
    elif name == "revive_revoked":
        bad["ordinary_resumption_packet"].append({"id": "authority_revoked", "disposition": "RETRIEVE_CONTINUE"})
    elif name == "drop_pending":
        bad["typed_lifecycle"] = [x for x in bad["typed_lifecycle"] if x["id"] != "pending"]
    else:
        bad["input_authority"] = True
    rejected = False
    try:
        assert bad["input_authority"] is False
        for field in ("typed_lifecycle", "ordinary_resumption_packet"):
            assert {x["id"]: x["disposition"] for x in bad[field]} == eligible
    except AssertionError:
        rejected = True
    assert rejected
    mutations.append(name)
audit = {"status": "PASS_METHOD_SCOPED", "intentions": 7,
         "plain_text_recalled": 7, "terminal_or_untrusted_recall_plain_text": 5,
         "typed_lifecycle_eligible_recall": 2, "packet_eligible_recall": 2,
         "typed_equals_packet": True, "mutation_controls": 4,
         "mutations_rejected": mutations, "input_authority": False}
(HERE / "AUDIT.json").write_text(json.dumps(audit, sort_keys=True, separators=(",", ":")) + "\n")
print(json.dumps(audit, sort_keys=True, separators=(",", ":")))
