"""Independent durable-fixture and raw broker receipt audit for #4937."""
from __future__ import annotations
import copy,hashlib,json,os,stat,sys
from pathlib import Path,PurePosixPath
from urllib.parse import unquote

def schedule():
    out=[("valid_repo",None,"valid_repo"),("valid_workspace",None,"valid_workspace")]
    for field in ("schema","image","working"):
        out.append((field+"_inside_symlink",field,"inside_symlink"))
        for kind in ("traversal","encoded_traversal","absolute","missing","external_symlink","ambiguous_separator"):
            out.append((field+"_"+kind,field,kind))
    return out

def inventory(base):
    result=[]
    for cur,dirs,files in os.walk(base,followlinks=False):
        for name in sorted(dirs+files):
            p=Path(cur)/name; st=p.lstat(); rel=p.relative_to(base).as_posix()
            if stat.S_ISLNK(st.st_mode): kind="symlink"; target=os.readlink(p); digest=None
            elif stat.S_ISDIR(st.st_mode): kind="directory"; target=None; digest=None
            elif stat.S_ISREG(st.st_mode): kind="file"; target=None; digest=hashlib.sha256(p.read_bytes()).hexdigest()
            else: kind="other"; target=None; digest=None
            result.append({"path":rel,"kind":kind,"size":st.st_size,"link_target":target,"sha256":digest})
    return sorted(result,key=lambda x:x["path"])

def resolve_independent(value,root):
    if value in ("/repo","/workspace"): return str(Path(root).resolve(strict=True))
    prefix="/repo/" if value.startswith("/repo/") else "/workspace/" if value.startswith("/workspace/") else None
    if prefix is None: raise ValueError("unscoped absolute path")
    rel=value[len(prefix):]
    for _ in range(4):
        nxt=unquote(rel)
        if nxt==rel: break
        rel=nxt
    if "\\" in rel or "\x00" in rel: raise ValueError("ambiguous separator")
    parts=rel.split("/")
    if any(x in ("",".","..") for x in parts): raise ValueError("traversal/noncanonical")
    resolved=(Path(root).resolve(strict=True).joinpath(*parts)).resolve(strict=True)
    resolved.relative_to(Path(root).resolve(strict=True))
    return str(resolved)

def argv_paths(args):
    return {key:args[args.index(flag)+1] for flag,key in (("--output-schema","schema"),("--image","image"),("-C","working"))}

