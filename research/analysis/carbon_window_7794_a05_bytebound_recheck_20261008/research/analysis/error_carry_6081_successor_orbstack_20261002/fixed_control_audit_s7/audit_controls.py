import hashlib, json, sys
from pathlib import Path

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main(raw_path,s5_path,out_path):
    if sha(raw_path)!="81e8e0f9d34de42272744a3793162fe0cb857c77b8e67f28108f28dfc4bc8e49": raise SystemExit("STOP_RAW_HASH")
    if sha(s5_path)!="247f2e27a9a7661f5dc9520d1ce547605485f0652016e50f4bbccee02b74a584": raise SystemExit("STOP_RECONSTRUCTION_RECEIPT_HASH")
    raw=json.loads(Path(raw_path).read_text()); s5=json.loads(Path(s5_path).read_text())
    if len(raw.get("rows",[]))!=80 or s5.get("reconstructed_rows")!=80 or s5.get("independent_reconstruction")!="EXACT_MATCH": raise SystemExit("STOP_RECONSTRUCTION_RECEIPT")
    ix={(r["action_set"],r["case"],r["policy"]):r["result"] for r in raw["rows"]}
    policies=("A_HORIZON_NEAREST","B_SLOT_NEAREST","C_ERROR_CARRY","D_RELEASE")
    checks={}; errors=[]
    def check(label, predicate):
        checks[label]=bool(predicate)
        if not predicate: errors.append(label)
    for alphabet in ("4way","8way"):
        for p in policies[:3]:
            east=ix[(alphabet,"exact-east",p)]
            check(f"{alphabet}/{p}/exact-east",east.get("status")=="SCHEDULED" and east.get("moves")==[["1","0"]]*4 and east.get("positions")==[[str(k),"0"] for k in range(1,5)] and east.get("prefix_error_sq")==["0"]*4 and east.get("release") is True and east.get("envelope_violations")==0)
            zero=ix[(alphabet,"zero",p)]
            check(f"{alphabet}/{p}/zero",zero.get("status")=="SCHEDULED" and zero.get("moves")==[["0","0"]]*5 and zero.get("positions")==[["0","0"]]*5 and zero.get("prefix_error_sq")==["0"]*5 and zero.get("release") is True and zero.get("switches")==0)
    for p in policies:
        refusal=ix[("4way","outside-4way-hull",p)]
        check(f"4way/{p}/outside-hull-refusal",refusal.get("status")=="REFUSE_OUTSIDE_HULL" and refusal.get("moves")==[] and refusal.get("release") is True)
        unknown=ix[("8way","unknown-calibration",p)]
        check(f"8way/{p}/unknown-calibration-refusal",unknown.get("status")=="REFUSE_UNKNOWN_CALIBRATION" and unknown.get("moves")==[] and unknown.get("release") is True)
    diagonal=ix[("8way","diagonal","C_ERROR_CARRY")]
    check("8way/C/exact-diagonal-terminal",diagonal.get("status")=="SCHEDULED" and diagonal.get("positions",[])[-1:]==[["2","2"]] and diagonal.get("terminal_error_sq")=="0" and diagonal.get("release") is True)
    result={"status":"PASS_FIXED_CONTROLS" if not errors else "FAIL_FIXED_CONTROLS",
            "checks_passed":sum(checks.values()),"checks_total":len(checks),"failures":errors,
            "source_raw_sha256":sha(raw_path),"source_audit_sha256":sha(s5_path),
            "scope":"formal exact/zero/refusal controls in the frozen synthetic fixture only"}
    Path(out_path).write_text(json.dumps(result,sort_keys=True,indent=2)+"\n")
    if errors: raise SystemExit("FAIL_FIXED_CONTROLS")
if __name__=="__main__": main(sys.argv[1],sys.argv[2],sys.argv[3])
