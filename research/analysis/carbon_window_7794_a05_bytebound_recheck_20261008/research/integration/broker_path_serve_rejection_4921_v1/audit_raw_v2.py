"""Posthoc independent raw-only audit-v2 for #4921; never replays serve() or imports candidate code."""
from __future__ import annotations
import copy,json,sys
from pathlib import Path,PurePosixPath
from urllib.parse import unquote

def schedule():
    out=[("valid_repo",None,"valid_repo"),("valid_workspace",None,"valid_workspace")]
    for field in ("schema","image","working"):
        out.append((field+"_inside_symlink",field,"inside_symlink"))
        for kind in ("traversal","encoded_traversal","absolute","missing","external_symlink","ambiguous_separator"):
            out.append((field+"_"+kind,field,kind))
    return out

def expected_path(value,root,kind,field):
    if kind=="inside_symlink":
        target={"schema":"schema.json","image":"image.png","working":"work"}[field]
        return str(PurePosixPath(root)/target)
    if value in ("/repo","/workspace"): return str(PurePosixPath(root))
    prefix="/repo/" if value.startswith("/repo/") else "/workspace/" if value.startswith("/workspace/") else None
    if prefix is None: raise ValueError("unscoped")
    rel=value[len(prefix):]
    for _ in range(4):
        nxt=unquote(rel)
        if nxt==rel: break
        rel=nxt
    if "\\" in rel or "\x00" in rel: raise ValueError("separator")
    parts=rel.split("/")
    if any(x in ("",".","..") for x in parts): raise ValueError("component")
    if kind=="missing" and rel=="not-present": raise ValueError("missing fixture target")
    if kind=="external_symlink" and rel in ("escape_file","escape_image","escape_dir"):
        raise ValueError("frozen fixture maps symlink outside root")
    return str(PurePosixPath(root).joinpath(*parts))

def argv_paths(args):
    return {key:args[args.index(flag)+1] for flag,key in
            (("--output-schema","schema"),("--image","image"),("-C","working"))}

def audit_rows(raw):
    rows=raw["rows"]; sched=schedule()
    if len(rows)!=23: raise ValueError("row_count")
    by={r["case_id"]:r for r in rows}
    if len(by)!=len(rows) or set(by)!={x[0] for x in sched}: raise ValueError("case_identity")
    root=raw["repo_root"]
    for case_id,field,kind in sched:
        row=by[case_id]; accepted=kind in ("valid_repo","valid_workspace","inside_symlink")
        if row.get("field")!=field or row.get("class")!=kind: raise ValueError("case_binding")
        if row.get("expected")!=("accept" if accepted else "reject"): raise ValueError("expected_label")
        if row.get("request_id") != row.get("receipt",{}).get("request_id"): raise ValueError("request_id")
        if row.get("broker_receipt_count")!=1 or not row.get("response_exists"): raise ValueError("receipt_count")
        receipt=row["receipt"]
        if receipt.get("authority_granted") is not False: raise ValueError("authority")
        if accepted:
            if row.get("exit_code")!=0 or receipt.get("returncode")!=0 or receipt.get("error_class") is not None: raise ValueError("accept_receipt")
            calls=row.get("subprocess_calls",[])
            if len(calls)!=1: raise ValueError("accept_call_count")
            got=argv_paths(calls[0])
            for key,value in row["path_values"].items():
                if got[key]!=expected_path(value,root,kind if key==field else "valid",key): raise ValueError("argv_mapping_"+key)
        else:
            if row.get("exit_code")!=1 or receipt.get("returncode") is not None: raise ValueError("reject_returncode")
            if receipt.get("error_class")!="InvalidHostPath" or receipt.get("stop_reason")!="HOST_MODEL_PATH_REJECTED": raise ValueError("reject_receipt")
            if row.get("subprocess_calls")!=[]: raise ValueError("reject_called_subprocess")
            try: expected_path(row["path_values"][field],root,kind,field)
            except ValueError: pass
            else: raise ValueError("invalid_path_not_rejected_by_policy")
    if raw.get("formal_runner_invocations")!=1 or raw.get("retries")!=0: raise ValueError("allocation_count")
    return {"rows":23,"accepted":5,"rejected":18,"errors":[]}

def corruption_controls(raw):
    changes=[
      ("missing_row",lambda x:x["rows"].pop()),
      ("authority_flip",lambda x:x["rows"][0]["receipt"].update(authority_granted=True)),
      ("rejected_subprocess",lambda x:next(r for r in x["rows"] if r["case_id"]=="schema_absolute")["subprocess_calls"].append(["mock"])),
      ("invalid_receipt_flip",lambda x:next(r for r in x["rows"] if r["case_id"]=="schema_absolute")["receipt"].update(returncode=0)),
      ("duplicate_row",lambda x:x["rows"].append(copy.deepcopy(x["rows"][0]))),
      ("accepted_call_missing",lambda x:next(r for r in x["rows"] if r["case_id"]=="valid_repo")["subprocess_calls"].clear())]
    results=[]
    for name,mutate in changes:
        changed=copy.deepcopy(raw); mutate(changed); rejected=False
        try: audit_rows(changed)
        except (ValueError,KeyError,IndexError): rejected=True
        results.append({"name":name,"rejected":rejected})
    if not all(x["rejected"] for x in results): raise ValueError("corruption_controls")
    return {"total":len(results),"rejected":sum(x["rejected"] for x in results),"controls":results}

def main(src,dest):
    raw=json.loads(Path(src).read_text())
    summary=audit_rows(raw); controls=corruption_controls(raw)
    output={"schema":"broker-path-serve-rejection-4921-audit-v2","decision":"PASS_INDEPENDENT_AUDIT_RAW_SCOPED",
      "summary":summary,"corruption_controls":controls,
      "limitations":["raw-only recomputation; temporary fixture tree was not retained for post-run lstat/readlink verification","in-root symlink destinations are checked against the frozen runner's declared fixture mapping"]}
    Path(dest).write_text(json.dumps(output,sort_keys=True,indent=2)+"\n")
if __name__=="__main__":
    if len(sys.argv)!=3: raise SystemExit("usage: audit_raw_v2.py RAW.json AUDIT.json")
    main(sys.argv[1],sys.argv[2])
