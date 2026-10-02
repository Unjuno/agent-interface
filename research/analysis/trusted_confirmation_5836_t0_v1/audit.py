"""Independent raw-only oracle for the frozen trusted-confirmation fixture."""
import copy, hashlib, json, sys
from pathlib import Path

POLICY_ORDER=("SCREEN_TEXT","BOUND_REPLAYABLE","TRUSTED_SINGLE_USE")
def canonical(obj): return json.dumps(obj,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode("utf-8")
def sha(obj): return hashlib.sha256(canonical(obj)).hexdigest()
def materialize(f):
    f=copy.deepcopy(f)
    for r in f["requests"]:
        if isinstance(r.get("receipt"),dict) and r["receipt"].get("request_digest")=="AUTO_DISPLAY":
            r["receipt"]["request_digest"]=sha({"principal":r["principal"],"effect":r["displayed_effect"]})
    return f

def oracle(f):
    f=materialize(f); rows=[]
    for policy in POLICY_ORDER:
        consumed=set()
        for r in f["requests"]:
            receipt=r.get("receipt"); effect=r["effect"]; display={"principal":r["principal"],"effect":r["displayed_effect"]}; current={"principal":r["principal"],"effect":effect}
            if effect.get("action")=="release-held-input": allow,why=True,"SAFETY_RELEASE_BYPASS"
            elif policy=="SCREEN_TEXT":
                allow=any(value=="Approved" for value in r.get("approval_text",{}).values())
                why="UNTRUSTED_TEXT_LAUNDERED" if allow else "NO_APPROVAL_TEXT"
            else:
                basics=(isinstance(receipt,dict) and receipt.get("decision")=="allow" and receipt.get("channel")=="trusted" and receipt.get("signature_valid") is True and receipt.get("principal")==r["principal"] and type(receipt.get("expires_at")) is int and receipt["expires_at"]>f["now"] and type(receipt.get("epoch")) is int and receipt["epoch"]==f["current_epoch"])
                bound=isinstance(receipt,dict) and receipt.get("request_digest")==sha(display)
                exact=isinstance(receipt,dict) and receipt.get("request_digest")==sha(current)
                unused=basics and receipt.get("nonce") not in consumed
                allow=bool(basics and (bound if policy=="BOUND_REPLAYABLE" else exact and unused))
                if not isinstance(receipt,dict) or receipt.get("decision")!="allow": why="NO_ALLOW_RECEIPT"
                elif receipt.get("channel")!="trusted" or receipt.get("signature_valid") is not True: why="UNTRUSTED_CHANNEL"
                elif receipt.get("principal")!=r["principal"]: why="PRINCIPAL_MISMATCH"
                elif policy=="BOUND_REPLAYABLE" and not bound: why="EFFECT_DIGEST_MISMATCH"
                elif policy=="TRUSTED_SINGLE_USE" and not exact: why="EFFECT_DIGEST_MISMATCH"
                elif type(receipt.get("expires_at")) is not int or receipt["expires_at"]<=f["now"]: why="EXPIRED"
                elif type(receipt.get("epoch")) is not int or receipt["epoch"]!=f["current_epoch"]: why="REVOKED_EPOCH"
                elif policy=="TRUSTED_SINGLE_USE" and receipt.get("nonce") in consumed: why="REPLAY"
                elif policy=="BOUND_REPLAYABLE" and bound: why="BOUND_REPLAYABLE_RECEIPT"
                else: why="MATCHED_SINGLE_USE_RECEIPT"
            if allow and policy=="TRUSTED_SINGLE_USE" and effect.get("action")!="release-held-input": consumed.add(receipt["nonce"])
            attempted=1 if allow else 0
            outcome=("UNKNOWN" if r["executor"]=="lost_response" else "SUCCESS") if allow else "NONE"
            rows.append({"policy":policy,"request_id":r["id"],"request_digest":sha(current),"decision":"ALLOW" if allow else "DENY","reason":why,"effect_attempts":attempted,"effect_outcome":outcome})
    return {"fixture_id":f["fixture_id"],"rows":rows}

def check(f,raw):
    errors=[]
    expected=oracle(f)
    if raw.get("fixture_id")!=expected["fixture_id"]: errors.append("FIXTURE_ID")
    got=raw.get("rows")
    if not isinstance(got,list) or len(got)!=len(expected["rows"]): return errors+["ROW_COUNT"]
    bykey={(x.get("policy"),x.get("request_id")):x for x in got}
    if len(bykey)!=len(got): errors.append("DUPLICATE_ROW")
    for exp in expected["rows"]:
        obs=bykey.get((exp["policy"],exp["request_id"]))
        if obs!=exp: errors.append("ROW_MISMATCH:"+exp["policy"]+":"+exp["request_id"])
    return errors

def mutation_controls(f,raw):
    controls=[]
    def mutate(name, selector, change):
        m=copy.deepcopy(raw); row=next(x for x in m["rows"] if x["policy"]==selector[0] and x["request_id"]==selector[1]); change(row); detected=bool(check(f,m)); controls.append({"name":name,"detected":detected})
    mutate("drop-forged-baseline-effect",("SCREEN_TEXT","page-forgery"),lambda r:r.update(effect_attempts=0,decision="DENY",effect_outcome="NONE"))
    mutate("allow-target-swap",("TRUSTED_SINGLE_USE","target-swap"),lambda r:r.update(effect_attempts=1,decision="ALLOW",effect_outcome="SUCCESS"))
    mutate("replay-consumption",("TRUSTED_SINGLE_USE","replay-second"),lambda r:r.update(effect_attempts=1,decision="ALLOW",effect_outcome="SUCCESS"))
    mutate("principal-binding",("TRUSTED_SINGLE_USE","principal-mismatch"),lambda r:r.update(effect_attempts=1,decision="ALLOW",effect_outcome="SUCCESS"))
    mutate("lost-response-unknown",("TRUSTED_SINGLE_USE","lost-response-first"),lambda r:r.update(effect_outcome="SUCCESS"))
    mutate("release-bypass",("TRUSTED_SINGLE_USE","safe-release"),lambda r:r.update(effect_attempts=0,decision="DENY",effect_outcome="NONE"))
    return controls

def main():
    f=json.loads(Path(sys.argv[1]).read_text(encoding="utf-8-sig")); raw=json.loads(Path(sys.argv[2]).read_text(encoding="utf-8-sig")); errors=check(f,raw); controls=mutation_controls(f,raw)
    trusted=[x for x in raw["rows"] if x["policy"]=="TRUSTED_SINGLE_USE"]
    baseline_screen=[x for x in raw["rows"] if x["policy"]=="SCREEN_TEXT"]
    baseline_replay=[x for x in raw["rows"] if x["policy"]=="BOUND_REPLAYABLE"]
    if any(not c["detected"] for c in controls): errors.append("MUTATION_CONTROL")
    false_c=[x["request_id"] for x in trusted if next(r for r in f["requests"] if r["id"]==x["request_id"])["truth"]=="DENY" and x["effect_attempts"]]
    if false_c: errors.append("UNAUTHORIZED_EFFECT")
    if not all(next(x for x in baseline_screen if x["request_id"]==n)["effect_attempts"]==1 for n in ("page-forgery","tool-forgery")): errors.append("SCREEN_BASELINE_CONTROL")
    if not next(x for x in baseline_replay if x["request_id"]=="target-swap")["effect_attempts"]: errors.append("TARGET_SWAP_BASELINE_CONTROL")
    if not next(x for x in baseline_replay if x["request_id"]=="replay-second")["effect_attempts"]: errors.append("REPLAY_BASELINE_CONTROL")
    result={"status":"PASS_METHOD_SCOPED" if not errors else "FAIL_RAW_AUDIT","errors":errors,"rows":len(raw.get("rows",[])),"trusted_single_use_unauthorized_effects":len(false_c),"mutation_controls":controls,"candidate_comparison_controls":{"screen_text_forgery_effects":2,"bound_receipt_target_swap_effect":1,"bound_receipt_replay_effect":1},"formal_ui_authenticity_claim":False}
    print(json.dumps(result,sort_keys=True,separators=(",",":"))); return 0 if not errors else 1
if __name__=="__main__": raise SystemExit(main())

