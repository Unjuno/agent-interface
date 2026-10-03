"""Exclusive one-shot host driver; stage outputs and receipts are never reused."""
import argparse
import datetime
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent

def command(argv, timeout=15):
    started = datetime.datetime.now(datetime.timezone.utc).isoformat()
    try:
        p = subprocess.run(argv, capture_output=True, timeout=timeout)
        return {"argv":argv,"started_utc":started,"returncode":p.returncode,
                "stdout":p.stdout.decode(errors="replace"),"stderr":p.stderr.decode(errors="replace")}
    except subprocess.TimeoutExpired as e:
        return {"argv":argv,"started_utc":started,"returncode":None,"stop":"TIMEOUT",
                "stdout":(e.stdout or b"").decode(errors="replace"),"stderr":(e.stderr or b"").decode(errors="replace")}

def main():
    parser = argparse.ArgumentParser(); parser.add_argument("stage",choices=("candidate","auditor")); args=parser.parse_args()
    plan = json.loads((ROOT/"PLAN.json").read_text())
    freeze = json.loads((ROOT/"FREEZE.json").read_text())
    for name,digest in freeze["sha256"].items():
        if hashlib.sha256((ROOT/name).read_bytes()).hexdigest() != digest: raise SystemExit("STOP_SOURCE_DRIFT: "+name)
    if args.stage == "auditor":
        predecessor=json.loads((ROOT/"runs/candidate/receipt.json").read_text())
        if predecessor["run"]["returncode"] != 0 or predecessor["terminal"]["Running"]:
            raise SystemExit("STOP_CANDIDATE_NOT_SUCCESSFUL_TERMINAL")
    output=ROOT/"runs"/args.stage; output.mkdir(parents=True,exist_ok=False)
    name="x11-7024-a01-5ce3-"+args.stage
    base=["orbctl","run","-m",plan["vm"],"-u","root","docker"]
    driver=["/study/candidate.py","/study/PLAN.json","/out/evidence"] if args.stage == "candidate" else [
        "/study/auditor.py","/study/runs/candidate/evidence/raw.jsonl","/study/PLAN.json","/out/AUDIT.json"]
    argv=base+["create","--name",name,"--label","research.owner="+plan["owner"],"--pull=never","--network=none",
        "--read-only","--cap-drop=ALL","--security-opt=no-new-privileges","--cpus=1","--memory=512m",
        "--memory-swap=512m","--pids-limit=128","--tmpfs=/tmp:rw,nosuid,nodev,size=64m",
        "--mount","type=bind,src=/mnt/mac"+str(ROOT)+",dst=/study,readonly",
        "--mount","type=bind,src=/mnt/mac"+str(output)+",dst=/out",plan["image_id"]]+driver
    record={"stage":args.stage,"scientific_candidate_invocations":1 if args.stage=="candidate" else 0,
            "freeze_sha256":hashlib.sha256((ROOT/"FREEZE.json").read_bytes()).hexdigest()}
    with (output/"receipt.json").open("x") as stream:
        record["create"]=command(argv)
        if record["create"]["returncode"] == 0:
            record["before"]=command(base+["inspect",name])
            record["run"]=command(base+["start","-a",name],90)
            inspected=command(base+["inspect",name]); record["after"]=inspected
            if inspected["returncode"] == 0:
                obj=json.loads(inspected["stdout"])[0]
                if obj["State"]["Running"]:
                    if obj["Name"] != "/"+name or obj["Config"]["Labels"].get("research.owner") != plan["owner"]:
                        raise RuntimeError("STOP_OWNER_IDENTITY_MISMATCH")
                    record["owned_stop"]=command(base+["stop","-t","2",name])
                    record["after"]=command(base+["inspect",name])
                    obj=json.loads(record["after"]["stdout"])[0]
                record["terminal"]=obj["State"]
        json.dump(record,stream,indent=2); stream.write("\n")
    print(json.dumps({"stage":args.stage,"run":record.get("run"),"terminal":record.get("terminal")}))
    if record.get("run",{}).get("returncode") != 0 or record.get("terminal",{}).get("Running",True): raise SystemExit(1)

if __name__ == "__main__": main()
