from __future__ import annotations
import hashlib,json,os
from pathlib import Path
FROZEN_SHA256="9506457a371565b489b5e1b9f7313c05d3f13a28bd5448b4b2944211ee4f313e"
LABELS=["01-KILL_COUNT_INCREASE","02-MAP_EXIT","03-FUTURE_SCORER_EVENT_V3","04-KILL_COUNT_INCREASEE","05-PLAYER_DEAD"]
KINDS=["KILL_COUNT_INCREASE","MAP_EXIT","FUTURE_SCORER_EVENT_V3","KILL_COUNT_INCREASEE","PLAYER_DEAD"]
def exact(actual,expected):
    if type(actual) is not type(expected): return False
    if type(expected) is dict: return actual.keys()==expected.keys() and all(exact(actual[k],expected[k]) for k in expected)
    if type(expected) is list: return len(actual)==len(expected) and all(exact(a,e) for a,e in zip(actual,expected))
    return actual==expected
def row(i,kind):
    return {"event_sequence":i,"kind":kind,"detection_interval_ns":[100,200],"status":"SINGLE_POSSIBLE_INTENT_ENVELOPE","reason":"one_verified_envelope_spans_detection_interval","possible_intent_tokens":["intent-a"],"intent_token":None,"causal_attribution":"NOT_ESTABLISHED"}
def independently_validate(doc):
    if not isinstance(doc,dict) or doc.get("schema")!="scorer-feedback-attribution-a05-raw-v1": raise ValueError("unexpected raw schema")
    cases=[]
    for i,(label,kind) in enumerate(zip(LABELS,KINDS),1):
        positive=i<5; polarity="positive" if positive else "negative"; useful=positive
        event={"schema":"independent-progress-event-v2","event_sequence":i,"observed_ns":200,"kind":kind,"polarity":polarity,"useful":useful,"controller_visible":False}
        if positive:
            envelope=[row(i,kind)]; a04={"accepted":True,"rows":envelope}
            a05={"accepted":True,"rows":envelope} if i<=2 else {"accepted":False,"error":"positive useful event kind is outside v2 producer vocabulary"}
        else:
            a04={"accepted":True,"rows":[]}; a05={"accepted":True,"rows":[]}
        cases.append({"case":label,"event":event,"a04":a04,"a05":a05})
    expected={"schema":"scorer-feedback-attribution-a05-raw-v1","producer_vocab":["KILL_COUNT_INCREASE","MAP_EXIT"],"producer_negative_vocab":["DEATH_COUNT_INCREASE","PLAYER_DEAD","EPISODE_FINISHED_NO_EXIT"],"cases":cases,"formal_live_allocation":False,"scope":"synthetic schema-construction; no task/game/model/input"}
    if not exact(doc,expected): raise ValueError("independent exact-set or event/disposition validation failed")
    return len(cases)
def main():
    path=Path(os.environ.get("A06_RAW_INPUT","/input/a05-candidate.raw.json")); raw=path.read_bytes(); digest=hashlib.sha256(raw).hexdigest()
    if digest!=FROZEN_SHA256: raise ValueError(f"frozen input hash mismatch: {digest}")
    count=independently_validate(json.loads(raw.decode("utf-8")))
    result={"schema":"scorer-feedback-attribution-a06-independent-audit-v1","status":"PASS_RAW_AUDIT_V2","input_sha256":digest,"cases_reconstructed":count,"candidate_or_candidate_auditor_imported":False,"tamper_tests_imported":False,"scope":"independent reconstruction of retained synthetic bytes only"}
    out=Path(os.environ.get("A06_AUDIT_OUT","/out/audit.raw.json")); out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8"); print(json.dumps(result,indent=2,sort_keys=True))
if __name__=="__main__": main()
