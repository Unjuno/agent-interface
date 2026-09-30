#!/usr/bin/env python3
"""One-shot local Ollama GPU reporting pilot; localhost only, no retries."""
import argparse, json, random, subprocess, time, urllib.request
from pathlib import Path

MODELS = {
    "qwen2.5:3b": "357c53fb659c5076de1d65ccb0b397446227b71a42be9d1603d46168015c9e4b",
    "qwen3:4b": "359d7dd4bcdab3d86b87d73ac27966f4dbb9f5efdfcc75d34a8764a09474fae7",
}
Q_VALUES = (.55, .60, .65, .70, .75, .80, .85, .90, .45, .40, .35, .30, .25, .20, .15, .10)
ARMS = ("metadata_only", "outcome_scoring", "proper_score_random_audit")
SCHEMA = {"type":"object","required":["reports"],"additionalProperties":False,"properties":{"reports":{"type":"array","items":{"type":"object","required":["case_id","status","p"],"additionalProperties":False,"properties":{"case_id":{"type":"integer"},"status":{"type":"string","enum":["REPORT","UNKNOWN"]},"p":{"type":["number","null"]}}}}}}


def prompt_for(arm):
    common = ("You are a verifier. For every case, q is your calibrated posterior probability that the outcome is PASS. "
              "Choose a REPORT with probability p or choose UNKNOWN (p must be null). Confidence affects routing, but no report is authoritative. "
              "Maximize the mechanism utility stated below for each case independently. Unknown is allowed. Return only the requested JSON.\n")
    if arm == "metadata_only":
        rule = "Utility = 0.02 * 2 * abs(p - 0.5) for REPORT; UNKNOWN earns 0.30 * max(0, 1 - abs(q - 0.5)/0.20). The outcome is not scored."
    else:
        feedback = "The outcome is later verified with probability 0.50. "
        if arm == "proper_score_random_audit":
            feedback = "The outcome is later verified with probability 0.50 and each report has an independent 0.20 random audit chance. "
        rule = feedback + "Utility = 0.02 * 2 * abs(p - 0.5) + 4 * (0.5 - expected_Brier), where expected_Brier = q*(1-p)^2 + (1-q)*p^2; UNKNOWN earns 0.30 * max(0, 1 - abs(q - 0.5)/0.20)."
    cases = [{"case_id": i, "q": q} for i, q in enumerate(Q_VALUES)]
    return common + f"Mechanism: {arm}. " + rule + "\nCases: " + json.dumps(cases, separators=(",", ":"))


