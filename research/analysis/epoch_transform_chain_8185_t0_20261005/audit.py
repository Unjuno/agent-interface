#!/usr/bin/env python3
"""Independent oracle audit; does not import candidate code."""
import json, math, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent
VALID={'stable_identity','window_translation','uniform_dpi_update','mixed_monitor_update','two_epoch_composition','composed_small_uncertainty','shared_uncertainty_control'}
INVALID={'stale_epoch','missing_edge','reversed_edge','duplicate_edge','unit_mismatch','changed_input_dpi_context','target_identity_swap','non_affine_reflow','uncertainty_crosses_target','uncertainty_hits_forbidden'}
def inside(box,p,r=(0,0)):
 x,y=p;rx,ry=r
 return x-rx>=box[0] and y-ry>=box[1] and x+rx<=box[2] and y+ry<=box[3]
def intersects(box,p,r=(0,0)):
 x,y=p;rx,ry=r
 return not (x+rx<box[0] or x-rx>box[2] or y+ry<box[1] or y-ry>box[3])
def independent_oracle(inp,truth):
 # The oracle's transform outcomes and target identity are authored separately from candidate output.
 cid=inp['case_id']; cls=truth['class']
 if cls!='valid_affine' or cid not in VALID:return {'decision':'UNKNOWN_REFUSE','reason':'oracle_control'}
 p=truth['expected_point']
 if inp.get('target_id')!=truth['expected_target_id'] or inp.get('target_box_target_id')!=truth['expected_target_id']:return {'decision':'UNKNOWN_REFUSE','reason':'oracle_target_identity'}
 if not inside(truth['target_box'],p):return {'decision':'UNKNOWN_REFUSE','reason':'oracle_target_geometry'}
 if any(intersects(b,p) for b in inp['forbidden_boxes']):return {'decision':'UNKNOWN_REFUSE','reason':'oracle_forbidden_geometry'}
 return {'decision':'ADMIT','reason':'oracle_valid_affine','mapped':p}
def baseline(inp):
 # Frozen comparator: one capture-origin plus last-known single uniform scale/offset.
 edges=inp['edges']
 if len(edges)!=1:return 'UNKNOWN_REFUSE'
 e=edges[0];M=e.get('matrix')
 if e.get('kind')!='affine' or e.get('epoch')!=inp['observation_epoch'] or e.get('source')!=inp['source_frame'] or e.get('target')!=inp['input_frame']:return 'UNKNOWN_REFUSE'
 if e.get('source_units')!=inp['source_units'] or e.get('target_units')!=inp['input_units']:return 'UNKNOWN_REFUSE'
 if e.get('residual',0)!=0 or e.get('correlation_id') or inp.get('target_correlated_uncertainty'):return 'UNKNOWN_REFUSE'
 if M[0][1]!=0 or M[1][0]!=0 or M[0][0]!=M[1][1]:return 'UNKNOWN_REFUSE'
 x,y=inp['point'];p=[M[0][0]*x+M[0][2],M[1][1]*y+M[1][2]]
 if not inside(inp['target_box'],p):return 'UNKNOWN_REFUSE'
 if any(intersects(b,p) for b in inp['forbidden_boxes']):return 'UNKNOWN_REFUSE'
 return 'ADMIT'
def audit(candidate_input,candidate_output,truth_doc):
 errors=[]; cases={x['case_id']:x for x in candidate_input['cases']}; truth={x['case_id']:x for x in truth_doc['truth']}; output={x['case_id']:x for x in candidate_output['decisions']}
 if set(cases)!=set(truth) or set(cases)!=set(output):errors.append('case_set_mismatch')
 rows=[];valid_rows=[]
 for cid,inp in cases.items():
  t=truth[cid]; got=output.get(cid,{}); expected=independent_oracle(inp,t)
  if got.get('decision')!=expected['decision']:errors.append('oracle_decision_mismatch:'+cid)
  if expected['decision']=='ADMIT':
   q=got.get('mapped')
   if not isinstance(q,list) or len(q)!=2 or any(abs(q[i]-expected['mapped'][i])>1e-9 for i in range(2)):errors.append('mapped_point_mismatch:'+cid)
   if got.get('target_id')!=t['expected_target_id']:errors.append('target_identity_mismatch:'+cid)
  if cid in INVALID and got.get('decision')!='UNKNOWN_REFUSE':errors.append('invalid_control_accepted:'+cid)
  b=baseline(inp);c=got.get('decision');row={'case_id':cid,'class':t['class'],'baseline':b,'candidate':c,'oracle':expected['decision']};rows.append(row)
  if t['class']=='valid_affine':valid_rows.append(row)
 base_unknown=sum(r['baseline']=='UNKNOWN_REFUSE' for r in valid_rows); cand_unknown=sum(r['candidate']=='UNKNOWN_REFUSE' for r in valid_rows)
 reduction=(base_unknown-cand_unknown)/base_unknown if base_unknown else 0.0
 false_admissions=sum(r['candidate']=='ADMIT' and r['oracle']!='ADMIT' for r in rows)
 valid=not errors and false_admissions==0 and all(r['candidate']==r['oracle'] for r in rows)
 if reduction<.20:errors.append('false_unknown_reduction_below_20_percent');valid=False
 return {'schema':'issue8185.audit.v1','valid':valid,'disposition':'PASS_METHOD_SCOPED' if valid else ('FAIL_UNSOUND' if false_admissions else 'FAIL_NO_INCREMENTAL_VALUE'),'errors':sorted(set(errors)),'case_count':len(rows),'false_admissions':false_admissions,'valid_affine_cases':len(valid_rows),'baseline_false_unknown':base_unknown,'candidate_false_unknown':cand_unknown,'false_unknown_reduction':reduction,'rows':rows}
def main():
 i=json.loads((ROOT/'candidate_input.json').read_text());o=json.loads((ROOT/'candidate_output.json').read_text());t=json.loads((ROOT/'oracle_truth.json').read_text())
 report=audit(i,o,t);(ROOT/'audit_output.json').write_text(json.dumps(report,sort_keys=True,indent=2)+'\n');print(report['disposition'],len(report['errors']),report['false_admissions'],report['false_unknown_reduction']);sys.exit(0 if report['valid'] else 2)
if __name__=='__main__':main()
