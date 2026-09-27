#!/usr/bin/env python3
import json, sys, time

SCOPE='decision-deadline-v1'
DEADLINE_NS=120_000_000
LEASE_NS=400_000_000
FRESHNESS_NS=400_000_000

def emit(obj):
    sys.stdout.write(json.dumps(obj,sort_keys=True)+'\n'); sys.stdout.flush()

def main():
    state='STATIC_GO'
    effect_count=0
    observation=None
    for line in sys.stdin:
        msg=json.loads(line)
        op=msg.get('op')
        if op=='observe':
            now=time.monotonic_ns()
            observation={
                'scope':SCOPE,'state':state,'observation_id':msg['observation_id'],'epoch':7,
                'observation_available_ns':now,'decision_deadline_ns':now+DEADLINE_NS,
                'lease_valid_until_ns':now+LEASE_NS,'freshness_budget_ns':FRESHNESS_NS
            }
            emit({'op':'observation','observation':observation})
        elif op=='act':
            recv=time.monotonic_ns(); effect_count+=1
            deadline=observation['decision_deadline_ns'] if observation else -1
            emit({'op':'effect','effect_count':effect_count,'received_ns':recv,
                  'semantic_valid': bool(observation and recv <= deadline),
                  'state_before':state,'state_after':state,'action':msg.get('action')})
        elif op=='close':
            emit({'op':'closed','effect_count':effect_count,'state':state}); return
        else:
            emit({'op':'error','reason':'unknown_op'}); return 2
    return 0
if __name__=='__main__': raise SystemExit(main())
