"""Independent checks over saved A04 old/new dispositions."""
import json
from pathlib import Path


data = json.loads(Path("RESULT.json").read_text(encoding="utf-8"))
assert data["schema"] == "scorer-feedback-attribution-a04-result-v1"
for name in ("missing", "null", "empty", "whitespace", "non_string"):
    case = data["cases"][name]
    assert case["a03"][0]["status"] == "SINGLE_POSSIBLE_INTENT_ENVELOPE"
    assert case["a03"][0]["intent_token"] is None
    assert case["a04"]["rejected"] is True
    assert case["a04"]["error"] == "positive scorer event kind must be a nonempty string"
valid = data["cases"]["valid_control"]
for version in ("a03", "a04"):
    row = valid[version][0]
    assert row["status"] == "SINGLE_POSSIBLE_INTENT_ENVELOPE"
    assert row["possible_intent_tokens"] == ["intent-a"]
    assert row["intent_token"] is None
print("A04 saved-result audit: PASS (5 malformed-kind rejections; valid control unchanged)")
