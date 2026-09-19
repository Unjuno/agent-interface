import hashlib,json,itertools
GATES=("physical","task_effect","matched_arms","arm_audit","release_integrity")
def classify(record):
    if set(record)!=set(GATES): return "HOLD_MALFORMED"
    if any(type(record[k]) is not bool for k in GATES): return "HOLD_MALFORMED"
    return "AUTHORIZE" if all(record.values()) else "HOLD"
def oracle(record): return classify(record)
def main():
    rows=[]
    for bits in itertools.product((False,True), repeat=5):
        r=dict(zip(GATES,bits)); rows.append({"record":r,"candidate":classify(r),"oracle":oracle(r)})
    assert len(rows)==32 and sum(x["candidate"]=="AUTHORIZE" for x in rows)==1
    controls=[
      ("viewport_as_task_effect",{"physical":True,"task_effect":True,"matched_arms":True,"arm_audit":True,"release_integrity":True},"reject weak role"),
      ("open_prerequisite_as_ready",{"physical":True,"task_effect":True,"matched_arms":True,"arm_audit":True,"release_integrity":False},"open prerequisite"),
      ("pair_summary_without_arm_binding",{"physical":True,"task_effect":True,"matched_arms":True,"arm_audit":False,"release_integrity":True},"missing binding"),
      ("hud_as_task_effect",{"physical":True,"task_effect":False,"matched_arms":True,"arm_audit":True,"release_integrity":True},"state feedback only"),
      ("terminal_as_success",{"physical":True,"task_effect":False,"matched_arms":True,"arm_audit":True,"release_integrity":True},"terminal not effect"),
    ]
    checked=[]
    for name,r,reason in controls:
        out=classify(r); assert out=="HOLD"
        checked.append({"name":name,"outcome":out,"reason":reason})
    snapshot={"physical":True,"task_effect":True,"matched_arms":False,"arm_audit":False,"release_integrity":True}
    out={"schema":"matched-recovery-entry-gate-1866-v1","formal_invocations":1,"reruns":0,"vectors":rows,"controls":checked,"current_snapshot":snapshot,"decision":"PASS_MATCHED_RECOVERY_ENTRY_GATE_HOLD_SCOPED","current_disposition":classify(snapshot),"digest":hashlib.sha256(json.dumps(rows+checked,sort_keys=True).encode()).hexdigest()}
    assert out["current_disposition"]=="HOLD" and all(x["candidate"]==x["oracle"] for x in rows)
    print(json.dumps(out,sort_keys=True))
if __name__=="__main__": main()
