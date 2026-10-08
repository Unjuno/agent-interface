"""Audit frozen public entry evidence without extraction, GUI launch or replay."""
import hashlib,io,json,tarfile
from pathlib import Path
root=Path(__file__).resolve().parent
prefix='/var/tmp/agent-interface-integrated-main/results-local/public-six-task-comparison-01/'
def check(ok,why):
 if not ok:raise ValueError(why)
def sha(b):return hashlib.sha256(b).hexdigest()
m=json.loads((root/'manifest.json').read_text());a=(root/'raw.tar.gz').read_bytes()
check(sha(a)==m['archive_sha256'],'archive hash')
with tarfile.open(fileobj=io.BytesIO(a),mode='r:gz') as t:
 ms=t.getmembers();check(all(x.isfile() and not x.name.startswith('/') and '..' not in Path(x.name).parts for x in ms),'unsafe member')
 check(len({x.name for x in ms})==len(ms),'duplicate member')
 raw={x.name:t.extractfile(x).read() for x in ms}
check(set(raw)=={x['path'] for x in m['files']},'coverage')
for x in m['files']:check(len(raw[x['path']])==x['bytes'] and sha(raw[x['path']])==x['sha256'],'member '+x['path'])
def j(n):return json.loads(raw[n])
check(j('PLAN.json')['source_revision']=='b1ffe8f23e74292ee99e44401270bc31438782d3','source freeze')
check(sha(raw['runtime.pyz'])==j('MANIFEST.json')['sha256'],'package')
check(len(j('direct/STOP.json')['tasks'])==6 and all(x['status']=='unattempted' for x in j('direct/STOP.json')['tasks']),'all direct task rows')
check(j('direct/evaluation-at-close.json')['record_count']==0,'no baseline submission')
r=j('direct/host/reply-2.json');p=json.loads(r['result']['content'][0]['text'])['receipt']['source']['raw_report']['result']
check(p['status']=='refused' and p['backend_emissions']==0 and p['detail']=='program schema mismatch','initial refusal')
evals=j('guarded/evaluation-at-close.json');check(evals['success'] and evals['record_count']==6,'final independent evaluation')
records=[json.loads(line) for line in raw['guarded/submission-history.jsonl'].splitlines()]
check(len(records)==6,'six exact submissions')
for i,x in enumerate(records,1):
 check(x['task_id']==f'task-{i}' and x['submitted_values']==[f't991930-{i}'] and x['exact'] is True,'independent token')
 check(x['layout']==('A' if i<=3 else 'B'),'layout')
rows=[];releases=[]
for i in range(1,26):
 rep=j(f'guarded/host/reply-{i}.json');check(rep['status']=='returned' and rep['sdk_entry_ns']<=rep['sdk_return_ns'],'SDK')
 p=json.loads(rep['result']['content'][0]['text']);rows.append(p)
 if rep['tool']=='interface_guarded_input' and p['status']=='completed':releases+=p['result']['execution']['releases']
check(len(releases)==18 and all(x['verified'] and not x['keys_down'] and not x['buttons_down'] for x in releases),'18 releases')
refusals=[x for x in rows if x['status']=='refused'];check(len(refusals)==1,'single refusal')
check(refusals[0]['result']['input_dispatched'] is False and refusals[0]['result']['guard_checks'][0]['status']=='MISSING','changed layout no input')
check(rows[-2]['operation_invoked'] is False and rows[-2]['call_id']==rows[-3]['call_id'],'read-only continuation')
check(rows[-1]['status']=='closed' and rows[-1]['release']['verified'],'close')
seq=[]
for n in raw:
 if n.startswith('guarded/server/guarded-session-') and Path(n).name.startswith('observation-'):
  o=j(n);a=o['native']['artifact'];check(o['image_source']=='exact_capture_rgb_handoff','RGB')
  check(a['path'].startswith(prefix) and sha(raw[a['path'][len(prefix):]])==a['sha256'],'PNG')
  check(a['source_raw_sha256']==o['native']['sha256'],'raw source')
  seq.append(o['sequence'])
check(sorted(seq)==list(range(1,82)),'81 captures')
for route in ('direct','guarded'):
 check(j(route+'/host/exit.json')['code']==0,'transport exit')
 check([x['returncode'] for x in j(route+'/cleanup.json')]==({'direct':[0,1,1],'guarded':[0,1,0]}[route]),'private cleanup accounting')
 check(j('terminal.json')[route]['exit_code']==0,'outer terminal')
metrics=j('metrics.json');check(metrics['status']=='HOLD_COMPARISON_INCOMPLETE' and len(metrics['guarded_tasks'])==6,'no promotion')
usage=j('model-usage-projection.json')['calls'];check(len(usage)==23 and all(len(x['usage_records_before_output'])==1 for x in usage),'local usage projection')
print(json.dumps({'status':'HOLD_COMPARISON_INCOMPLETE','raw_files':len(raw),'guarded_exact_tasks':6,'direct_tasks_unattempted':6,'guarded_public_calls':25,'guarded_observations':len(seq),'verified_input_releases':len(releases),'changed_state_refusals':1,'read_only_continuation':True,'limits':'No baseline ranking, human-tempo, causal token/cost or overall acceptance claim.'},indent=2))
