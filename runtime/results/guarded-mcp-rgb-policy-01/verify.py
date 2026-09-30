"""Read-only audit of exact retained bytes; does not launch a GUI or replay input."""
import hashlib, io, json, tarfile, zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parent
PREFIX='/var/tmp/agent-interface-integrated-main/results-local/guarded-mcp-rgb-policy-01/'
def require(ok,message):
 if not ok:raise ValueError(message)
def sha(data):return hashlib.sha256(data).hexdigest()
manifest=json.loads((ROOT/'manifest.json').read_text())
archive=(ROOT/'raw.tar.gz').read_bytes()
require(sha(archive)==manifest['archive_sha256'],'archive hash')
with tarfile.open(fileobj=io.BytesIO(archive),mode='r:gz') as t:
 members=t.getmembers()
 require(all(m.isfile() and not m.name.startswith('/') and '..' not in Path(m.name).parts for m in members),'unsafe member')
 require(len({m.name for m in members})==len(members),'duplicate member')
 raw={m.name:t.extractfile(m).read() for m in members}
require(set(raw)=={r['path'] for r in manifest['files']},'manifest coverage')
for row in manifest['files']:
 b=raw[row['path']];require(len(b)==row['bytes'] and sha(b)==row['sha256'],'file hash '+row['path'])
def j(name):return json.loads(raw[name])
def reply(route,n):
 row=j(f'{route}/public-host/reply-{n}.json')
 require(row['status']=='returned' and row['sdk_entry_ns']<=row['sdk_return_ns'],'SDK boundary')
 return row,json.loads(row['result']['content'][0]['text'])
a,baseline=reply('baseline',1)
require(baseline['status']=='refused' and baseline['input_dispatched'] is False and 'no matching current capture RGB handoff' in baseline['error'],'baseline reproduction')
require(j('baseline/finished.json')['payload'] is None,'baseline no saved input')
require(j('candidate/payload.json')=={'value':'rgb_public_01','saves':1},'independent effect')
rows=[reply('candidate',i) for i in range(1,11)]
require([m['status'] for _,m in rows]==['observed','minted','refused','completed','completed','completed','completed','refused','completed','closed'],'complete public call accounting')
require(rows[2][1]['result']['backend_emissions']==0,'invalid schema input zero')
require(rows[7][1]['result']['input_dispatched'] is False and rows[7][1]['result']['guard_checks'][0]['status']=='MISSING','changed region refusal')
require(rows[8][1]['operation_invoked'] is False,'read-only lookup')
require(rows[8][1]['call_id']==rows[6][1]['call_id'],'lookup identity')
releases=[]
for transport,m in rows:
 if transport['tool']=='interface_guarded_input' and m['status']=='completed':
  releases.extend(m['result']['execution']['releases'])
require(len(releases)==4 and all(x['verified'] and not x['keys_down'] and not x['buttons_down'] for x in releases),'operation releases')
require(rows[-1][1]['release']['verified'],'close release')
observations=[]
for name in raw:
 if name.startswith('candidate/server/guarded-session-') and Path(name).name.startswith('observation-'):
  ob=j(name);art=ob['native']['artifact']
  require(ob['image_source']=='exact_capture_rgb_handoff','RGB handoff')
  require(art['path'].startswith(PREFIX),'owned artifact')
  require(sha(raw[art['path'][len(PREFIX):]])==art['sha256'],'PNG hash')
  require(art['source_raw_sha256']==ob['native']['sha256'],'raw link')
  observations.append(ob['sequence'])
require(sorted(observations)==list(range(1,22)),'all 21 observations')
for route in ('baseline','candidate'):
 require(j(route+'/public-host/exit.json')['code']==0,'relay exit')
 require([x['returncode'] for x in j(route+'/cleanup.json')]==[0,1,-15],'private process cleanup accounting')
 with zipfile.ZipFile(io.BytesIO(raw[route+'.pyz'])) as z:
  packaged=z.read('runtime/cli_v1/mcp_guarded.py')
  if route=='candidate':require(packaged==raw['candidate-mcp_guarded.py'],'tested package source')
require(j('native-checks-with-deps/result.json')['status']=='PASS','native suites')
require(j('native-checks/result.json')['status']=='FAIL','first missing-dependency failure retained')
usage=j('model-usage-projection.json')['calls']
require(len(usage)==12 and all(len(x['usage_records_before_output'])==1 for x in usage),'unique local usage association')
for x in usage:
 require(x['local_context']['model']=='gpt-6.1-sol','local model context')
 u=x['usage_records_before_output'][0]['usage']
 require(u['total_tokens']==u['input_tokens']+u['output_tokens'],'usage accounting')
result={'status':'PASS_PUBLIC_GUARDED_RGB_REPAIR_SCOPED','files':len(raw),'candidate_calls':10,'observations':len(observations),'completed_input_releases':len(releases),'payload':j('candidate/payload.json'),'model_usage_projection_calls':len(usage),'sdk_ms':[round((a['sdk_return_ns']-a['sdk_entry_ns'])/1e6,3) for a,_ in rows],'limits':'One Tk integration case with retained refusal and two semantic repairs, not a matched six-task acceptance or human/model latency/cost improvement.'}
print(json.dumps(result,indent=2))
