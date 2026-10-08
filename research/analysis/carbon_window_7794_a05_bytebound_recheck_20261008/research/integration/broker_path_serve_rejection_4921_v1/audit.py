"""Independent raw-only audit for #4921; imports neither runner nor candidate policy."""
from __future__ import annotations
import copy, json, sys
from pathlib import Path
from urllib.parse import unquote

def schedule():
    out=[("valid_repo",None,"valid_repo"),("valid_workspace",None,"valid_workspace")]
    for field in ("schema","image","working"):
        out.append((field+"_inside_symlink",field,"inside_symlink"))
        for kind in ("traversal","encoded_traversal","absolute","missing","external_symlink","ambiguous_separator"):
            out.append((field+"_"+kind,field,kind))
    return out

def resolve_independent(value, root):
    if value in ("/repo","/workspace"): return str(root.resolve(strict=True))
    prefix="/repo/" if value.startswith("/repo/") else "/workspace/" if value.startswith("/workspace/") else None
    if prefix is None: raise ValueError("unscoped")
    rel=value[len(prefix):]
    for _ in range(4):
        nxt=unquote(rel)
        if nxt==rel: break
        rel=nxt
    if "\\" in rel or "\x00" in rel: raise ValueError("separator")
    parts=rel.split("/")
    if any(x in ("",".","..") for x in parts): raise ValueError("components")
    resolved=(root.resolve(strict=True).joinpath(*parts)).resolve(strict=True)
    resolved.relative_to(root.resolve(strict=True))
    return str(resolved)

def argv_paths(args):
    out={}
    for flag,key in (("--output-schema","schema"),("--image","image"),("-C","working")):
        i=args.index(flag); out[key]=args[i+1]
    return out

def audit_rows(raw):
    rows=raw["rows"]; sched=schedule()
    if len(rows)!=len(sched): raise ValueError("row_count")
    by_id={r["case_id"]:r for r in rows}
    if len(by_id)!=len(rows) or set(by_id)!={x[0] for x in sched}: raise ValueError("case_identity")
    root=Path(raw["repo_root"])
    for case_id,field,kind in sched:
        row=by_id[case_id]; accept=kind in ("valid_repo","valid_workspace","inside_symlink")
        if row["expected"] != ("accept" if accept else "reject"): raise ValueError("expectation")
        if row["broker_receipt_count"]!=1 or not row["response_exists"]: raise ValueError("receipt_count")
        receipt=row["receipt"]
        if receipt.get("request_id") != row.get("request_id"): raise ValueError("request_id")
        if receipt.get("authority_granted") is not False: raise ValueError("authority")
        if accept:
            if row["exit_code"]!=0 or receipt.get("returncode")!=0 or receipt.get("error_class") is not None: raise ValueError("accepted_receipt")
            if len(row["subprocess_calls"])!=1: raise ValueError("accepted_call_count")
            got=argv_paths(row["subprocess_calls"][0])
            for key,value in row["path_values"].items():
                expected=resolve_independent(value,root)
                if got[key]!=expected: raise ValueError("accepted_mapping_"+key)
        else:
            if row["exit_code"]!=1 or receipt.get("returncode") is not None: raise ValueError("rejected_returncode")
            if receipt.get("error_class")!="InvalidHostPath" or receipt.get("stop_reason")!="HOST_MODEL_PATH_REJECTED": raise ValueError("rejection_receipt")
            if len(row["subprocess_calls"])!=0: raise ValueError("rejected_reached_subprocess")
            try: resolve_independent(row["path_values"][field],root)
            except (ValueError,OSError): pass
            else: raise ValueError("invalid_case_resolves")
    if raw.get("formal_runner_invocations")!=1 or raw.get("retries")!=0: raise ValueError("allocation_count")
    return {"rows":len(rows),"accepted":5,"rejected":18,"errors":[]}

def controls(raw):
    tests=[]
    cases=[]
    for name,mutate in (
       ("missing_row",lambda x:x["rows"].pop()),
       ("authority_flip",lambda x:x["rows"][0]["receipt"].update(authority_granted=True)),
       ("rejected_subprocess",lambda x:next(r for r in x["rows"] if r["field"]=="schema" and r["class"]=="absolute")["subprocess_calls"].append(["codex.exe"])),
       ("invalid_receipt_flip",lambda x:next(r for r in x["rows"] if r["field"]=="schema" and r["class"]=="absolute")["receipt"].update(returncode=0)),
       ("duplicate_row",lambda x:x["rows"].append(copy.deepcopy(x["rows"][0])))):
        altered=copy.deepcopy(raw); mutate(altered)
        rejected=False
        try: audit_rows(altered)
        except (ValueError,KeyError,IndexError): rejected=True
        cases.append({"name":name,"rejected":rejected})
    if not all(x["rejected"] for x in cases): raise ValueError("corruption_control")
    return {"total":len(cases),"rejected":sum(x["rejected"] for x in cases),"controls":cases}

def main(src,dest):
    raw=json.loads(Path(src).read_text())
    summary=audit_rows(raw); mutation=controls(raw)
    result={"schema":"broker-path-serve-rejection-4921-audit-v1","decision":"PASS_INDEPENDENT_AUDIT",
            "summary":summary,"corruption_controls":mutation}
    Path(dest).write_text(json.dumps(result,sort_keys=True,indent=2)+"\n")
if __name__=="__main__":
    if len(sys.argv)!=3: raise SystemExit("usage: audit.py RAW.json AUDIT.json")
    main(sys.argv[1],sys.argv[2])