def audit(raw,manifest,check_fs=True):
    rows=raw["rows"]; sched=schedule()
    if len(rows)!=23: raise ValueError("row_count")
    by={r["case_id"]:r for r in rows}
    if len(by)!=23 or set(by)!={c[0] for c in sched}: raise ValueError("case_identity")
    if raw.get("formal_runner_invocations")!=1 or raw.get("retries")!=0: raise ValueError("allocation_count")
    if raw.get("fixture_unchanged_during_run") is not True or manifest.get("initial_equals_final") is not True: raise ValueError("fixture_changed")
    manifest_bytes=(json.dumps(manifest,sort_keys=True,indent=2)+"\n").encode()
    if hashlib.sha256(manifest_bytes).hexdigest()!=raw.get("fixture_manifest_sha256"): raise ValueError("manifest_digest")
    base=Path(raw["fixture_base"]); root=Path(raw["repo_root"]); outside=Path(raw["outside_root"])
    if str(base)!=manifest.get("base") or str(root)!=manifest.get("repo_root") or str(outside)!=manifest.get("outside_root"): raise ValueError("fixture_roots")
    if check_fs:
        actual=inventory(base)
        if actual!=manifest.get("entries"): raise ValueError("fixture_inventory")
        if not root.is_dir() or not outside.is_dir(): raise ValueError("fixture_roots_missing")
        for name,target in (("inside_file",root/"schema.json"),("inside_image",root/"image.png"),("inside_dir",root/"work")):
            p=root/name
            if not p.is_symlink() or Path(os.readlink(p)).resolve(strict=True)!=target.resolve(strict=True): raise ValueError("inroot_link_"+name)
        for name,target in (("escape_file",outside/"schema.json"),("escape_image",outside/"image.png"),("escape_dir",outside/"work")):
            p=root/name
            if not p.is_symlink() or Path(os.readlink(p)).resolve(strict=True)!=target.resolve(strict=True): raise ValueError("external_link_"+name)
    for case_id,field,kind in sched:
        row=by[case_id]; accept=kind in ("valid_repo","valid_workspace","inside_symlink")
        if row.get("field")!=field or row.get("class")!=kind: raise ValueError("row_binding")
        if row.get("expected")!=("accept" if accept else "reject"): raise ValueError("expected_label")
        receipt=row.get("receipt",{})
        if receipt.get("request_id")!=row.get("request_id") or row.get("broker_receipt_count")!=1 or not row.get("response_exists"): raise ValueError("receipt_identity")
        if receipt.get("authority_granted") is not False: raise ValueError("authority")
        if accept:
            if row.get("exit_code")!=0 or receipt.get("returncode")!=0 or receipt.get("error_class") is not None: raise ValueError("accept_receipt")
            calls=row.get("subprocess_calls",[])
            if len(calls)!=1: raise ValueError("accept_call")
            got=argv_paths(calls[0])
            for key,value in row["path_values"].items():
                expected=resolve_independent(value,root)
                if got[key]!=expected: raise ValueError("accept_mapping_"+key)
        else:
            if row.get("exit_code")!=1 or receipt.get("returncode") is not None: raise ValueError("reject_returncode")
            if receipt.get("error_class")!="InvalidHostPath" or receipt.get("stop_reason")!="HOST_MODEL_PATH_REJECTED": raise ValueError("reject_receipt")
            if row.get("subprocess_calls")!=[]: raise ValueError("invalid_reached_subprocess")
            try: resolve_independent(row["path_values"][field],root)
            except (ValueError,OSError): pass
            else: raise ValueError("invalid_path_accepted")
    return {"rows":23,"accepted":5,"rejected":18,"errors":[]}

def controls(raw,manifest):
    variants=[
      ("missing_raw_row",lambda r,m:r["rows"].pop()),
      ("authority_flip",lambda r,m:r["rows"][0]["receipt"].update(authority_granted=True)),
      ("invalid_subprocess_call",lambda r,m:next(x for x in r["rows"] if x["case_id"]=="schema_absolute")["subprocess_calls"].append(["mock"])),
      ("invalid_receipt_flip",lambda r,m:next(x for x in r["rows"] if x["case_id"]=="schema_absolute")["receipt"].update(returncode=0)),
      ("fixture_link_target",lambda r,m:next(x for x in m["entries"] if x["path"]=="repo/inside_file").update(link_target="/outside/escape")),
      ("fixture_inventory_missing",lambda r,m:m["entries"].pop()),
      ("fixture_changed_claim",lambda r,m:r.update(fixture_unchanged_during_run=False))]
    result=[]
    for name,mutate in variants:
        r=copy.deepcopy(raw);m=copy.deepcopy(manifest);mutate(r,m);rejected=False
        try:audit(r,m,check_fs=True)
        except (ValueError,KeyError,IndexError,OSError):rejected=True
        result.append({"name":name,"rejected":rejected})
    if not all(x["rejected"] for x in result):raise ValueError("corruption_controls")
    return {"total":len(result),"rejected":sum(x["rejected"] for x in result),"controls":result}

def main(raw_path,manifest_path,out_path):
    raw=json.loads(Path(raw_path).read_text()); manifest=json.loads(Path(manifest_path).read_text())
    summary=audit(raw,manifest); mutations=controls(raw,manifest)
    result={"schema":"broker-path-durable-fixture-4937-audit-v1","decision":"PASS_DURABLE_FIXTURE_SERVE_REJECTION_SCOPED",
      "summary":summary,"corruption_controls":mutations,"fixture_manifest_sha256":raw["fixture_manifest_sha256"]}
    Path(out_path).write_text(json.dumps(result,sort_keys=True,indent=2)+"\n")
if __name__=="__main__":
    if len(sys.argv)!=4:raise SystemExit("usage: audit_raw.py RAW.json FIXTURE_MANIFEST.json AUDIT.json")
    main(sys.argv[1],sys.argv[2],sys.argv[3])
