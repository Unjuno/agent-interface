"""Fail-closed preflight, one formal container, and isolated-input auditor."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import time

EXP=Path(__file__).resolve().parent
REPO=EXP.parents[2]
SEED=REPO/"research/needle_role_skill_reload_3780_v1/formal/seed-3788/builder/skill.json"
IMAGE="sha256:392307d22300de8b5986851a12d9176dfc0fc073e65bf6523ebd7dcbeb23564e"
CONTEXT="orbstack"


def sha(b:bytes)->str:return hashlib.sha256(b).hexdigest()
def run(argv):return subprocess.run(argv,text=True,capture_output=True)
def git(*args):
    p=run(["git",*args])
    if p.returncode:raise RuntimeError("git command failed: "+repr(args)+" "+p.stderr)
    return p.stdout.strip()
def inspect_container(name):
    p=run(["docker","--context",CONTEXT,"inspect",name])
    if p.returncode:raise RuntimeError("cannot inspect owned container: "+p.stderr)
    return json.loads(p.stdout)[0]
def write_json(path,value):path.write_text(json.dumps(value,sort_keys=True,indent=2)+"\n")


ALLOCATION="needle-publication-orbstack-bind-5066-20260928-03"
OUTPUT_PATH=Path("/tmp/unjuno-5134-orbstack-publication-20260928-03")


def validate_output_path(requested:str)->Path:
    out=Path(requested).resolve()
    if out!=OUTPUT_PATH.resolve():raise RuntimeError("output path differs from frozen allocation path")
    return out


def release_marker(issue_number:int,allocation:str,main_sha:str)->str:
    if issue_number==5074:return f"SLOT_RELEASE: #5074 -> #5134 allocation={allocation} main={main_sha}"
    if issue_number==5085:return f"QUEUE_RELEASE: #5085 authorizes #5134 allocation={allocation} main={main_sha}"
    raise RuntimeError("unsupported release authority issue")


def verify_slot_release(comments:list,comment_id:int,issue_number:int,allocation:str,main_sha:str)->dict:
    if not isinstance(comments,list):raise RuntimeError("slot release comments are not a list")
    owner_comments=[c for c in comments if isinstance(c,dict) and
                    isinstance(c.get("user"),dict) and c["user"].get("login")=="Unjuno"]
    if not owner_comments:raise RuntimeError("no slot-owner comments available")
    latest=max(owner_comments,key=lambda c:(str(c.get("created_at","")),int(c.get("id",0))))
    if latest.get("id")!=comment_id:raise RuntimeError("slot release comment is not the owner's latest comment")
    expected=release_marker(issue_number,allocation,main_sha)
    if expected not in {line.strip() for line in str(latest.get("body","")).splitlines()}:
        raise RuntimeError("owner comment does not explicitly release the exact allocation on current main")
    return {"issue":issue_number,"comment_id":comment_id,"owner":latest["user"]["login"],
            "created_at":latest.get("created_at"),"marker":expected}


def main():
    ap=argparse.ArgumentParser();ap.add_argument("--output",required=True);ap.add_argument("--preflight-only",action="store_true")
    ap.add_argument("--slot-release-5074-comment-id",type=int)
    ap.add_argument("--queue-release-5085-comment-id",type=int)
    args=ap.parse_args();out=validate_output_path(args.output)
    if out.exists():raise RuntimeError("output destination already exists")
    if sha(SEED.read_bytes())!="2e7bff5a2c6ffd35935c5e3c88d08cb686fb736d332c8d5cdb24bb1b67dc873a":raise RuntimeError("seed identity mismatch")
    freeze=json.loads((EXP/"FREEZE.json").read_text()); source_expected=freeze["source_sha256"]
    source_actual={n:sha((EXP/n).read_bytes()) for n in source_expected}
    if source_actual!=source_expected:raise RuntimeError("source hash mismatch")
    commit=git("rev-parse","HEAD");tree=git("rev-parse","HEAD^{tree}")
    if git("status","--porcelain"):raise RuntimeError("checkout must be clean before allocation")
    live_main=run(["git","ls-remote","origin","refs/heads/main"])
    if live_main.returncode:raise RuntimeError("cannot verify live main ref")
    live_main_sha=live_main.stdout.split()[0] if live_main.stdout.split() else ""
    if freeze.get("base_main_sha")!=live_main_sha:raise RuntimeError("freeze base is not the current remote main")
    if git("merge-base",commit,live_main_sha)!=live_main_sha:raise RuntimeError("source branch does not include exact current main")
    blob_ids={n:git("rev-parse",f"HEAD:{EXP.relative_to(REPO)}/{n}") for n in source_expected}
    seed_blob=git("hash-object",str(SEED))
    if seed_blob!="45b80150dac503f4eb6f3cb5d82f9afa2c587107":raise RuntimeError("seed Git blob identity mismatch")
    if args.preflight_only:
        print(json.dumps({"preflight":"PASS_STATIC","source_commit":commit,"source_tree_sha":tree,
                          "live_main_sha":live_main_sha,"docker_invocations":0,"output_created":False}));return 0
    if args.slot_release_5074_comment_id is None or args.queue_release_5085_comment_id is None:
        raise RuntimeError("formal launch requires exact owner release comments on both #5074 and #5085")
    slot_release={}
    for issue_number,comment_id in ((5074,args.slot_release_5074_comment_id),(5085,args.queue_release_5085_comment_id)):
        comments_run=run(["gh","api","--paginate","--slurp",f"repos/Unjuno/agent-interface/issues/{issue_number}/comments?per_page=100"])
        if comments_run.returncode:raise RuntimeError(f"cannot read GitHub release on #{issue_number}: "+comments_run.stderr)
        try:
            pages=json.loads(comments_run.stdout)
            comments=[comment for page in pages for comment in page] if pages and isinstance(pages[0],list) else pages
            slot_release[str(issue_number)]=verify_slot_release(comments,comment_id,issue_number,
                  ALLOCATION,live_main_sha)
        except (ValueError,TypeError,IndexError) as exc:
            raise RuntimeError(f"cannot verify GitHub release on #{issue_number}: "+str(exc)) from exc
    context=run(["docker","--context",CONTEXT,"context","show"])
    if context.returncode or context.stdout.strip()!=CONTEXT:raise RuntimeError("wrong/unavailable Docker context")
    image=run(["docker","--context",CONTEXT,"image","inspect",IMAGE,"--format","{{.Id}} {{.Os}}/{{.Architecture}}"])
    if image.returncode or image.stdout.strip()!=IMAGE+" linux/arm64":raise RuntimeError("pinned image/platform mismatch")
    inventory=run(["docker","--context",CONTEXT,"ps","--quiet"])
    if inventory.returncode:raise RuntimeError("cannot verify OrbStack container inventory: "+inventory.stderr)
    if inventory.stdout.strip():raise RuntimeError("OrbStack shared lane is occupied")
    out.parent.mkdir(parents=True,exist_ok=True);out.mkdir()
    source_mount=str(REPO.resolve());output_mount=str(out.resolve())
    audit_input_mount=str((out/"audit-input").resolve())
    audit_output_mount=str((out/"audit-output").resolve())
    expected_mounts=[{"Type":"bind","Source":source_mount,"Destination":"/src","RW":False},
                     {"Type":"bind","Source":output_mount,"Destination":"/out","RW":True}]
    expected_auditor_mounts=[{"Type":"bind","Source":source_mount,"Destination":"/src","RW":False},
                     {"Type":"bind","Source":audit_input_mount,"Destination":"/in","RW":False},
                     {"Type":"bind","Source":audit_output_mount,"Destination":"/out","RW":True}]
    env={"OBSTAC_SOURCE_COMMIT":commit,"OBSTAC_IMAGE_ID":IMAGE,
         "OBSTAC_FREEZE_SHA256":sha((EXP/"FREEZE.json").read_bytes()),"OBSTAC_CONSTRUCTION":"0"}
    exp_container="/src/"+str(EXP.relative_to(REPO))
    cname="unjuno5134-formal-"+commit[:8];aname="unjuno5134-audit-"+commit[:8]
    limits=["--pull=never","--platform","linux/arm64","--network","none","--read-only","--cpus","0.25",
            "--memory","512m","--pids-limit","32","--shm-size","32m","--cap-drop","ALL",
            "--security-opt","no-new-privileges"]
    formal_mount_args=["--mount",f"type=bind,source={source_mount},target=/src,readonly",
                       "--mount",f"type=bind,source={output_mount},target=/out"]
    audit_mount_args=["--mount",f"type=bind,source={source_mount},target=/src,readonly",
                      "--mount",f"type=bind,source={audit_input_mount},target=/in,readonly",
                      "--mount",f"type=bind,source={audit_output_mount},target=/out"]
    envargs=[v for k,value in env.items() for v in ("-e",f"{k}={value}")]
    fargv=["docker","--context",CONTEXT,"run","--name",cname,*limits,*formal_mount_args,*envargs,IMAGE,"python","-B",exp_container+"/runner.py"]
    aargv=["docker","--context",CONTEXT,"run","--name",aname,*limits,*audit_mount_args,*envargs,IMAGE,"python","-B",exp_container+"/audit.py"]
    receipt={"allocation":ALLOCATION,"source_commit":commit,
             "slot_release":slot_release,
             "source_tree_sha":tree,"source_sha256":source_actual,"source_blob_sha256":blob_ids,
             "live_main_sha":live_main_sha,
             "seed_blob":"45b80150dac503f4eb6f3cb5d82f9afa2c587107","seed_sha256":sha(SEED.read_bytes()),
             "freeze_sha256":env["OBSTAC_FREEZE_SHA256"],"image_id":IMAGE,"image_platform":"linux/arm64",
             "construction":"0","environment":env,"source_mount":source_mount,"output_mount":output_mount,
             "mounts":expected_mounts,"auditor_mounts":expected_auditor_mounts,
             "audit_input_mount":audit_input_mount,"audit_output_mount":audit_output_mount,
             "docker_context":CONTEXT,"docker_argv":fargv,"auditor_docker_argv":aargv,
             "formal_container_name":cname,"auditor_container_name":aname,
             "resource_limits":{"cpus":"0.25","memory":"512m","pids":32,"network":"none","root_read_only":True,
                               "source_read_only":True,"cap_drop":"ALL","no_new_privileges":True}}
    receipt_path=out/"invocation_receipt.json";write_json(receipt_path,receipt)
    started=time.time_ns();formal=run(fargv)
    (out/"formal.stdout.txt").write_text(formal.stdout);(out/"formal.stderr.txt").write_text(formal.stderr)
    formal_inspect=inspect_container(cname)
    receipt["formal_container_inspect"]={"Id":formal_inspect["Id"],"Image":formal_inspect["Image"],
         "State":formal_inspect["State"],"Mounts":formal_inspect["Mounts"],"ConfigImage":formal_inspect["Config"]["Image"]}
    write_json(receipt_path,receipt)
    expected_actual={m["Destination"]:m for m in formal_inspect["Mounts"]}
    if set(expected_actual)!={"/src","/out"} or any(expected_actual[m["Destination"]].get("Source")!=m["Source"] or
       bool(expected_actual[m["Destination"]].get("RW"))!=m["RW"] for m in expected_mounts):
        raise RuntimeError("actual formal container mounts differ from frozen receipt")
    if formal.returncode==0 and (out/"raw.json").is_file():
        audit_input=out/"audit-input";audit_output=out/"audit-output"
        audit_input.mkdir();audit_output.mkdir()
        for name in ("raw.json","invocation_receipt.json"):
            (audit_input/name).write_bytes((out/name).read_bytes())
        write_json(audit_input/"input_manifest.json",{"files":{name:sha((audit_input/name).read_bytes()) for name in ("raw.json","invocation_receipt.json")}})
        receipt["auditor_mounts"]=expected_auditor_mounts
        receipt["audit_input_mount"]=audit_input_mount
        receipt["audit_output_mount"]=audit_output_mount
        receipt["auditor_docker_argv"]=aargv
        write_json(audit_input/"invocation_receipt.json",receipt)
        write_json(audit_input/"input_manifest.json",{"files":{name:sha((audit_input/name).read_bytes()) for name in ("raw.json","invocation_receipt.json")}})
        auditor=run(aargv);(out/"audit.stdout.txt").write_text(auditor.stdout);(out/"audit.stderr.txt").write_text(auditor.stderr)
        audit_inspect=inspect_container(aname)
    else:auditor=None;audit_inspect=None
    audit_mounts_ok=False
    if audit_inspect:
        actual={m.get("Destination"):m for m in audit_inspect.get("Mounts",[]) if isinstance(m,dict)}
        audit_mounts_ok=set(actual)=={"/src","/in","/out"} and all(
            actual[name].get("Source")==want["Source"] and bool(actual[name].get("RW"))==want["RW"]
            for name,want in (("/src",expected_auditor_mounts[0]),("/in",expected_auditor_mounts[1]),("/out",expected_auditor_mounts[2])))
    execution={"allocation":receipt["allocation"],"formal_exit":formal.returncode,
               "audit_exit":auditor.returncode if auditor else None,"started_ns":started,"finished_ns":time.time_ns(),
               "formal_container_id":formal_inspect["Id"],"formal_container_state":formal_inspect["State"],
               "formal_mounts":formal_inspect["Mounts"],"auditor_container_id":audit_inspect["Id"] if audit_inspect else None,
               "auditor_container_state":audit_inspect["State"] if audit_inspect else None,
               "auditor_mounts":audit_inspect["Mounts"] if audit_inspect else None,
               "receipt_sha256":sha(receipt_path.read_bytes()),"docker_context":CONTEXT,"host_platform":platform.platform()}
    write_json(out/"execution.json",execution)
    manifest={str(p.relative_to(out)):{"bytes":p.stat().st_size,"sha256":sha(p.read_bytes())}
              for p in sorted(out.rglob("*")) if p.is_file() and p.name!="manifest.json"}
    write_json(out/"manifest.json",manifest)
    print(json.dumps({"formal_exit":formal.returncode,"audit_exit":auditor.returncode if auditor else None,
                      "output":str(out),"raw_sha256":manifest.get("raw.json",{}).get("sha256"),
                      "audit_sha256":manifest.get("audit.json",{}).get("sha256")},sort_keys=True))
    return 0 if auditor and auditor.returncode==0 and audit_mounts_ok else 1


if __name__=="__main__":
    try:raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({"preflight_error":type(exc).__name__,"error":str(exc)},sort_keys=True),file=sys.stderr);raise
