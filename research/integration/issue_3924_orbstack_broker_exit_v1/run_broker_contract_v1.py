#!/usr/bin/env python3
"""Run the preregistered fake-executable broker contract matrix."""
import hashlib, json, os, pathlib, shutil, subprocess, sys, time

ROOT = pathlib.Path(__file__).resolve().parent
OUT = ROOT / "formal"
SRC = ROOT / "source"
BROKER = SRC / "broker_candidate.py"
BASELINE = SRC / "broker_baseline.py"
FAKE = SRC / "fake_codex.py"

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def write_request(d, rid="r1", prompt="test"):
    d.mkdir(parents=True, exist_ok=True)
    (d / f"{rid}.request.json").write_text(json.dumps({"request_id":rid,"schema":"/repo/schema.json","working":"/repo","prompt":prompt})+"\n")
def execute(name, broker, requests, env_extra=None):
    ipc=OUT/name; ipc.mkdir(parents=True, exist_ok=True)
    for rid,prompt in requests: write_request(ipc,rid,prompt)
    env=os.environ.copy(); env.update({"CODEX_EXE":"/evidence/source/fake_codex.py","HOST_MODEL_BROKER_TIMEOUT_S":"0.15","FAKE_LOG":"/evidence/formal/fake_calls.jsonl"}); env.update(env_extra or {})
    p=subprocess.run([sys.executable,str(broker),"--ipc",str(ipc),"--repo",str(ROOT),"--once"],capture_output=True,text=True,env=env,timeout=5)
    (ipc/"process.stdout").write_text(p.stdout); (ipc/"process.stderr").write_text(p.stderr)
    (ipc/"process.exit").write_text(str(p.returncode)+"\n")
    return p.returncode

def main():
    if OUT.exists(): raise SystemExit("formal output exists; refusing repeat")
    OUT.mkdir()
    log=OUT/"fake_calls.jsonl"; log.write_text("")
    cases=[]
    cases.append(("baseline_exit0",execute("baseline_exit0",BASELINE,[("r1","exit=0")],{"FAKE_MODE":"exit0"})))
    cases.append(("candidate_exit0",execute("candidate_exit0",BROKER,[("r1","exit=0")],{"FAKE_MODE":"exit0"})))
    cases.append(("candidate_exit7",execute("candidate_exit7",BROKER,[("r1","exit=7")],{"FAKE_MODE":"exit7"})))
    cases.append(("candidate_timeout",execute("candidate_timeout",BROKER,[("r1","sleep")],{"FAKE_MODE":"sleep"})))
    cases.append(("candidate_unavailable",execute("candidate_unavailable",BROKER,[("r1","missing")],{"CODEX_EXE":"/no/such/fake-codex"})))
    bad=OUT/"candidate_malformed"; bad.mkdir(); (bad/"bad.request.json").write_text("{not-json\n")
    before=len(log.read_text().splitlines())
    env=os.environ.copy(); env.update({"CODEX_EXE":"/evidence/source/fake_codex.py","FAKE_LOG":"/evidence/formal/fake_calls.jsonl"})
    p=subprocess.run([sys.executable,str(BROKER),"--ipc",str(bad),"--repo",str(ROOT),"--once"],capture_output=True,text=True,env=env,timeout=5)
    (bad/"process.stdout").write_text(p.stdout); (bad/"process.stderr").write_text(p.stderr); (bad/"process.exit").write_text(str(p.returncode)+"\n")
    malformed_no_call=(len(log.read_text().splitlines())==before)
    cases.append(("candidate_malformed",p.returncode))
    cases.append(("candidate_two_queued",execute("candidate_two_queued",BROKER,[("r1","exit=0"),("r2","exit=0")],{"FAKE_MODE":"exit0"})))
    summary={"cases":cases,"fake_invocations":len(log.read_text().splitlines()),"malformed_no_fake_invocation":malformed_no_call}
    (OUT/"runner_summary.json").write_text(json.dumps(summary,indent=2)+"\n")
    print(json.dumps(summary,sort_keys=True))

if __name__=="__main__": main()