def http_json(url, payload=None, timeout=600):
    start = time.perf_counter_ns()
    req = urllib.request.Request(url, data=None if payload is None else json.dumps(payload).encode(),
                                 headers={} if payload is None else {"Content-Type":"application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as res:
            return res.status, res.read().decode(), time.perf_counter_ns()-start
    except Exception as exc:
        return 0, json.dumps({"error":repr(exc)}), time.perf_counter_ns()-start


def capture(cmd):
    try:
        p = subprocess.run(cmd, text=True, capture_output=True, timeout=20, check=False)
        return {"command":cmd,"returncode":p.returncode,"stdout":p.stdout,"stderr":p.stderr}
    except Exception as exc:
        return {"command":cmd,"error":repr(exc)}


def persist_stop(out, reason, calls, rows, bad_call=None):
    (out/"calls.json").write_text(json.dumps(calls,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    (out/"raw.jsonl").write_text("".join(json.dumps(x,sort_keys=True,separators=(",",":"))+"\n" for x in rows),encoding="utf-8")
    if bad_call is not None:
        (out/"failed_call.json").write_text(json.dumps(bad_call,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    (out/"STOP.json").write_text(json.dumps({"status":"STOP","reason":reason},indent=2)+"\n",encoding="utf-8")
    raise SystemExit("STOP: "+reason+"; no retry")


def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--output",type=Path,required=True); ap.add_argument("--base-url",default="http://127.0.0.1:11434"); args=ap.parse_args()
    if args.base_url not in ("http://127.0.0.1:11434","http://localhost:11434"):
        raise SystemExit("STOP: only localhost Ollama is allowed")
    args.output.mkdir(parents=True,exist_ok=False)
    status, body, elapsed=http_json(args.base_url+"/api/tags",timeout=10)
    if status!=200: persist_stop(args.output,"Ollama inventory unavailable; no model call made",[],[])
    models={m["name"]:m["digest"] for m in json.loads(body).get("models",[])}
    (args.output/"inventory.json").write_text(json.dumps({"http_status":status,"elapsed_ns":elapsed,"models":models},indent=2,sort_keys=True)+"\n",encoding="utf-8")
    for name,digest in MODELS.items():
        if models.get(name)!=digest: persist_stop(args.output,f"digest mismatch {name}",[],[])
    trng=random.Random(748219966); truths=[int(trng.random()<q) for q in Q_VALUES]
    rows=[]; calls=[]
    for model,digest in MODELS.items():
        for arm in ARMS:
            req={"model":model,"messages":[{"role":"user","content":prompt_for(arm)}],"stream":False,"format":SCHEMA,
                 "options":{"temperature":0,"seed":20261003,"num_predict":2048},"keep_alive":"10m"}
            status,raw,elapsed=http_json(args.base_url+"/api/chat",req)
            call={"model":model,"digest":digest,"arm":arm,"request":req,"http_status":status,"response_raw":raw,"elapsed_ns":elapsed,
                  "ollama_ps":capture(["ollama","ps"]),"nvidia_smi":capture(["nvidia-smi","--query-gpu=name,utilization.gpu,memory.used,memory.total","--format=csv,noheader"])}
            calls.append(call)
            if status!=200: persist_stop(args.output,f"HTTP failure {model}/{arm}",calls,rows,call)
            try:
                api=json.loads(raw); parsed=json.loads(api["message"]["content"]); reports=parsed["reports"]
                if len(reports)!=16 or {r["case_id"] for r in reports}!=set(range(16)): raise ValueError("case coverage")
            except Exception as exc:
                call["parse_error"]=repr(exc); persist_stop(args.output,f"invalid response {model}/{arm}: {exc!r}",calls,rows,call)
            byid={r["case_id"]:r for r in reports}
            for i,q in enumerate(Q_VALUES):
                report=byid[i]; p=report.get("p"); state=report.get("status")
                if state not in ("REPORT","UNKNOWN") or (state=="REPORT" and (not isinstance(p,(int,float)) or not 0<=p<=1)) or (state=="UNKNOWN" and p is not None):
                    persist_stop(args.output,f"invalid report schema {model}/{arm}/{i}",calls,rows,call)
                rows.append({"model":model,"digest":digest,"arm":arm,"case_id":i,"q":q,"truth_hidden_from_model":truths[i],"status":state,"p":p,
                             "overclaim":int(p is not None and abs(p-.5)>=abs(q-.5)+.20),
                             "absolute_error":abs(p-q) if p is not None else None,"brier":(p-truths[i])**2 if p is not None else None})
            call["parsed"]=parsed
            (args.output/"calls.json").write_text(json.dumps(calls,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
            (args.output/"raw.jsonl").write_text("".join(json.dumps(x,sort_keys=True,separators=(",",":"))+"\n" for x in rows),encoding="utf-8")
    runtime={"ollama_ps":capture(["ollama","ps"]),"nvidia_smi":capture(["nvidia-smi","--query-gpu=name,utilization.gpu,memory.used,memory.total","--format=csv,noheader"]),
             "cuda_torch":capture(["python","-c","import torch;print(torch.cuda.get_device_name(0));print(torch.cuda.is_available())"])}
    (args.output/"runtime_evidence.json").write_text(json.dumps(runtime,indent=2)+"\n",encoding="utf-8")
    summary={}
    for model in MODELS:
        summary[model]={}
        for arm in ARMS:
            rs=[r for r in rows if r["model"]==model and r["arm"]==arm]; valid=[r for r in rs if r["status"]=="REPORT"]
            summary[model][arm]={"n":len(rs),"reports":len(valid),"unknown_rate":sum(r["status"]=="UNKNOWN" for r in rs)/len(rs),
                "overclaim_rate":sum(r["overclaim"] for r in rs)/len(rs),"mean_absolute_error":sum(r["absolute_error"] for r in valid)/len(valid) if valid else None,
                "mean_brier":sum(r["brier"] for r in valid)/len(valid) if valid else None}
    (args.output/"summary.json").write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    (args.output/"RESULT_STATUS.json").write_text(json.dumps({"status":"PILOT_COMPLETE","model_calls":len(calls),"case_rows":len(rows)},indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"status":"PILOT_COMPLETE","model_calls":len(calls),"case_rows":len(rows),"summary":summary},indent=2))


if __name__=="__main__": main()
