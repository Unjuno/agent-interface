import argparse, json, platform, sys

def clamp(x, lo=0.0, hi=1.0): return min(hi, max(lo, x))
def receiver_output(y, ref, z, applied, requested=None, kp=2.0, rate=0.2):
    raw = kp * (ref - y) + z
    command = clamp(raw)
    return clamp(command, applied-rate, applied+rate), raw, command

def episode(name, y, applied, ref=1.0, kp=2.0, rate=0.2, requested=None):
    cold, cold_raw, cold_cmd = receiver_output(y, ref, 0.0, applied, kp=kp, rate=rate)
    seed = (requested if requested is not None else applied) - kp * (ref-y)
    conditioned, cond_raw, cond_cmd = receiver_output(y, ref, seed, applied, kp=kp, rate=rate)
    rows=[]
    for label, first in [('cold',cold),('conditioned',conditioned)]:
        state=y; u=first; peak=abs(ref-state); max_state=state
        for _ in range(20):
            state = state + 0.25*(u-state)
            peak=max(peak,abs(ref-state)); max_state=max(max_state,state)
            err=ref-state
            raw=kp*err + (seed if label=='conditioned' else 0.0)
            cmd=clamp(raw); nxt=clamp(cmd,u-rate,u+rate)
            u=nxt
        rows.append({'route':label,'first_applied':round(first,12),'first_raw':round(cond_raw if label=='conditioned' else cold_raw,12),'first_command':round(cond_cmd if label=='conditioned' else cold_cmd,12),'discontinuity':round(abs(first-applied),12),'peak_abs_tracking_error':round(peak,12),'peak_state':round(max_state,12)})
    return {'case':name,'input':{'y':y,'applied_u':applied,'requested_u':requested if requested is not None else applied,'ref':ref,'kp':kp,'rate_limit_per_tick':rate,'state_fresh':True,'source_quiesced':True,'lease_valid':True},'routes':rows}

def gated_case(name, current=True, present=True, quiesced=True, lease=True, delay_ticks=0):
    receiver_actuations=[]; owner='source'; events=['source_active']
    if delay_ticks:
        events.append('handoff_delayed')
    if not current or not present or not lease:
        events.append('receiver_denied'); events.append('source_released')
        owner='none'
    elif not quiesced:
        events.append('receiver_denied_before_quiescence')
    else:
        if delay_ticks: events.append('source_quiesced_after_delay')
        owner='receiver'; events.append('transfer_accepted'); events.append('receiver_actuation'); receiver_actuations=[0.6]
    return {'case':name,'input':{'state_fresh':current,'state_present':present,'source_quiesced':quiesced,'lease_valid':lease,'delay_ticks':delay_ticks},'owner_final':owner,'events':events,'receiver_actuations':receiver_actuations,'release_not_delayed_by_conditioning':not bool(not current or not present or not lease)}

def main():
 p=argparse.ArgumentParser(); p.add_argument('--raw',required=True); a=p.parse_args()
 raw={'schema':'issue7424-bumpless-t0-raw-v1','runtime':{'python':sys.version,'platform':platform.platform()},'episodes':[episode('no-disturbance',0.4,0.6),episode('step-disturbance-at-switch',0.5,0.6),episode('saturation-at-switch',0.5,1.0)],'gates':[gated_case('stale-state',current=False),gated_case('missing-state',present=False),gated_case('revoked-lease',lease=False),gated_case('delayed-handoff',delay_ticks=2),gated_case('pre-quiescence',quiesced=False)],'mutation_controls':[{'case':'mutant-stale-state-accepted','input':{'state_fresh':False,'state_present':True,'source_quiesced':True,'lease_valid':True},'receiver_actuations':[0.6]},{'case':'mutant-act-before-quiescence','input':{'state_fresh':True,'state_present':True,'source_quiesced':False,'lease_valid':True},'receiver_actuations':[0.6]}]}
 # Explicitly corrupted-control records: expected actuator value is derived from requested, not applied, state.
 raw['mutation_controls'].append({'case':'mutant-condition-from-requested-input','input':{'applied_u':0.6,'requested_u':0.95,'state_fresh':True,'source_quiesced':True,'lease_valid':True},'receiver_actuations':[0.8],'discontinuity':0.2})
 with open(a.raw,'w',encoding='utf-8',newline='\n') as f: json.dump(raw,f,sort_keys=True,indent=2); f.write('\n')
 print(json.dumps({'status':'RUN_COMPLETE','episodes':len(raw['episodes']),'gates':len(raw['gates']),'mutations':len(raw['mutation_controls'])},sort_keys=True))
if __name__=='__main__': main()





