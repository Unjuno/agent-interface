from __future__ import annotations
import argparse, ast, copy, hashlib, json
from pathlib import Path

EXPECTED_ORDER = [
    "SETUP_DOCTOR", "MODEL_ATTEMPT", "OBSERVATION", "GUARDED_DISPATCH",
    "REFUSAL", "USEFUL_EFFECT", "STALE_INVALIDATION", "REPAIR",
    "TERMINAL_RELEASE", "CLEANUP_FAILURE",
]
EXPECTED_ROLES = {
    "runtime/golden_desktop_demo_v3.py": {"doctor", "run_live", "schema"},
    "runtime/cli_v1/api.py": {"doctor", "dispatch", "cleanup"},
    "runtime/core_v1/__init__.py": {"admission", "release"},
    "runtime/GOLDEN_DESKTOP_DEMO_V3.md": {"retained_result", "scope_limits"},
}
EXPECTED_OLD_API = "f9dc26441c5f4ff9d7f57aa6a6a7b3849a1537d7"
EXPECTED_NEW_API = "47193afd3bdb5e8bef91bf539f74f180ce9b9406"

def git_blob_sha(data: bytes) -> str:
    return hashlib.sha1(f"blob {len(data)}\0".encode("ascii") + data).hexdigest()

def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))

def function_names(source: str):
    return {n.name for n in ast.walk(ast.parse(source)) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}

def validate(repo: Path, manifest: dict, result: dict, predecessor_manifest: dict, predecessor_result: dict):
    errors=[]
    sources=manifest.get("sources")
    psources=predecessor_manifest.get("sources")
    if not isinstance(sources,list) or len(sources)!=4: errors.append("source_count")
    if not isinstance(psources,list) or len(psources)!=4: errors.append("predecessor_source_count")
    if errors: return errors
    by={x.get("path"):x for x in sources}
    pby={x.get("path"):x for x in psources}
    if set(by)!=set(EXPECTED_ROLES): errors.append("source_set")
    if set(pby)!=set(EXPECTED_ROLES): errors.append("predecessor_source_set")
    for p, roles in EXPECTED_ROLES.items():
        if p not in by or set(by[p].get("roles",[]))!=roles: errors.append("roles:"+p)
        if p not in pby or set(pby[p].get("roles",[]))!=roles: errors.append("predecessor_roles:"+p)
        f=repo/p
        if not f.is_file():
            errors.append("missing:"+p); continue
        if git_blob_sha(f.read_bytes()) != by[p].get("blob_sha"): errors.append("blob:"+p)
    changes=[]
    for p in EXPECTED_ROLES:
        if p in by and p in pby and by[p].get("blob_sha")!=pby[p].get("blob_sha"):
            changes.append((p,pby[p].get("blob_sha"),by[p].get("blob_sha")))
    if changes != [("runtime/cli_v1/api.py",EXPECTED_OLD_API,EXPECTED_NEW_API)]: errors.append("rebind_scope")

    try:
        golden=(repo/"runtime/golden_desktop_demo_v3.py").read_text(encoding="utf-8")
        api=(repo/"runtime/cli_v1/api.py").read_text(encoding="utf-8")
        core=(repo/"runtime/core_v1/__init__.py").read_text(encoding="utf-8")
        doc=(repo/"runtime/GOLDEN_DESKTOP_DEMO_V3.md").read_text(encoding="utf-8")
        if not {"doctor","run_live","main"} <= function_names(golden): errors.append("golden_roles")
        if not {"doctor","dispatch"} <= function_names(api): errors.append("api_roles")
        if '"side_effect_authority": False' not in api: errors.append("api_authority_diagnostic")
        if "finally:" not in api or "close = getattr" not in api or "cleanup_error" not in api: errors.append("api_cleanup")
        if not all(x in core for x in ("admit_program","required_capabilities","validate_program")): errors.append("core_roles")
        if "First frozen allocation" not in doc or "All 57 terminal" not in doc: errors.append("retained_result_scope")
    except (OSError, SyntaxError, UnicodeError) as e: errors.append("source_parse:"+type(e).__name__)

    if result.get("status") != "PASS_DESKTOP_VERTICAL_SLICE_REBOUND_AUDIT_SCOPED": errors.append("status")
    if result.get("lifecycle_rows") != 10: errors.append("lifecycle_rows")
    rows=result.get("rows_detail")
    prows=predecessor_result.get("rows_detail")
    if not isinstance(rows,list) or [x.get("state") for x in rows] != EXPECTED_ORDER: errors.append("row_order")
    if rows != prows: errors.append("rows_changed")
    for key in ("authority_grants","model_calls","gui_calls","input_calls","network_calls"):
        if result.get(key) != 0: errors.append(key)
    if result.get("source_changes") != [{"path":"runtime/cli_v1/api.py","old_blob":EXPECTED_OLD_API,"new_blob":EXPECTED_NEW_API}]: errors.append("result_source_changes")
    return errors

def run_controls(repo,manifest,result,pmanifest,presult):
    controls=[]
    def expect(name,m,r,pm=pmanifest,pr=presult):
        errs=validate(repo,m,r,pm,pr)
        controls.append({"name":name,"rejected":bool(errs),"errors":errs})
    m=copy.deepcopy(manifest); m["sources"][0]["blob_sha"]="0"*40; expect("changed_source_hash",m,copy.deepcopy(result))
    m=copy.deepcopy(manifest); m["sources"].append({"path":"extra.py","blob_sha":"0"*40,"roles":[]}); expect("undeclared_source",m,copy.deepcopy(result))
    m=copy.deepcopy(manifest); m["sources"][1]["roles"].append("authority"); expect("role_mutation",m,copy.deepcopy(result))
    r=copy.deepcopy(result); r["rows_detail"][4]["state"]="SUCCESS"; expect("lifecycle_row_mutation",copy.deepcopy(manifest),r)
    r=copy.deepcopy(result); r["authority_grants"]=1; expect("authority_count_mutation",copy.deepcopy(manifest),r)
    return controls

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--repo",type=Path,required=True)
    ap.add_argument("--manifest",type=Path,required=True)
    ap.add_argument("--result",type=Path,required=True)
    ap.add_argument("--predecessor-manifest",type=Path,required=True)
    ap.add_argument("--predecessor-result",type=Path,required=True)
    ap.add_argument("--controls",action="store_true")
    a=ap.parse_args()
    m,r,pm,pr=map(load,(a.manifest,a.result,a.predecessor_manifest,a.predecessor_result))
    errors=validate(a.repo,m,r,pm,pr)
    controls=run_controls(a.repo,m,r,pm,pr) if a.controls else []
    if a.controls and any(not x["rejected"] for x in controls): errors.append("control_not_rejected")
    out={"decision":"PASS_DESKTOP_VERTICAL_SLICE_REBOUND_AUDIT_SCOPED" if not errors else "FAIL_AUDIT",
         "errors":errors,"controls":controls,"checks":{"sources":4,"lifecycle_rows":10,"authority_grants":r.get("authority_grants")}}
    print(json.dumps(out,sort_keys=True,separators=(",",":")))
    raise SystemExit(0 if not errors else 1)
if __name__=="__main__": main()
