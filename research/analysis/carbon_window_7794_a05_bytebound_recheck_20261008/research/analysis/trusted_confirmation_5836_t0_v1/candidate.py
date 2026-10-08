"""Finite broker policy candidates for Issue #5836; no external interfaces."""
import hashlib, json, sys
from pathlib import Path

POLICIES = ("SCREEN_TEXT", "BOUND_REPLAYABLE", "TRUSTED_SINGLE_USE")
def canon(value): return json.dumps(value,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode("utf-8")
def digest(value): return hashlib.sha256(canon(value)).hexdigest()
def display_digest(row): return digest({"principal":row["principal"],"effect":row["displayed_effect"]})
def actual_digest(row): return digest({"principal":row["principal"],"effect":row["effect"]})
def trusted_receipt(row, used, now, current_epoch):
    r=row.get("receipt")
    if not isinstance(r,dict) or r.get("decision")!="allow": return False,"NO_ALLOW_RECEIPT"
    if r.get("channel")!="trusted" or r.get("signature_valid") is not True: return False,"UNTRUSTED_CHANNEL"
    if r.get("principal")!=row.get("principal"): return False,"PRINCIPAL_MISMATCH"
    if r.get("request_digest")!=actual_digest(row): return False,"EFFECT_DIGEST_MISMATCH"
    if type(r.get("expires_at")) is not int or r["expires_at"]<=now: return False,"EXPIRED"
    if type(r.get("epoch")) is not int or r["epoch"]!=current_epoch: return False,"REVOKED_EPOCH"
    if r.get("nonce") in used: return False,"REPLAY"
    return True,"MATCHED_SINGLE_USE_RECEIPT"
def replayable_receipt(row, now, current_epoch):
    r=row.get("receipt")
    if not isinstance(r,dict) or r.get("decision")!="allow": return False,"NO_ALLOW_RECEIPT"
    if r.get("channel")!="trusted" or r.get("signature_valid") is not True: return False,"UNTRUSTED_CHANNEL"
    if r.get("principal")!=row.get("principal"): return False,"PRINCIPAL_MISMATCH"
    if r.get("request_digest")!=display_digest(row): return False,"EFFECT_DIGEST_MISMATCH"
    if type(r.get("expires_at")) is not int or r["expires_at"]<=now: return False,"EXPIRED"
    if type(r.get("epoch")) is not int or r["epoch"]!=current_epoch: return False,"REVOKED_EPOCH"
    return True,"BOUND_REPLAYABLE_RECEIPT"
def run(fixture):
    out=[]
    for policy in POLICIES:
        used=set()
        for row in fixture["requests"]:
            action=row["effect"].get("action")
            if action=="release-held-input": allowed,reason=True,"SAFETY_RELEASE_BYPASS"
            elif policy=="SCREEN_TEXT":
                allowed=any(v=="Approved" for v in row.get("approval_text",{}).values())
                reason="UNTRUSTED_TEXT_LAUNDERED" if allowed else "NO_APPROVAL_TEXT"
            elif policy=="BOUND_REPLAYABLE": allowed,reason=replayable_receipt(row,fixture["now"],fixture["current_epoch"])
            else: allowed,reason=trusted_receipt(row,used,fixture["now"],fixture["current_epoch"])
            if allowed and policy=="TRUSTED_SINGLE_USE" and action!="release-held-input": used.add(row["receipt"]["nonce"])
            if allowed: outcome="UNKNOWN" if row["executor"]=="lost_response" else "SUCCESS"; attempted=1
            else: outcome="NONE"; attempted=0
            out.append({"policy":policy,"request_id":row["id"],"request_digest":actual_digest(row),"decision":"ALLOW" if allowed else "DENY","reason":reason,"effect_attempts":attempted,"effect_outcome":outcome})
    return {"fixture_id":fixture["fixture_id"],"rows":out}
def main():
    src=json.loads(Path(sys.argv[1]).read_text(encoding="utf-8-sig"))
    for row in src["requests"]:
        if isinstance(row.get("receipt"),dict) and row["receipt"].get("request_digest")=="AUTO_DISPLAY": row["receipt"]["request_digest"]=display_digest(row)
    print(json.dumps(run(src),sort_keys=True,separators=(",",":")))
if __name__=="__main__": main()
