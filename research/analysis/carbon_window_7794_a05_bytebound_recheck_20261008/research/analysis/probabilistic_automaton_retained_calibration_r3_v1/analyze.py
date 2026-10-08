import argparse,json,hashlib
from pathlib import Path
MEASURED='MEASURED_SAME_POPULATION'
EXPECTED={
'release_edge_869':'c9b48a676d6ca82a406f429608f84efd63f23fa7',
'receipt_drain_1472':'ddfdf5c3325fac0b23716d54357ff506f6d16ac1',
'fast_lane_1445':'748771ffda6cb76221d90a24ff9e14c7db2330bf',
'recovery_1769':'d8888ee7543783a3e4f67b53138956687d727b83',
'temporal_monitor_1764':'1498fec5b36df85cc8eb7a10eaae86381126cb5c'}
def classify(L,S):
 req=L['required_fields'];fams=L['families'];cal=[];real=0;invalid=[]
 for r in fams:
  ok=all(r[k]==MEASURED for k in req)
  if ok:cal.append(r['id'])
  if r['real_backend_rows']==MEASURED:real+=1
  if not ok:invalid.append(r['id'])
 src_ok=all(S[k]['git_blob']==v for k,v in EXPECTED.items()) and set(S)==set(EXPECTED)
 forbidden_ok=L['production_estimate'] is None and L['cross_family_substitution'] is False
 good=len(fams)==5 and real>=2 and not cal and len(invalid)==5 and src_ok and forbidden_ok
 return {'decision':'PASS_RETAINED_PROBABILISTIC_AUTOMATON_CALIBRATION_NOT_IDENTIFIABLE_SCOPED' if good else 'FAIL_INTEGRITY','family_count':len(fams),'real_backend_family_count':real,'calibratable_families':cal,'invalid_family_count':len(invalid),'source_map_exact':src_ok,'production_estimate_emitted':L['production_estimate'] is not None,'cross_family_substitution':L['cross_family_substitution']}
def corruptions(L,S):
 base=classify(L,S);controls={};authored=[r for r in L['families'] if r['source_role']=='authored_control']
 controls['authored_population_promotion_detected']=all(r['empirical_population_frequency']=='AUTHORED_CONTROL' for r in authored)
 controls['no_rows_not_measured']=all(r['real_backend_rows']=='NO_FORMAL_ROWS' for r in L['families'] if r['source_role']=='no_formal_rows')
 controls['synthetic_not_live']=all(r['real_backend_rows']=='SYNTHETIC_SEMANTICS' for r in L['families'] if r['source_role']=='synthetic_semantics')
 X=json.loads(json.dumps(L));X['cross_family_substitution']=True;controls['cross_family_laundering_rejected']=classify(X,S)['decision']!='PASS_RETAINED_PROBABILISTIC_AUTOMATON_CALIBRATION_NOT_IDENTIFIABLE_SCOPED'
 X=json.loads(json.dumps(L));X['production_estimate']={'p':'fabricated'};controls['fabricated_estimate_rejected']=classify(X,S)['decision']!='PASS_RETAINED_PROBABILISTIC_AUTOMATON_CALIBRATION_NOT_IDENTIFIABLE_SCOPED'
 controls['base_pass']=base['decision'].startswith('PASS_');return controls
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--ledger',required=True);ap.add_argument('--source-map',required=True);ap.add_argument('--construction',action='store_true');ap.add_argument('--output',required=True);a=ap.parse_args();o=Path(a.output);assert not o.exists();L=json.loads(Path(a.ledger).read_text());S=json.loads(Path(a.source_map).read_text());r=classify(L,S);r['corruption_controls']=corruptions(L,S);r['formal_invocations']=0 if a.construction else 1;r['reruns']=0;r['replacements']=0;r['tuning']=0
 if not all(r['corruption_controls'].values()):r['decision']='FAIL_INTEGRITY'
 if a.construction and r['decision'].startswith('PASS_'):r['decision']='CONSTRUCTION_PASS'
 raw=json.dumps(r,sort_keys=True,separators=(',',':')).encode();r['digest']=hashlib.sha256(raw).hexdigest();o.write_text(json.dumps(r,indent=2,sort_keys=True)+'\n');print(json.dumps(r,indent=2,sort_keys=True))
if __name__=='__main__':main()
