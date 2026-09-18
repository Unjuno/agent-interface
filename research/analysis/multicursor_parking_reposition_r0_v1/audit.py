from __future__ import annotations
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
EXPECTED={str(n):4**n for n in range(2,7)}

def main():
    r=json.loads((ROOT/'RESULT.json').read_text()); e=[]
    if r.get('formal_invocations')!=1 or r.get('reruns')!=0:e.append('allocation')
    if r.get('by_length')!=EXPECTED or r.get('sequences')!=sum(EXPECTED.values()):e.append('corpus')
    if r.get('alias_checks')!=r.get('sequences')*3 or r.get('alias_mismatch')!=0:e.append('alias')
    if r.get('switch_checks')!=r.get('sequences')*4 or r.get('switch_mismatch')!=0:e.append('switch')
    if r.get('strict_gain_cases',0)<=0:e.append('nonvacuous')
    if r.get('decision')!='PASS_MULTICURSOR_PARKING_REPOSITION_SCOPED' or r.get('pass') is not True:e.append('decision')
    out={'pass':not e,'errors':e,'decision':r.get('decision') if not e else 'FAIL_INTEGRITY',
         'result_sha256':hashlib.sha256((ROOT/'RESULT.json').read_bytes()).hexdigest()}
    (ROOT/'AUDIT.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,sort_keys=True));raise SystemExit(0 if not e else 1)
if __name__=='__main__':main()
