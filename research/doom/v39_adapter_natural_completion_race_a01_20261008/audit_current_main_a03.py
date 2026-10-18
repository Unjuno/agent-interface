import hashlib
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent
freeze = json.loads((ROOT / "FREEZE_A03.json").read_text(encoding="utf-8"))
raw = (ROOT / "RESULT_A03.json").read_bytes()
expected = (ROOT / "RESULT_A03.sha256").read_text(encoding="ascii").split()[0]
assert hashlib.sha256(raw).hexdigest() == expected
result = json.loads(raw)
assert result["main"] == freeze["main_commit"]
assert result["source_blobs"] == {row["path"]: row["git_blob"] for row in freeze["sources"]}
assert result["status"] == "PASS_EXACT_READER_ROUTES_COMPLETION_BEFORE_INTERRUPT_REPLY"
events = [row["event"] for row in result["events"]]
assert events.index("turn_completion_consumed") < events.index("interrupt_response_injected")
assert result["turn_result"]["answer_eligible"] is False and result["turn_result"]["answer"] is None
assert result["helper_terminal"]["release"] == {"verified": True, "keys_down": [], "buttons_down": []}
print("PASS_CURRENT_MAIN_A03_AUDIT", freeze["main_commit"], len(freeze["sources"]), expected)
