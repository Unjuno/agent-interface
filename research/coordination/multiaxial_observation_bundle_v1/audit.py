from __future__ import annotations
import argparse,hashlib,json,pathlib

def sha256(p):
 h=hashlib.sha256();h.update(p.read_bytes());return h.hexdigest()

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--result',required=True);ap.add_argument('--source-dir',required=True);ap.add_argument('--out',required=True);a=ap.parse_args()
 rp=pathlib.Path(a.result);src=pathlib.Path(a.source_dir);d=json.loads(rp.read_text());errors=[];g={}
 for n,e in d['source_sha256'].items():
  if sha256(src/n)!=e: errors.append('SOURCE_MISMATCH:'+n)
 rows=d['rows'];cand=[r for r in rows if r['result']['policy']=='CAPABILITY_GATED'];base=[r for r in rows if r['result']['policy']=='RELEVANCE_ONLY']
 g['row_count_48']=len(rows)==48 and len(cand)==24 and len(base)==24
 candidate_ok=True;metadata_ok=True;zero_leak=True
 from model import SOURCES
 for r in cand:
  x=r['result']
  if x['included_ids']!=r['expected_included'] or x['rejected_disallowed']!=r['expected_rejected'] or x['omitted_due_to_budget']!=r['expected_omitted'] or x['unsupported_sources']!=r['expected_unsupported']:
   candidate_ok=False;errors.append('CANDIDATE:'+r['row_id'])
  for item in x['items']:
   if item!=SOURCES[item['source_id']].item(): metadata_ok=False;errors.append('METADATA:'+r['row_id']+':'+item['source_id'])
   if item['source_kind'] not in next(c for c in json.loads((src/'cases.json').read_text()) if c['case_id']==r['case_id'])['allowed_kinds'] or item['context'] not in next(c for c in json.loads((src/'cases.json').read_text()) if c['case_id']==r['case_id'])['allowed_contexts']:
    zero_leak=False;errors.append('LEAK:'+r['row_id']+':'+item['source_id'])
 g['candidate_expected_24_24']=candidate_ok;g['metadata_exact']=metadata_ok;g['zero_disallowed_candidate']=zero_leak
 discr=[r for r in base if r['baseline_disallowed']];viol=0
 cases={c['case_id']:c for c in json.loads((src/'cases.json').read_text())}
 for r in discr:
  c=cases[r['case_id']]
  if any(SOURCES[i['source_id']].source_kind not in c['allowed_kinds'] or SOURCES[i['source_id']].context not in c['allowed_contexts'] for i in r['result']['items']): viol+=1
 g['baseline_discriminator_16_16']=len(discr)==16 and viol==16
 g['malformed_controls_5_5_reject']=len(d['malformed_controls'])==5 and all(not x['accepted'] for x in d['malformed_controls'])
 decision='PASS_MULTIAXIAL_SOURCE_CAPABILITY_GATE_SCOPED' if all(g.values()) and not errors else 'FAIL_OBSERVATION_SOURCE_GATE'
 out={'decision':decision,'gates':g,'errors':errors,'result_sha256':sha256(rp),'formal_reruns':0};pathlib.Path(a.out).write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,sort_keys=True));return 0 if decision.startswith('PASS') else 1
if __name__=='__main__':raise SystemExit(main())
