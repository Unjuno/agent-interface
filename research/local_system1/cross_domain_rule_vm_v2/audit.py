#!/usr/bin/env python3
import argparse,json
from pathlib import Path

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--result',required=True); ap.add_argument('--out',required=True); a=ap.parse_args()
    r=json.loads(Path(a.result).read_text()); errs=[]
    if r['formal_invocation']!=1 or r['reruns']!=0: errs.append('formal_count')
    if r['chromium']['unique_payloads']!=8192 or r['chromium']['errors']: errs.append('chromium')
    if len(r['openttd_retained'])!=5 or not all(x['ok'] for x in r['openttd_retained']): errs.append('openttd_retained')
    if not all(x['ok'] for x in r['openttd_controls']): errs.append('controls')
    if any(r['counters'][k]!=0 for k in r['counters']): errs.append('counters')
    recompute={
      'chromium_exact':not r['chromium']['errors'],
      'openttd_retained_5of5':len(r['openttd_retained'])==5 and all(x['ok'] for x in r['openttd_retained']),
      'controls_fail_closed':all(x['ok'] for x in r['openttd_controls']),
      'chromium_vm_p95_lt10us':r['timings']['chromium_vm_only']['p95_us']<10,
      'openttd_vm_p95_lt10us':r['timings']['openttd_vm_only']['p95_us']<10,
      'chromium_e2e_p95_lt25us':r['timings']['chromium_vm_e2e']['p95_us']<25,
      'openttd_e2e_p95_lt25us':r['timings']['openttd_vm_e2e']['p95_us']<25,
    }
    if recompute!=r['gates']: errs.append('gates')
    expected='PASS_CROSS_DOMAIN_RULE_VM_SCOPED' if all(recompute.values()) else ('FAIL_CROSS_DOMAIN_SEMANTICS' if not recompute['chromium_exact'] or not recompute['openttd_retained_5of5'] else ('FAIL_FAIL_CLOSED' if not recompute['controls_fail_closed'] else 'HOLD_VM_OVERHEAD_NOT_SMALL'))
    if expected!=r['decision']: errs.append('decision')
    out={'audit':'PASS' if not errs else 'FAIL','errors':errs,'decision':r['decision'],'recomputed_gates':recompute}
    Path(a.out).write_text(json.dumps(out,indent=2,sort_keys=True)+'\n'); print(json.dumps(out,sort_keys=True))
if __name__=='__main__': main()
