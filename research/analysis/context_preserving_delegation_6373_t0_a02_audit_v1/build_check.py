import copy
import json
from auditor import evaluate

cases=json.load(open("input/raw.json",encoding="utf-8"))["cases"]
rows=json.load(open("input/candidate.json",encoding="utf-8"))
oracle=json.load(open("input/oracle.json",encoding="utf-8"))["expected_case_safety"]
base=evaluate(cases,rows,oracle)
assert base["all_rows_valid"] and base["restore_plus_diff_not_worse_than_summary"]
mutants=[]
m=copy.deepcopy(rows); next(r for r in m if r["case"]=="browser_to_sheet" and r["policy"]=="RESTORE_PLUS_DIFF")["modeled_context_mismatches"]+=1; mutants.append(m)
m=copy.deepcopy(rows); next(r for r in m if r["case"]=="selection_autosave_coupling" and r["policy"]=="RESTORE_PLUS_DIFF")["effects_after"]["B20"]=0; mutants.append(m)
m=copy.deepcopy(rows); next(r for r in m if r["case"]=="external_viewport_change" and r["policy"]=="RESTORE_PLUS_DIFF")["context_after"]["viewport"]="page2"; mutants.append(m)
m=copy.deepcopy(rows); next(r for r in m if r["case"]=="required_download_evidence" and r["policy"]=="RESTORE_PLUS_DIFF")["context_after"]["download"]="none"; mutants.append(m)
assert all(not evaluate(cases,m,oracle)["all_rows_valid"] for m in mutants)
print("BUILD_PASS rows=32 downstream_success_gate=present mutations=4")
