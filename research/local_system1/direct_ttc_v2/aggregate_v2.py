#!/usr/bin/env python3
import argparse,json,sys,resource
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
import run_direct_ttc_v1 as v1
SEEDS=[9061701,9061702,9061703,9061704]
def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--cases',required=True); ap.add_argument('--out',required=True); a=ap.parse_args()
 root=Path(a.cases); rows=[]
 for s in SEEDS:
  p=root/str(s)/'CASE.json'
  if not p.exists(): raise SystemExit(f'missing case {s}')
  r=json.loads(p.read_text())
  if r.get('seed')!=s or r.get('case_id')!=f'DIRECT-TTC-V2-{s}': raise SystemExit(f'bad case {s}')
  rows.append({k:v for k,v in r.items() if k not in ['case_id','peak_rss_kib']})
 dec,gates=v1.decide(rows)
 result={'task':'LOCAL-SYSTEM1-DIRECT-TTC-20260917-002','formal_cases':4,'formal_case_reruns':0,'aggregate_invocations':1,'decision':dec,'gates':gates,'scientific_source_sha256':'a34471ea88d6b79cb0578baacd418c9191c7a2c13d4050cb2909fbb9f474d3eb','seeds':SEEDS,'rows':rows,'peak_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
 Path(a.out).write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
 print(json.dumps({'decision':dec,'out':a.out},sort_keys=True))
if __name__=='__main__': main()
