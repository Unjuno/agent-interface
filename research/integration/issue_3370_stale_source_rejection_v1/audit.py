"""Independent audit for the one-shot stale-source MCP control."""
import hashlib
import json
from pathlib import Path
import sys

root=Path(sys.argv[1]); failures=[]
def need(ok,msg):
    if not ok: failures.append(msg)
def read(name): return json.loads((root/name).read_text())

start=read('start-meta.json')
need(start.get('image_status')=='image','initial source image unavailable')
need(start.get('image_reference',{}).get('sequence')==1,'initial source sequence is not 1')
need(len(read('start-images.json'))==1,'exactly one starting PNG')
observe=read('observe-meta.json')
observe_native=observe.get('receipt',{}).get('native_result',{})
need(observe_native.get('status')=='boundary','read-only stage-1 observation did not return boundary')
need(observe_native.get('observation',{}).get('sequence')==2,'new observation is not sequence 2')
need(observe_native.get('observation_only',{}).get('input_dispatched') is False,
     'observation step does not prove no input')
need(len(read('observe-images.json'))==1,'fresh observation PNG missing')
need(read('start-images.json')[0]['sha256']==read('observe-images.json')[0]['sha256'],
     'expected unchanged canvas bytes differ; preserve as unexpected observation')
stale=read('stale-submit-meta.json')
need(stale.get('status')=='mcp_error','stale request was not refused as an MCP error')
need(any('decision must name the presented source' in t for t in stale.get('text',[])),
     'stale-source mismatch is not the recorded rejection reason')
run=root/'allocation/run'
need(not (run/'actions.json').exists() or json.loads((run/'actions.json').read_text())==[],
     'native input action was recorded')
request2=json.loads((run/'request-2.json').read_text()) if (run/'request-2.json').exists() else {}
request3=json.loads((run/'request-3.json').read_text()) if (run/'request-3.json').exists() else {}
need(request2.get('source_sequence')==2 and request2.get('interaction')=='observe',
     'stage 2 was not closed using the pre-registered read-only current-source observation')
need(request3.get('source_sequence')==3 and request3.get('finish') is True,
     'stage 3 was not closed using the pre-registered no-input finish')
reply2=json.loads((run/'reply-2.json').read_text()) if (run/'reply-2.json').exists() else {}
need(reply2.get('status')=='boundary' and reply2.get('observation_only',{}).get('input_dispatched') is False,
     'read-only cleanup observation boundary missing')
reply3=json.loads((run/'reply-3.json').read_text()) if (run/'reply-3.json').exists() else {}
need(reply3.get('status')=='finished','explicit no-input finish reply missing')
owner=json.loads((run/'owner.json').read_text())
need(owner.get('pid') is not None,'owner identity missing')
client=read('client-result.json')
final=client.get('final_status',{})
allocation=final.get('allocation',{}) if isinstance(final,dict) else {}
need('terminal' in client.get('status_polls',[]),'managed owner terminal state not observed')
need(allocation.get('status')=='terminal','final owner state is not terminal')
need(allocation.get('returncode')==0,'bounded owner did not exit successfully after no-input finish')
cleanup_path=run/'cleanup-report.json'
need(cleanup_path.exists(),'cleanup report missing')
if cleanup_path.exists():
    cleanup=json.loads(cleanup_path.read_text())
    need(cleanup.get('status')=='completed' and cleanup.get('tracked_processes_terminal') is True,
         'cleanup did not complete with tracked processes terminal')
result='PASS_STALE_SOURCE_REFUSED_ZERO_INPUT' if not failures else 'FAIL_OR_HOLD'
out={'schema':'agent-interface/issue-3370-stale-source-audit-v1','result':result,
 'failures':failures,'limits':['single stale-source control only','no host presentation/model receipt boundary',
 'no delayed/no-image/disconnect/cancellation controls','no efficiency or task-success claim']}
(root/'audit.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
print(json.dumps(out,sort_keys=True))
raise SystemExit(0 if not failures else 1)
