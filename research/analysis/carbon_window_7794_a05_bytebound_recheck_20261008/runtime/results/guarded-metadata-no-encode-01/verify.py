"""Read frozen records only; no archive extraction, capture or input replay."""
import pathlib,json,hashlib,tarfile,io,zipfile,base64
root=pathlib.Path(__file__).resolve().parent
def check(ok,why):
 if not ok:raise ValueError(why)
def sha(b):return hashlib.sha256(b).hexdigest()
manifest=json.loads((root/'manifest.json').read_text());archive=(root/'raw.tar.gz').read_bytes();check(sha(archive)==manifest['archive_sha256'],'archive digest')
with tarfile.open(fileobj=io.BytesIO(archive),mode='r:gz') as t:
 members=t.getmembers();check(all(x.isfile() and not x.name.startswith('/') and '..' not in pathlib.Path(x.name).parts for x in members),'unsafe archive');check(len({x.name for x in members})==len(members),'duplicate names');raw={x.name:t.extractfile(x).read() for x in members}
check(set(raw)=={x['path'] for x in manifest['files']},'manifest coverage')
for x in manifest['files']:check(len(raw[x['path']])==x['bytes'] and sha(raw[x['path']])==x['sha256'],'member '+x['path'])
def j(n):return json.loads(raw[n])
check(j('PLAN.json')['source_revision']=='90e505c7045c443ec9b0f1bfd623f84c13d1652d','source')
check(sha(raw['candidate.pyz'])==j('MANIFEST.json')['sha256'],'package digest')
with zipfile.ZipFile(io.BytesIO(raw['candidate.pyz'])) as z:
 for n in ['runtime/cli_v1/mcp_server.py','runtime/cli_v1/guarded_presentation.py','runtime/cli_v1/review.py']:check(z.read(n)==raw['source/'+n],'packaged source')
check(b'AssertionError: 1 != 0' in raw['tdd-red.txt'],'red reproduces unwanted encoding')
check(b"'full' != 'brief'" in raw['projection-red.txt'],'brief regression red')
check(b'Ran 236 tests' in raw['cli-tests-with-required-source.txt'] and raw['cli-tests-with-required-source.txt'].rstrip().endswith(b'OK'),'wide tests')
native=j('native-check/result.json');check(native['status']=='PASS' and all(x['returncode']==0 for x in native['suites']),'shared checks')
for row in native['suites']:
 for log in row['logs'].values():check(sha(raw['native-check/'+log['file']])==log['sha256'],'native log digest')
rep={i:j(f'allocation/host/reply-{i}.json') for i in range(1,5)};req={i:j(f'allocation/host/request-{i}.json') for i in range(1,5)};data={i:json.loads(rep[i]['result']['content'][0]['text']) for i in rep}
check([r['tool'] for r in rep.values()]==['interface_guarded_observe','interface_results','interface_results','interface_close'],'finite public sequence')
for i,r in rep.items():check(r['status']=='returned' and r['sdk_entry_ns']<=r['sdk_return_ns'] and req[i]['tool']==r['tool'],'SDK')
check(req[2]['arguments']=={'call_id':data[1]['call_id'],'include_image':False},'explicit omission')
check(data[2]['operation_invoked'] is False and data[3]['operation_invoked'] is False,'historical no invocation')
check(data[2]['source']==data[1]['source']==data[3]['source'] and data[2]['observation_report']==data[1]['observation_report']==data[3]['observation_report'],'same observation')
check(data[2]['image_status']=='image' and data[2]['image_delivery']=='omitted_by_request' and len(rep[2]['result']['content'])==1,'omitted shape')
check(rep[1]['result']['content'][1]['data']==rep[3]['result']['content'][1]['data'],'default image bytes')
observations=[n for n in raw if n.startswith('allocation/server/guarded-session-') and pathlib.Path(n).name.startswith('observation-')];check(len(observations)==1,'one native capture')
o=j(observations[0]);check(o['sequence']==1 and o['image_source']=='exact_capture_rgb_handoff','current capture')
a=o['native']['artifact'];prefix='/var/tmp/agent-interface-integrated-main/results-local/guarded-metadata-no-encode-01/';check(a['path'].startswith(prefix),'artifact scope');image=raw[a['path'][len(prefix):]];check(sha(image)==a['sha256'] and a['source_raw_sha256']==o['native']['sha256'],'PNG/raw link')
check(base64.b64decode(rep[1]['result']['content'][1]['data'],validate=True)==image,'delivered PNG')
check(data[4]['status']=='closed' and data[4]['release_attempted'] is False and data[4]['connection_close_attempted'] is True,'observation-only close')
check(j('allocation/evaluation-at-close.json')['record_count']==0,'no task submission')
check(j('allocation/host/exit.json')['code']==0 and j('live-check.json')['fixture_terminal']['exit_code']==0,'terminal')
check([x['returncode'] for x in j('allocation/cleanup.json')]==[0,1,0],'child accounting')
check(j('live-check.json')['original_raw_sha256']==j('live-check.json')['after_raw_sha256']==sha(raw['allocation/server/'+data[1]['call_id']+'/report.json']),'raw unchanged')
print(json.dumps({'status':'PASS_GUARDED_METADATA_REVIEW_SCOPED','raw_files':len(raw),'public_calls':4,'native_captures':1,'task_input_calls':0,'default_image_unchanged':True,'metadata_lookup_no_capture_or_replay':True,'limits':'Encoding count proven by regression red/green; live use verifies retained metadata/image. No CPU, wall-clock, token/cost or task-quality benefit measured.'},indent=2))
