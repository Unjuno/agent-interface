import argparse,json,hashlib,statistics
from pathlib import Path

def verify(d):
    e=[]
    if d.get('formal_invocations')!=1:e.append('formal_invocations')
    if d.get('reruns')!=0:e.append('reruns')
    if d.get('cases')!=400000:e.append('cases')
    L=d.get('large',{});c=L.get('current',{});t=L.get('temporal',{});w=L.get('wait',{})
    if c.get('mismatch')!=0 or t.get('mismatch')!=0:e.append('oracle_mismatch')
    if c.get('hits')!=151814:e.append('current_hits')
    if t.get('hits')!=231610:e.append('temporal_hits')
    if not (c.get('mean_latency_ns',1e18)-t.get('mean_latency_ns',0)>=3_000_000):e.append('large_current_delta')
    if not (w.get('mean_latency_ns',1e18)-t.get('mean_latency_ns',0)>=10_000_000):e.append('large_wait_delta')
    if any(d.get(k)!=0 for k in ('authority_grants','model_calls','gui_actions','task_input_actions')):e.append('forbidden_actions')
    rows=d.get('live_rows',[])
    if len(rows)!=72 or any(not r.get('effect') or r.get('wrong') for r in rows):e.append('live_effect')
    s=d.get('live_summary',{});tm=s.get('temporal',{}).get('median_latency_ns',1e18);cm=s.get('current',{}).get('median_latency_ns',0);wm=s.get('wait',{}).get('median_latency_ns',0)
    if tm>=5_000_000:e.append('live_temporal')
    if cm<25_000_000:e.append('live_current')
    if wm<25_000_000:e.append('live_wait')
    if cm-tm<20_000_000:e.append('live_current_delta')
    if wm-tm<20_000_000:e.append('live_wait_delta')
    decision='PASS_TEMPORAL_SPECULATION_K1_BUDGET_SCOPED' if not e else ('HOLD_NO_LATENCY_DISCRIMINATOR' if e==['large_current_delta'] else 'FAIL_RUNG1')
    return {'decision':decision,'audit_pass':not e,'errors':e}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('result');a=ap.parse_args();p=Path(a.result);d=json.loads(p.read_text());o=verify(d);o['result_sha256']=hashlib.sha256(p.read_bytes()).hexdigest();print(json.dumps(o,indent=2,sort_keys=True));raise SystemExit(0 if o['audit_pass'] else 1)
if __name__=='__main__':main()
