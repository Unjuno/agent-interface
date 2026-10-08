"""Delivery-only saved provenance checks; not a prospective native producer input."""
import argparse
import datetime
import hashlib
import json
import shutil
import subprocess
from pathlib import Path
import auditor
import saved_verify

HERE=Path(__file__).resolve().parent

def verify(git_custody=False):
    freeze=auditor.read(HERE/"FREEZE.json")
    plan=auditor.read(HERE/"plan.json")
    digest=hashlib.sha256((HERE/"FREEZE.json").read_bytes()).hexdigest()
    for name in ("source-stage-v2-before.json","source-stage-v2-after.json"):
        r=auditor.read(HERE/"setup"/name)
        auditor.join(r["exit_code"],0,"stage verification exit")
        actual=auditor.parse(r["output"])
        auditor.join(actual["frozen_source_sha256"],freeze["source_sha256"],"before/after staged source")
        auditor.join(actual["freeze_sha256"],digest,"staged exact freeze")
        auditor.join(actual["writable_files"],[],"readonly staged source")
    old=HERE/"FREEZE-v1-unexecuted.json"
    auditor.require(hashlib.sha256(old.read_bytes()).hexdigest()==freeze["supersedes_unexecuted_freeze"]["sha256"],"retained v1")
    auditor.join(freeze["supersedes_unexecuted_freeze"]["formal_producer_invocations"],0,"unexecuted v1")
    native=auditor.read(HERE/"setup/producer-terminal.json")
    audit=auditor.read(HERE/"setup/auditor-terminal.json")
    auditor.join(native["command"],freeze["host_command"],"single host command")
    auditor.join(audit["command"],freeze["auditor_command"],"single auditor command")
    for r in (native,audit):
        auditor.join(r["exit_code"],0,"official terminal")
        auditor.join(r["invocations"],1,"single invocation")
    inspector=auditor.read(HERE/"setup/auditor-inspect.json")
    auditor.join(inspector["exit_code"],0,"official inspect exit")
    i=auditor.parse(inspector["output"])
    auditor.join(i["Image"],plan["image_id"],"official image")
    auditor.join(i["RestartCount"],0,"official no restart")
    for k,v in {"Running":False,"OOMKilled":False,"Restarting":False,"ExitCode":0}.items():
        auditor.join(i["State"][k],v,"official terminal state")
    for k,v in {"NanoCpus":1_000_000_000,"Memory":134217728,"MemorySwap":134217728,
                "PidsLimit":32,"ReadonlyRootfs":True,"NetworkMode":"none"}.items():
        auditor.join(i["HostConfig"][k],v,"official runtime limits")
    auditor.join(i["Config"]["User"],"501:501","official unprivileged")
    auditor.require("ALL" in i["HostConfig"]["CapDrop"] and "no-new-privileges" in i["HostConfig"]["SecurityOpt"],"official capabilities")
    cmd=freeze["auditor_command"]
    auditor.join(i["Config"]["Cmd"],cmd[cmd.index(plan["image_id"])+1:],"official actual command")
    mounts={m["Destination"]:m for m in i["Mounts"]}
    for pos,s in enumerate(cmd):
        if s=="--mount":
            fields=cmd[pos+1].split(",")
            parsed=dict(x.split("=",1) for x in fields if "=" in x)
            m=mounts[parsed["dst"]]
            auditor.join(m["Source"],parsed["src"],"official mount source")
            auditor.join(m["RW"],"readonly" not in fields,"official mount permission")
    def utc(s): return datetime.datetime.fromisoformat(s.replace("Z","+00:00"))
    astart=utc(i["State"]["StartedAt"])
    for cell in plan["cells"]:
        n=auditor.parse(auditor.read(HERE/"raw"/cell["id"]/"launch.json")["inspect_stdout"])
        auditor.require(utc(n["State"]["FinishedAt"])<astart,"official auditor only after native terminal")
    auditor.join(auditor.read(HERE/"setup/auditor-copy.json")["exit_code"],0,"official result retention")
    auditor.join(auditor.read(HERE/"audit/controls.json")["rejected"],12,"effective controls count")
    auditor.join([c["name"] for c in auditor.read(HERE/"audit/controls.json")["controls"]],freeze["saved_controls"],"prospective controls")
    if git_custody:
        bundled="/Library/Developer/CommandLineTools/usr/bin/git"
        git=bundled if Path(bundled).exists() else shutil.which("git")
        auditor.require(git is not None,"git read-only custody available")
        prefix=str(HERE.relative_to(Path(subprocess.check_output([git,"rev-parse","--show-toplevel"],cwd=HERE,text=True).strip())))+"/"
        def blob(commit,name): return subprocess.check_output([git,"show",commit+":"+name],cwd=HERE)
        receipt=auditor.read(HERE/"setup/public-freezes.json")
        auditor.require(blob(receipt["freeze_v2_commit"],prefix+"FREEZE.json")== (HERE/"FREEZE.json").read_bytes(),"public prospective freeze blob")
        auditor.require(blob(freeze["supersedes_unexecuted_freeze"]["commit"],prefix+"FREEZE.json")==old.read_bytes(),"public unexecuted freeze blob")
        for name,h in freeze["source_sha256"].items():
            auditor.require(hashlib.sha256(blob(freeze["source_checkpoint"],prefix+name)).hexdigest()==h,"public prospective source blob")
        predecessor="research/live_control/phase_diversified_capture_6067_t1_20261003_3cbf/"
        for name in ("common.py","fixture.py","policy.py","x11.py"):
            auditor.require(blob(plan["baseline_commit"],predecessor+name)==(HERE/"baseline"/name).read_bytes(),"immutable baseline copy")
    print(json.dumps({"official_producer":1,"official_auditor":1,"native_replays":0,
                      "staged_source_files":len(freeze["source_sha256"]),"git_custody":git_custody},sort_keys=True))

if __name__=="__main__":
    ap=argparse.ArgumentParser(); ap.add_argument("--git",action="store_true")
    verify(ap.parse_args().git)
