import hashlib, json
from pathlib import Path
root=Path(__file__).parent
def sha(name): return hashlib.sha256((root/name).read_bytes()).hexdigest()
candidate=json.loads((root/"candidate.stdout").read_text(encoding="utf-8-sig"))
params=json.loads((root/"schema"/"TurnInterruptParams.json").read_text(encoding="utf-8"))
provenance=json.loads((root/"provenance.json").read_text(encoding="utf-8"))
assert set(params["required"])=={"threadId","turnId"}
assert params["properties"]["threadId"]["type"]=="string"
assert params["properties"]["turnId"]["type"]=="string"
assert provenance["generated_full_schema_sha256"]=="4a6fc883c2e84c4721bfabd6756ca5bb6e99675a8938768d8bc9cc67ff984700"
assert candidate["cli_version"]=="codex-cli 0.160.0"
assert candidate["loopback_only"] is True and candidate["temporary_codex_home"] is True
assert candidate["api_credentials_cleared"] is True
assert candidate["initialize_reply"].get("result")
thread=candidate["thread_id"]; turn=candidate["turn_id"]
assert candidate["thread_reply"]["result"]["thread"]["id"]==thread
assert candidate["turn_start_reply"]["result"]["turn"]["id"]==turn
assert candidate["turn_start_reply"]["result"]["turn"]["status"]=="inProgress"
assert candidate["interrupt_reply"]=={"id":4,"result":{}}
assert candidate["mock_request_count"]==1 and candidate["mock_client_disconnected_before_release"] is True
assert candidate["mock_errors"]==[]
assert candidate["turn_completed"]["method"]=="turn/completed"
assert candidate["turn_completed"]["params"]["threadId"]==thread
ended=candidate["turn_completed"]["params"]["turn"]
assert ended["id"]==turn and ended["status"]=="interrupted"
assert [x["event"] for x in candidate["events"]]==["responses_request_received","client_disconnected_before_response"]
assert (root/"candidate.exit").read_text().strip()=="0"
assert (root/"candidate.stderr").read_bytes()==b""
summary={"audit":"PASS_RETAINED_TURN_INTERRUPT_CONSTRUCTION","checks":["installed CLI version","generated schema extraction required fields","temporary local isolation flags","API credential removal","actual returned thread and turn identity matching","interrupt RPC acceptance","one held mock request","disconnect before response release","interrupted terminal status","no mock errors","candidate exit/stderr"],"cli_version":candidate["cli_version"],"mock_request_count":candidate["mock_request_count"],"pending_http_disconnected_before_release":True,"rpc_accepted":True,"terminal_status":ended["status"],"candidate_exit":0,"full_generated_schema_sha256":provenance["generated_full_schema_sha256"],"published_schema_extract_sha256":sha("schema/TurnInterruptParams.json"),"candidate_sha256":sha("probe.py"),"stdout_sha256":sha("candidate.stdout"),"scope":"Local App Server + loopback mock only; no actual model/provider/game/GUI/input."}
print(json.dumps(summary,indent=2,sort_keys=True))
