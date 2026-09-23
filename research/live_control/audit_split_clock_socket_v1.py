"""Replay real split-clock network transcript and source pins."""
import hashlib,json
from pathlib import Path
from received_continuation_v1 import start,advance,clock_for
HERE=Path(__file__).resolve().parent

def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 r=HERE/'results/split-clock-socket-01'
 for n,h in read(r/'plan.json')['sources'].items():assert sha(HERE/n)==h,n
 calls=read(r/'calls.json');events=[json.loads(l) for l in (r/'runtime-events.jsonl').read_text().splitlines()];ep=read(r/'endpoint.json');state=start(ep['socket'])
 for c in calls:
  q,a=c['request'],c['reply'];assert q['after']==state['cursor'] and a['records']==events[q['after']:a['cursor']]
  state=advance(state,ep['socket'],q['after'],a);assert state==c['continuation']
  if c['requested_clock_id']:assert clock_for(state,c['requested_clock_id'])==c['matched_clock']
 assert len(calls)==5 and len(events)==7
 assert calls[1]['matched_clock'] is None and calls[2]['matched_clock'] is None and calls[2]['reply']['status']=='timeout'
 assert calls[3]['matched_clock']['echo_cursor']==4 and calls[3]['matched_clock']['record_cursor']==5
 assert all('command' not in calls[i]['request'] for i in (2,3))
 commands=[e['command'] for e in events if e['event']=='command'];assert [c['transport_request_id'] for c in commands]==['old-clock','new-clock','finish-once']
 assert sum(c.get('command',{}).get('op')=='clock' for c in [x['request'] for x in calls])==1
 assert state['cursor']==7 and state['observation_cursor']==1 and state['observation']['sequence']==1
 assert read(r/'result.json')['exit_code']==0 and (r/'stderr.txt').read_bytes()==b''
 assert not Path(ep['socket']).exists() and not Path(ep['cancel_socket']).exists()
 report={'events':7,'real_socket_calls':5,'clock_commands_forwarded':1,'command_free_followups':2,'retained_observation_cursor':1,'final_received_cursor':7,'socket_paths_removed':True,'audit_sha256':sha(Path(__file__)),'scope':'real network/subprocess transcript; synthetic clock gate and image reference; no live GUI or model performance claim'}
 (r/'audit.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
if __name__=='__main__':main()
