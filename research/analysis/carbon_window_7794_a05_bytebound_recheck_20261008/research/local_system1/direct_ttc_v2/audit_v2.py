#!/usr/bin/env python3
import argparse,json,hashlib,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
import run_direct_ttc_v1 as v1
SEEDS=[9061701,9061702,9061703,9061704]
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--result',required=True); ap.add_argument('--out',required=True); a=ap.parse_args()
 r=json.loads(Path(a.result).read_text()); errors=[]
 if r.get('formal_cases')!=4 or r.get('formal_case_reruns')!=0 or r.get('aggregate_invocations')!=1: errors.append('counts')
 if r.get('seeds')!=SEEDS: errors.append('seeds')
 if r.get('scientific_source_sha256')!='a34471ea88d6b79cb0578baacd418c9191c7a2c13d4050cb2909fbb9f474d3eb': errors.append('source_sha')
 rows=r.get('rows',[])
 if [x.get('seed') for x in rows]!=SEEDS: errors.append('row_seeds')
 dec,gates=v1.decide(rows)
 if dec!=r.get('decision'): errors.append('decision')
 if gates!=r.get('gates'): errors.append('gates')
 audit={'audit':'PASS' if not errors else 'FAIL','errors':errors,'result_sha256':sha(a.result),'recomputed_decision':dec,'recomputed_gates':gates}
 Path(a.out).write_text(json.dumps(audit,indent=2,sort_keys=True)+'\n'); print(json.dumps(audit,sort_keys=True))
if __name__=='__main__': main()
