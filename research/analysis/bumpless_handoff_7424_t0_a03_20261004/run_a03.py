import argparse,json,platform,sys
KP=2.0; KI=0.1; ALPHA=0.25; RATE=0.2; HORIZON=20; LO=0.0; HI=1.0; ZLO=-1.0; ZHI=1.0; REF=1.0

def clamp(x,lo,hi): return min(hi,max(lo,x))
def rollout(case,y0,applied0,conditioned):
 z=applied0-KP*(REF-y0) if conditioned else 0.0
 y=y0; prev=applied0; states=[y]; errors=[abs(REF-y)]; commands=[]
 for k in range(HORIZON):
  e=REF-y; raw=KP*e+z; requested=clamp(raw,LO,HI); applied=clamp(requested,prev-RATE,prev+RATE)
  znext=z if ((raw>=HI and e>0) or (raw<=LO and e<0)) else clamp(z+KI*e,ZLO,ZHI)
  ynext=y+ALPHA*(applied-y)
  commands.append({'tick':k,'y':round(y,12),'error':round(e,12),'z_before':round(z,12),'raw':round(raw,12),'clamped_command':round(requested,12),'previous_applied':round(prev,12),'applied':round(applied,12),'jump':round(abs(applied-(applied0 if k==0 else prev)),12),'z_after':round(znext,12),'y_after':round(ynext,12)})
  y=ynext;prev=applied;z=znext;states.append(y);errors.append(abs(REF-y))
 peak=max(errors); settled=None
 for i in range(len(errors)-2):
  if max(errors[i:i+3])<=0.05: settled=i;break
 return {'route':'conditioned' if conditioned else 'cold','states':[round(x,12) for x in states],'abs_errors':[round(x,12) for x in errors],'commands':commands,'metrics':{'first_jump':commands[0]['jump'],'peak_abs_tracking_error':round(peak,12),'integrated_abs_error_21_samples':round(sum(errors),12),'max_state':round(max(states),12),'min_state':round(min(states),12),'overshoot':round(max(0,max(states)-REF),12),'settle_tick_three_samples_le_0_05':settled}}

def gate(name,current=True,present=True,quiesced=True,lease=True,delay=0):
 events=['source_active'];acts=[];owner='source'
 if delay: events.append('handoff_delayed')
 if not current or not present or not lease:
  events+=['receiver_denied','source_released'];owner='none'
 elif not quiesced: events.append('receiver_denied_before_quiescence')
 else:
  if delay:events.append('source_quiesced_after_delay')
  events+=['transfer_accepted','receiver_actuation'];owner='receiver';acts=[0.6]
 return {'case':name,'input':{'state_fresh':current,'state_present':present,'source_quiesced':quiesced,'lease_valid':lease,'delay_ticks':delay},'events':events,'owner_final':owner,'receiver_actuations':acts}

def main():
 p=argparse.ArgumentParser();p.add_argument('--raw',required=True);a=p.parse_args()
 specs=[('no-disturbance',0.4,0.6),('step-disturbance-at-switch',0.5,0.6),('saturation-at-switch',0.5,1.0)]
 cases=[]
 for name,y,u in specs:cases.append({'case':name,'input':{'y':y,'applied_u':u,'reference':REF,'kp':KP,'ki':KI,'plant_alpha':ALPHA,'slew_per_tick':RATE,'horizon_ticks':HORIZON},'routes':[rollout(name,y,u,False),rollout(name,y,u,True)]})
 raw={'schema':'issue7424-bumpless-t0-a03-raw-v1','runtime':{'python':sys.version,'platform':platform.platform()},'cases':cases,'gates':[gate('stale-state',current=False),gate('missing-state',present=False),gate('revoked-lease',lease=False),gate('pre-quiescence',quiesced=False),gate('delayed-handoff',delay=2)],'mutation_controls':[{'case':'stale-state-accepted','input':{'state_fresh':False,'state_present':True,'source_quiesced':True,'lease_valid':True},'receiver_actuations':[0.6]},{'case':'receiver-before-quiescence','input':{'state_fresh':True,'state_present':True,'source_quiesced':False,'lease_valid':True},'receiver_actuations':[0.6]},{'case':'seed-from-requested-not-applied','input':{'y':0.4,'applied_u':0.6,'requested_u':0.95,'reference':1.0},'receiver_actuations':[0.8],'first_jump':0.2}]}
 with open(a.raw,'w',encoding='utf-8',newline='\n') as f:json.dump(raw,f,sort_keys=True,indent=2);f.write('\n')
 print(json.dumps({'status':'RUN_COMPLETE','cases':len(cases),'gates':len(raw['gates']),'mutations':len(raw['mutation_controls'])},sort_keys=True))
if __name__=='__main__':main()
