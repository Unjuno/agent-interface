#!/usr/bin/env python3
"""Fail closed unless current run is the unique earliest run for one workflow allocation."""
from __future__ import annotations
import argparse,json
from pathlib import Path
from typing import Any

def _rows(payload:Any):
    if isinstance(payload,list): return payload,None
    if isinstance(payload,dict) and isinstance(payload.get('workflow_runs'),list):
        total=payload.get('total_count')
        if total is not None and type(total) is not int: raise ValueError('total_count must be int')
        return payload['workflow_runs'],total
    raise ValueError('expected list or workflow_runs[]')

def _rank(row):
    try:return int(row['run_number']),int(row['id'])
    except (KeyError,TypeError,ValueError):return 2**63-1,2**63-1

def select_global_owner(payload:Any,*,current_run_id:int,workflow_path:str,allocation_id:str,required_branch:str='main'):
    rows,total=_rows(payload);current_run_id=int(current_run_id);matching=[];malformed=0
    for raw in rows:
        if not isinstance(raw,dict) or raw.get('path')!=workflow_path: continue
        try: rid=int(raw['id']);rnum=int(raw['run_number'])
        except (KeyError,TypeError,ValueError): malformed+=1;continue
        matching.append(dict(raw,id=rid,run_number=rnum))
    unique={r['id']:r for r in matching}
    base={'schema':'formal-allocation-global-owner-v1','allocation_id':allocation_id,'workflow_path':workflow_path,'required_branch':required_branch,'current_run_id':current_run_id,'matching_run_count':len(unique)}
    if malformed:return {**base,'result_class':'UNCERTAIN_MALFORMED_MATCHING_RUN','may_enter_formal_step':False,'malformed_matching_count':malformed}
    if total is not None and total>len(rows):return {**base,'result_class':'UNCERTAIN_TRUNCATED_API_VIEW','may_enter_formal_step':False,'api_total_count':total,'api_rows_visible':len(rows)}
    current=unique.get(current_run_id)
    if current is None:return {**base,'result_class':'UNCERTAIN_CURRENT_RUN_NOT_VISIBLE','may_enter_formal_step':False,'matching_run_ids':sorted(unique)}
    ordered=sorted(unique.values(),key=_rank);owner=ordered[0]
    receipt={**base,'owner_run_id':owner['id'],'owner_run_number':owner['run_number'],'owner_head_sha':owner.get('head_sha'),'owner_head_branch':owner.get('head_branch'),'current_head_sha':current.get('head_sha'),'current_head_branch':current.get('head_branch'),'matching_run_ids':[r['id'] for r in ordered],'cross_head_sha_count':len({r.get('head_sha') for r in ordered}),'cross_branch_count':len({r.get('head_branch') for r in ordered}),'claim_scope':'launch ownership only; workflow path is the allocation identity'}
    if current.get('head_branch')!=required_branch:return {**receipt,'result_class':'FAIL_CURRENT_WRONG_BRANCH','may_enter_formal_step':False}
    if owner.get('head_branch')!=required_branch:return {**receipt,'result_class':'FAIL_OWNER_WRONG_BRANCH','may_enter_formal_step':False}
    ok=owner['id']==current_run_id
    return {**receipt,'result_class':'PASS_CANONICAL_GLOBAL_OWNER' if ok else 'FAIL_ALLOCATION_ALREADY_OWNED','may_enter_formal_step':ok}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('runs_json',type=Path);ap.add_argument('--current-run-id',type=int,required=True);ap.add_argument('--workflow-path',required=True);ap.add_argument('--allocation-id',required=True);ap.add_argument('--required-branch',default='main');ap.add_argument('--out',type=Path);a=ap.parse_args()
    result=select_global_owner(json.loads(a.runs_json.read_text(encoding='utf-8')),current_run_id=a.current_run_id,workflow_path=a.workflow_path,allocation_id=a.allocation_id,required_branch=a.required_branch)
    text=json.dumps(result,indent=2,sort_keys=True)+'\n';print(text,end='')
    if a.out:a.out.write_text(text,encoding='utf-8')
    raise SystemExit(0 if result['may_enter_formal_step'] else 2)
if __name__=='__main__':main()
