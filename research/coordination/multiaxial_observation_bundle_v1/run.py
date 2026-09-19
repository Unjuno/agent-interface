from __future__ import annotations
import argparse,hashlib,json,pathlib
from model import SOURCES,compile_relevance_only,compile_capability_gated,validate_presentation
ROOT=pathlib.Path(__file__).resolve().parent

def sha256(p):
 h=hashlib.sha256();h.update(p.read_bytes());return h.hexdigest()

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--out',required=True);a=ap.parse_args();out=pathlib.Path(a.out)
 if out.exists(): raise SystemExit('output exists')
 out.mkdir(parents=True)
 cases=json.loads((ROOT/'cases.json').read_text());rows=[]
 for rep in range(4):
  for case in cases:
   for policy in ('RELEVANCE_ONLY','CAPABILITY_GATED'):
    r=compile_relevance_only(case) if policy=='RELEVANCE_ONLY' else compile_capability_gated(case)
    rows.append({'row_id':f"{case['case_id']}::r{rep}::{policy}",'rep':rep,'case_id':case['case_id'],'expected_included':case['expected_included'],'expected_rejected':case['expected_rejected'],'expected_omitted':case['expected_omitted'],'expected_unsupported':case['expected_unsupported'],'baseline_disallowed':case['baseline_disallowed'],'result':r})
 malformed=[
  {'name':'missing_source','item':{'source_id':'','provenance':'p','evidence_role':'PLANNER_CONTEXT','currentness':'CURRENT'}},
  {'name':'missing_provenance','item':{'source_id':'x','provenance':'','evidence_role':'PLANNER_CONTEXT','currentness':'CURRENT'}},
  {'name':'unknown_role','item':{'source_id':'x','provenance':'p','evidence_role':'MAGIC','currentness':'CURRENT'}},
  {'name':'role_override','item':{'source_id':'x','provenance':'p','evidence_role':'PLANNER_CONTEXT','currentness':'CURRENT','presentation_role_override':'ADMISSION_DEPENDENCY'}},
  {'name':'currentness_override','item':{'source_id':'x','provenance':'p','evidence_role':'PLANNER_CONTEXT','currentness':'HISTORICAL','presentation_currentness_override':'CURRENT'}}]
 controls=[]
 for x in malformed:
  ok,reason=validate_presentation(x['item']);controls.append({'name':x['name'],'accepted':ok,'reason':reason})
 payload={'task':'MULTIAXIAL-SOURCE-CAPABILITY-GATE-20260917-001','formal_rows':len(rows),'rows':rows,'malformed_controls':controls,'source_sha256':{p.name:sha256(p) for p in [ROOT/'model.py',ROOT/'cases.json',ROOT/'run.py',ROOT/'audit.py',ROOT/'PLAN.md',ROOT/'prereg.json']}}
 (out/'formal.json').write_text(json.dumps(payload,indent=2,sort_keys=True)+'\n')
 print(json.dumps({'formal_rows':len(rows),'controls':len(controls)},sort_keys=True))
if __name__=='__main__':main()
