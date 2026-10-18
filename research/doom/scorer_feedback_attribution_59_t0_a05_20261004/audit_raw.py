from __future__ import annotations
import json
import os
from pathlib import Path
ROOT=Path(__file__).resolve().parent
raw=json.loads(Path(os.environ.get("A05_RAW_INPUT", str(ROOT/"out"/"candidate.raw.json"))).read_text(encoding="utf-8"))
expected={
 "01-KILL_COUNT_INCREASE": (True, "SINGLE_POSSIBLE_INTENT_ENVELOPE"),
 "02-MAP_EXIT": (True, "SINGLE_POSSIBLE_INTENT_ENVELOPE"),
 "03-FUTURE_SCORER_EVENT_V3": (False, None),
 "04-KILL_COUNT_INCREASEE": (False, None),
 "05-PLAYER_DEAD": (True, None),
}
assert raw["producer_vocab"] == ["KILL_COUNT_INCREASE","MAP_EXIT"]
checks=[]
for row in raw["cases"]:
    want_accept,want_status=expected[row["case"]]
    actual=row["a05"]["accepted"]
    assert actual is want_accept, (row["case"],actual,want_accept)
    if actual:
        statuses=[x["status"] for x in row["a05"]["rows"]]
        assert statuses == ([want_status] if want_status else [])
        if want_status:
            assert row["a05"]["rows"][0]["intent_token"] is None
            assert row["a05"]["rows"][0]["causal_attribution"]=="NOT_ESTABLISHED"
    if row["case"] in ("03-FUTURE_SCORER_EVENT_V3","04-KILL_COUNT_INCREASEE"):
        assert row["a04"]["accepted"] is True
        assert row["a04"]["rows"][0]["status"]=="SINGLE_POSSIBLE_INTENT_ENVELOPE"
        assert row["a04"]["rows"][0]["intent_token"] is None
    checks.append({"case":row["case"],"pass":True})
assert len(checks)==5
result={"schema":"scorer-feedback-attribution-a05-audit-v1","status":"PASS_RAW_AUDIT",
        "checks":checks,"cases_reconstructed":len(checks),"audit_uses_candidate_code":False,
        "claims":"method-scoped schema boundary only"}
Path(os.environ.get("A05_AUDIT_OUT", str(ROOT/"out"/"audit.raw.json"))).write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
print(json.dumps(result,indent=2,sort_keys=True))
