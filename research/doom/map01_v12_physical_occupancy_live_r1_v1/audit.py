from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path
from evaluate import evaluate

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('--formal',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();raw=json.loads((a.formal/'FORMAL_RESULT.json').read_text());errors=[];derived=[]
 for i in range(1,4):
  runtime=a.formal/f'session{i}'/'runtime'; pid=f'r1-physical-occupancy-{i}'; d=evaluate(runtime,pid);derived.append(d)
  if not d['pass']:errors.append(f'session{i}')
 if raw.get('formal_invocations')!=1 or any(raw.get(k)!=0 for k in ('reruns','replacements','tuning')):errors.append('budget')
 if raw.get('decision')!='PASS_MAP01_V12_PHYSICAL_OCCUPANCY_R1_SCOPED':errors.append('decision')
 if raw.get('sessions')!=derived:errors.append('rederive')
 widths=[x['censor_width_ms'] for d in derived for x in d['actuations']]
 if len(widths)!=6 or any(w>5.0 for w in widths):errors.append('precision')
 out={'passed':not errors,'errors':errors,'formal_sha256':sha(a.formal/'FORMAL_RESULT.json'),'derived_sessions':derived,'max_censor_width_ms':max(widths) if widths else None}
 a.out.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,sort_keys=True));raise SystemExit(0 if not errors else 1)
if __name__=='__main__':main()
