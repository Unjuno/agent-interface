#!/usr/bin/env python3
import argparse, copy, json, pathlib, shutil, subprocess, sys, tempfile
ap=argparse.ArgumentParser(); ap.add_argument('formal',type=pathlib.Path); ap.add_argument('study',type=pathlib.Path); a=ap.parse_args()
controls=[]
def run(root,study):
 p=subprocess.run([sys.executable,'-S','-B',str(study/'audit.py'),str(root),str(study)],capture_output=True,text=True,timeout=10)
 return p.returncode,json.loads(p.stdout) if p.stdout else None
mutations=['missing_case','wrong_effect','false_candidate','flip_gap','reorder_raw','nonzero_exit','wrong_scenario','source_change','missing_event','wrong_clock_flag']
for m in mutations:
 with tempfile.TemporaryDirectory(prefix='audit2255-') as td:
  base=pathlib.Path(td); root=base/'formal'; study=base/'study'; shutil.copytree(a.formal,root); shutil.copytree(a.study,study)
  rc0,o0=run(root,study); intact=(rc0==0 and o0 and o0.get('errors')==[])
  r=json.loads((root/'RUN.json').read_text())
  if m=='missing_case': r['cases'].pop()
  elif m=='wrong_effect': r['cases'][0]['snapshot']['text']='CORRUPT'
  elif m=='false_candidate': r['cases'][4]['policies'][1]['decision']['status']='SATISFIED'
  elif m=='flip_gap': r['cases'][4]['delivery_packet']['coverage_complete']=True
  elif m=='reorder_raw': r['cases'][0]['raw_events']=list(reversed(r['cases'][0]['raw_events']))
  elif m=='nonzero_exit': r['cases'][0]['app_exit']=9
  elif m=='wrong_scenario': r['cases'][0]['scenario']='BOGUS'
  elif m=='source_change': (study/'policy.py').write_text((study/'policy.py').read_text()+'\n# mutation\n')
  elif m=='missing_event': r['cases'][0]['raw_events'].pop()
  elif m=='wrong_clock_flag': r['cases'][7]['delivery_packet']['clock_coherent']=True
  if m!='source_change': (root/'RUN.json').write_text(json.dumps(r,indent=2,sort_keys=True)+'\n')
  rc1,o1=run(root,study); rejected=(rc1!=0 or (o1 and o1.get('errors')))
  controls.append({'name':m,'intact_pass':intact,'mutation_rejected':bool(rejected)})
out={'status':'PASS_COPIED_EVIDENCE_CONTROLS' if all(x['intact_pass'] and x['mutation_rejected'] for x in controls) else 'FAIL_CONTROLS','count':len(controls),'controls':controls}
print(json.dumps(out,indent=2,sort_keys=True))
raise SystemExit(0 if out['status'].startswith('PASS') else 1)
