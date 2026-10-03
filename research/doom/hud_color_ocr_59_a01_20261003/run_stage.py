"""One owned, bounded container stage; always retain terminal inspection."""
import argparse
import datetime
import hashlib
import json
import subprocess
import time
from pathlib import Path

ROOT=Path(__file__).resolve().parent
OWNER="01a0b98b-5ce3-7f53-82f3-e09294f24d57"
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def call(command,timeout=300):
    try:
        result=subprocess.run(command,capture_output=True,text=True,timeout=timeout)
        return {"command":command,"exit":result.returncode,"stdout":result.stdout,"stderr":result.stderr}
    except subprocess.TimeoutExpired as error:
        return {"command":command,"exit":None,"stop":"CLIENT_TIMEOUT","stdout":(error.stdout or b"").decode(errors="replace"),"stderr":(error.stderr or b"").decode(errors="replace")}

parser=argparse.ArgumentParser()
parser.add_argument("phase",choices=["pilot","evaluation"])
parser.add_argument("role",choices=["candidate","auditor"])
args=parser.parse_args()
freeze=json.loads((ROOT/"FREEZE.json").read_text())
study=freeze["guest_study_path"]
source=freeze["guest_source_path"]
for name,expected in {**freeze["source_sha256"],**freeze["input_sha256"]}.items():
    if sha(ROOT/name)!=expected: raise SystemExit(f"STOP_FROZEN_SOURCE_INPUT_DRIFT {name}")
for item in json.loads((ROOT/f"input/{args.phase}/manifest.json").read_text()):
    if sha(ROOT/f"input/{args.phase}"/item["image"])!=item["sha256"]: raise SystemExit("STOP_INPUT_IMAGE_DRIFT")
prefix=["orbctl","run","-m",freeze["vm"],"-u","root","docker"]
image=call(prefix+["image","inspect",freeze["image_id"]],30)
if image["exit"]!=0 or json.loads(image["stdout"])[0]["Id"]!=freeze["image_id"]: raise SystemExit("STOP_IMAGE_DRIFT")
if args.phase=="evaluation":
    selection=json.loads((ROOT/"SELECTION.json").read_text())
    if sha(ROOT/"runs/pilot_candidate/raw.json")!=selection["pilot_raw_sha256"] or sha(ROOT/"runs/pilot_auditor/audit.json")!=selection["pilot_audit_sha256"]: raise SystemExit("STOP_PILOT_SELECTION_DRIFT")
    methods="gray,"+selection["selected"]
else:
    methods="gray,red,red_excess"
if args.role=="auditor":
    receipt=json.loads((ROOT/f"runs/{args.phase}_candidate/receipt.json").read_text())
    if receipt["run"]["exit"]!=0: raise SystemExit("STOP_AUDITOR_REQUIRES_CANDIDATE_SUCCESS")
name=f"hud59-5ce3-{args.phase}-{args.role}"
inventory=call(prefix+["ps","-a","--filter",f"name=^{name}$","--format","{{.ID}}"],30)
if inventory["exit"]!=0 or inventory["stdout"].strip(): raise SystemExit("STOP_CONTAINER_NAME_OCCUPIED")
destination=ROOT/f"runs/{args.phase}_{args.role}"
destination.mkdir(parents=True,exist_ok=False)
command=prefix+["run","--name",name,"--pull=never","--network=none","--read-only","--cap-drop=ALL","--security-opt=no-new-privileges","--cpus=1","--memory=512m","--memory-swap=512m","--pids-limit=64","--label",f"study.owner={OWNER}","--label","study.question=59-hud-color-ocr","--tmpfs","/tmp:rw,nosuid,nodev,size=64m","-v",f"{study}/input/{args.phase}:/input:ro","-v",f"{study}/runs/{args.phase}_{args.role}:/out:rw"]
if args.role=="candidate":
    command += ["-v",f"{study}/candidate.py:/code/candidate.py:ro",freeze["image_id"],"/code/candidate.py","--transforms",methods]
else:
    command += ["-v",f"{study}/auditor.py:/code/auditor.py:ro","-v",f"{study}/runs/{args.phase}_candidate:/raw:ro","-v",f"{study}/TRUTH.json:/truth/TRUTH.json:ro","-v",f"{source}:/source:ro",freeze["image_id"],"/code/auditor.py","--phase",args.phase]
started=datetime.datetime.now(datetime.timezone.utc).isoformat()
clock=time.monotonic_ns()
run=call(command)
inspection=call(prefix+["inspect",name],30)
cleanup=None
if inspection["exit"]==0:
    container=json.loads(inspection["stdout"])[0]
    if container["Config"]["Labels"].get("study.owner")==OWNER and container["Image"]==freeze["image_id"] and container["State"]["Running"]:
        cleanup=call(prefix+["stop","--time","5",name],15)
        inspection=call(prefix+["inspect",name],30)
receipt={"started_utc":started,"elapsed_ns":time.monotonic_ns()-clock,"phase":args.phase,"role":args.role,"freeze_sha256":sha(ROOT/"FREEZE.json"),"selection_sha256":sha(ROOT/"SELECTION.json") if args.phase=="evaluation" else None,"run":run,"terminal_inspection":inspection,"cleanup":cleanup}
with (destination/"receipt.json").open("x") as output: json.dump(receipt,output,indent=2); output.write("\n")
print(json.dumps({"phase":args.phase,"role":args.role,"exit":run["exit"],"stdout":run["stdout"],"stderr":run["stderr"][-1500:]}))
terminal=json.loads(inspection["stdout"])[0] if inspection["exit"]==0 else None
if run["exit"]!=0 or not terminal or terminal["State"]["Running"] or terminal["State"]["ExitCode"]!=0: raise SystemExit(1)
