"""Replay real stale-clock failure into explicit received continuation state."""
import copy,hashlib,json
from pathlib import Path
from received_continuation_v1 import start,advance,clock_for,read_request
HERE=Path(__file__).resolve().parent

def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 out=HERE/'results/received-continuation-01';out.mkdir(exist_ok=False)
 r=HERE/'results/inkscape-guarded-click-01';ep=r/'runtime/events.jsonl';events=[json.loads(l) for l in ep.read_text().splitlines()]
 failed=read(r/'focus-x-current/calls.json');first=failed[0];after=first['request']['after'];session='archived-inkscape-guarded-click-01'
 state=advance(start(session),session,0,{'status':'boundary','cursor':after,'records':events[:after]})
 state=advance(state,session,after,first['reply']);identifier=first['request']['request_id']
 assert clock_for(state,identifier) is None
 assert state['cursor']>state['observation_cursor'] and state['observation']['sequence']==4
 pending=copy.deepcopy(state);poll=read_request(state,['clock']);assert 'command' not in poll and poll['after']==first['reply']['cursor']
 own_index=next(i for i,e in enumerate(events) if e['event']=='command' and e['command'].get('transport_request_id')==identifier)
 assert events[own_index+1]['event']=='clock'
 reply={'status':'boundary','cursor':own_index+2,'records':events[poll['after']:own_index+2]}
 state=advance(state,session,poll['after'],reply);matched=clock_for(state,identifier);assert matched['record']==events[own_index+1]
 old=next(e for e in first['reply']['records'] if e['event']=='clock');assert old['runtime_ns']<matched['record']['runtime_ns']
 # Whole real session, including overlap, then checkpoint JSON round-trip.
 whole=advance(state,session,state['cursor'],{'status':'boundary','cursor':len(events),'records':events[state['cursor']:]})
 assert whole['observation']['sequence']==12 and whole['cursor']==79
 restored=json.loads(json.dumps(whole));assert advance(restored,session,0,{'status':'boundary','cursor':len(events),'records':events})==whole
 controls={}
 for name in ('wrong_session','changed_overlap','gap','bad_cursor','duplicate_observation'):
  before=copy.deepcopy(whole);s=session;a=0;response={'status':'boundary','cursor':len(events),'records':copy.deepcopy(events)}
  if name=='wrong_session':s='another-session'
  elif name=='changed_overlap':response['records'][0]['tampered']=True
  elif name=='gap':a=80;response={'status':'boundary','cursor':80,'records':[]}
  elif name=='bad_cursor':response['cursor']=True
  else:a=whole['cursor'];response={'status':'boundary','cursor':a+1,'records':[copy.deepcopy(whole['observation'])]}
  try:advance(whole,s,a,response)
  except ValueError as exc:controls[name]=str(exc)
  else:raise AssertionError(name)
  assert whole==before
 closed=advance(whole,session,whole['cursor'],{'status':'closed','cursor':whole['cursor'],'records':[]})
 assert closed['channel_closed'] and 'runtime_exited' not in closed
 try:read_request(closed,['clock'])
 except ValueError:controls['closed_channel_read']='refused without asserting runtime exit'
 else:raise AssertionError('closed read')
 report={'scope':'offline replay and synthesized read-only slice of actual runtime events; not new socket execution',
  'sources':{str(p.relative_to(HERE.parent)):sha(p) for p in (ep,r/'focus-x-current/calls.json',HERE/'received_continuation_v1.py',Path(__file__))},
  'pending_cursor':pending['cursor'],'retained_image_cursor':pending['observation_cursor'],'retained_image_sequence':pending['observation']['sequence'],
  'old_clock_ns':old['runtime_ns'],'matched_clock_ns':matched['record']['runtime_ns'],'followup_request':poll,
  'final_cursor':whole['cursor'],'final_image_sequence':whole['observation']['sequence'],'controls':controls}
 (out/'pending.json').write_text(json.dumps(pending,indent=2)+'\n');(out/'final.json').write_text(json.dumps(whole,indent=2)+'\n');(out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
