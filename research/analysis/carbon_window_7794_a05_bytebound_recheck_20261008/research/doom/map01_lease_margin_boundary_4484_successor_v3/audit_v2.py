#!/usr/bin/env python3
"""Independent raw-only audit; does not import runner, transport, server, or Lease."""
import hashlib,json,pathlib
P=pathlib.Path(__file__).parent/"out"/"raw.json"; raw=json.loads(P.read_text())
errors=[]; results=[]
def req(x,msg):
    if not x: errors.append(msg)
for c in raw["cases"]:
    cid=c["case_id"]; rows=c["rows"]; clocks=[r for r in rows if r["request"].get("op")=="clock"]
    sends=c["host_clock_reads_ns"]
    req(len(clocks)==3,cid+": not exactly three calibration exchanges")
    req(len(sends)>=7,cid+": missing wrapper host readings")
    bounds=[]
    for i,row in enumerate(clocks):
        h1=sends[2*i]; h4=sends[2*i+1]; resp=row["response"]
        req(row["request"].get("op")=="clock",cid+": request kind")
        req(resp["container_receive_ns"]<=resp["container_clock_ns"]<=resp["container_send_ns"],cid+": C2/C3 ordering")
        req(h1<=h4,cid+": H1/H4 ordering")
        req(resp["request_id"]=="clock-%d"%i,cid+": request id sequence")
        bounds.append((resp["container_send_ns"]-h4,resp["container_send_ns"]-h1))
    lower=min(x[0] for x in bounds); upper=max(x[1] for x in bounds)
    req(c["translation_rows"]==([] if c["exception"] and "below 5s" in c["exception"]["message"] else c["translation_rows"]),cid+": malformed translations")
    sent=[r for r in rows if r["request"].get("op")=="submit"]
    remain_before_send=c["host_deadline_ns"]-sends[6]
    disposition=("HOLD" if not sent else sent[0]["response"].get("decision","unknown").upper())
    if disposition=="HOLD":
        req(not sent,cid+": lease escaped after HOLD")
        req(remain_before_send<5_000_000_000,cid+": HOLD without sub-5s margin")
    else:
        req(len(sent)==1,cid+": submit count")
        tr=c["translation_rows"]
        req(len(tr)==1,cid+": translation record count")
        if tr:
            t=tr[0]; req(t["offset_lower_ns"]==lower,cid+": non-conservative lower offset")
            req(t["offset_upper_ns"]==upper,cid+": upper offset mismatch")
            req(t["runtime_deadline_ns"]==t["host_deadline_ns"]+lower,cid+": translation mismatch")
            sr=sent[0]["response"]
            req(sr.get("lease_deadline_ns",t["runtime_deadline_ns"])==t["runtime_deadline_ns"],cid+": Lease deadline differs")
            if sr.get("decision")=="accepted":
                c_remaining=sr["remaining_ns"]
                h_equiv=t["host_deadline_ns"]-(sr["remaining_sample_ns"]-lower)
                req(c_remaining<=h_equiv,cid+": translated deadline extended host authority")
        if c["margin_ns"]==31_000_000_000:
            req(sent[0]["response"].get("decision")=="rejected" and "30 second" in sent[0]["response"].get("reason",""),cid+": 31s horizon was not rejected")
    results.append({"case_id":cid,"disposition":disposition,"clock_exchanges":len(clocks),
        "probe_intervals_ns":[[lo,hi] for lo,hi in bounds],"minimum_lower_offset_ns":lower,
        "maximum_upper_offset_ns":upper,"post_probe_host_margin_ns":remain_before_send,
        "lease_decision":sent[0]["response"].get("decision") if sent else None})
expected={"deadline-5s":"HOLD","deadline-5s249ms":"HOLD","deadline-5s250ms":"ACCEPTED","deadline-6s":"ACCEPTED","deadline-31s":"REJECTED"}
for x in results: req(x["disposition"]==expected[x["case_id"]],x["case_id"]+": differs from preregistered prediction")
req(raw["shutdown_response"]["request_id"]=="shutdown","missing shutdown acknowledgement")
req(len([l for l in raw["server_journal"].splitlines() if l])==20,"server journal count mismatch")
summary={"schema":"issue-5062-independent-audit-v2","disposition":"PASS_PREREGISTERED" if not errors else "FAIL_CONTRACT_OR_AUDIT",
 "errors":errors,"cases":results,"raw_sha256":hashlib.sha256(P.read_bytes()).hexdigest(),
 "source_git_blob_ids":{"sender":raw["sender_blob"],"exchange":raw["exchange_blob"],"lease":raw["lease_blob"],"server":raw["server_blob"]},
 "limits":["one WSL2 and Docker Desktop host session only","no game, model, GUI input, or network",
 "the 5.249s prediction is evaluated against observed elapsed time, not retroactively altered"]}
(P.parent/"audit-v2.json").write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n")
print(summary["disposition"],"errors",len(errors))
for e in errors: print("AUDIT:",e)



