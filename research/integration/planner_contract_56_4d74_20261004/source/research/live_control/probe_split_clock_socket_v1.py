"""Real AF_UNIX continuation across stale clock and delayed current clock."""
import hashlib,json,subprocess,sys
from pathlib import Path
from received_continuation_v1 import start
from received_exchange_v2 import request_once
HERE=Path(__file__).resolve().parent
root=HERE/'results/split-clock-socket-01';root.mkdir(exist_ok=False)
names=['split_clock_fixture_v1.py','split_clock_entry_v1.py','probe_split_clock_socket_v1.py','received_exchange_v2.py','received_continuation_v1.py','stopped_socket_v1.py','stopped_cursor_v1.py','command_once_v2.py','bounded_pipe_writer_v2.py','unix_json_deadline.py']
(root/'plan.json').write_text(json.dumps({'scope':'real private socket/subprocess, synthetic clock gate; no GUI/model timing','sources':{n:hashlib.sha256((HERE/n).read_bytes()).hexdigest() for n in names}},indent=2)+'\n')
p=subprocess.Popen([sys.executable,str(HERE/'split_clock_entry_v1.py'),'serve','--',str(root)],stdout=subprocess.PIPE,stderr=(root/'stderr.txt').open('w'),text=True)
calls=[];state=None
try:
 endpoint=json.loads(p.stdout.readline());(root/'endpoint.json').write_text(json.dumps(endpoint));socket=endpoint['socket'];state=start(socket)
 def call(spec):
  global state
  result=request_once(socket,state,spec);calls.append(result);state=result['continuation'];(root/'calls.json').write_text(json.dumps(calls,indent=2)+'\n');return result
 call({'events':['observation'],'timeout':2})
 first=call({'events':['clock'],'timeout':2,'command':{'op':'clock'},'request_id':'new-clock'})
 assert first['matched_clock'] is None and state['observation']['sequence']==1
 pending=call({'events':['clock'],'timeout':.05,'clock_request_id':'new-clock'})
 assert pending['reply']['status']=='timeout' and pending['matched_clock'] is None
 assert state['pending_clock']['request_id']=='new-clock' and p.poll() is None
 (root/'release-clock').write_text('release existing clock; no new command')
 received=call({'events':['clock'],'timeout':2,'clock_request_id':'new-clock'})
 assert received['matched_clock']['record']['runtime_ns']>1 and state['observation']['sequence']==1
 call({'events':['independent_evaluation'],'timeout':2,'command':{'op':'finish'},'request_id':'finish-once'})
 code=p.wait(timeout=10);assert code==0
 report={'exit_code':code,'calls':len(calls),'clock_commands':sum(c['request'].get('command',{}).get('op')=='clock' for c in calls),'read_only_followups':sum('command' not in c['request'] for c in calls[2:4]),'pending_timeout':pending['reply']['status'],'image_sequence_retained':state['observation']['sequence'],'scope':'actual network; synthetic clock and image reference'}
 assert report['clock_commands']==1 and report['read_only_followups']==2
 (root/'result.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
finally:
 (root/'release-clock').touch(exist_ok=True)
 if p.poll() is None:
  p.terminate();p.wait(timeout=10)
