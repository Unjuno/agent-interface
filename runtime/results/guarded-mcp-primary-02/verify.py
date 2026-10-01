"""Read-only raw bundle audit. Integrity/reconciliation, not model comprehension."""
import base64,hashlib,json,tarfile
from pathlib import Path
ROOT=Path(__file__).resolve().parent
PREFIX='results-local/guarded-mcp-primary-02/'
def require(condition,message):
    if not condition:raise SystemExit(message)
def sha(data):return hashlib.sha256(data).hexdigest()
manifest=json.loads((ROOT/'manifest.json').read_text());raw={}
with tarfile.open(ROOT/'raw.tar.gz','r:gz') as archive:
    members=archive.getmembers()
    require(len(members)==len(manifest),'member count mismatch')
    for member in members:
        require(member.isfile() and member.name in manifest and member.name not in raw,'unexpected or duplicate member')
        data=archive.extractfile(member).read();expected=manifest[member.name]
        require(len(data)==expected['bytes'] and sha(data)==expected['sha256'],'hash mismatch: '+member.name)
        raw[member.name]=data

def read(name):return json.loads(raw[PREFIX+name])
requests={i:read(f'transport/request-{i}.json') for i in range(1,33)}
replies={i:read(f'transport/reply-{i}.json') for i in range(1,33)}
reports={}
for i,r in replies.items():
    require(r['id']==i and requests[i]['id']==i and r['tool']==requests[i]['tool'] and
            r['status']=='returned' and r['next_id']==i+1,'relay identity mismatch')
    reports[i]=json.loads(r['result']['content'][0]['text'])
    v=reports[i]
    images=[b for b in r['result']['content'] if b['type']=='image']
    if images:
        require(len(images)==1,'multiple images')
        artifact=v['source']['native']['artifact']
        png=base64.b64decode(images[0]['data'],validate=True)
        require(sha(png)==artifact['sha256'],'returned image differs from source artifact')
        relative=artifact['path'].split('/agent-interface-integrated-main/',1)[1]
        require(raw[relative]==png,'retained artifact differs from returned image')
    if r['tool']=='interface_guarded_input' and v['status']=='completed':
        require(v['result']['recovery_required'] is False,'unexpected recovery')
        releases=v['result']['execution']['releases']
        require(bool(releases) and all(x['verified'] is True and x['keys_down']==[] and x['buttons_down']==[] for x in releases),'unverified release')
        require(all(g['status']=='VALID' for g in v['result']['guard_checks']),'completed invalid guard')
        require(v['feedback_status']=='captured' and bool(images),'missing feedback image')

require(sum(r['tool']=='interface_guarded_input' for r in replies.values())==23,'input count')
require(sum(r['tool']=='interface_guarded_input' and reports[i]['status']=='completed' for i,r in replies.items())==22,'completed count')
refusal=reports[17]['result']
require(refusal['status']=='refused' and refusal['input_dispatched'] is False,'stale input emitted')
require(refusal['guard_checks'][0]['stage']=='before_admission' and refusal['guard_checks'][0]['status']=='MISSING','wrong stale control')

review_names=[n for n in raw if n.startswith(PREFIX+'review-') and n.endswith('.json')]
require(len(review_names)==20,'review receipt count')
reviews={}
for name in review_names:
    note=json.loads(raw[name]);i=note['relay_id'];r=replies[i];v=reports[i]
    require(note['call_id']==v['call_id'] and note['source_sequence']==v['source']['sequence'] and
            note['observation_id']==v['source']['observation_id'],'review source mismatch')
    require(note['reply_sha256']==sha(raw[PREFIX+f'transport/reply-{i}.json']),'review reply hash')
    images=[{'mime_type':b['mimeType'],'sha256':sha(base64.b64decode(b['data'],validate=True))} for b in r['result']['content'] if b['type']=='image']
    require(note['images']==images and bool(images),'review image identity')
    reviews[(note['task'],note['phase'])]=(note,name)
for n,(entered,saved) in enumerate([(5,6),(9,10),(13,14),(20,21),(24,25),(28,29)],1):
    note,path=reviews[(f'task-{n}','entered')]
    require(note['relay_id']==entered and reviews[(f'task-{n}','saved')][0]['relay_id']==saved,'task review attribution')
    # Coarse filesystem consistency only: equal timestamps cannot prove order.
    require(manifest[path]['mtime_ns']<=manifest[PREFIX+f'transport/request-{saved}.json']['mtime_ns'],'review file timestamp later than Save request')
    texts=[x['text'] for x in requests[entered]['arguments']['tail'] if x['op']=='text']
    require(texts==[f't991329-{n}'],'unexpected input value')

history=[json.loads(line) for line in raw[PREFIX+'submission-history.jsonl'].splitlines()]
goal=read('goal.json');expected={t['task_id']:t['token'] for t in goal['tasks']}
require(len(history)==6 and len({r['task_id'] for r in history})==6,'duplicate or missing history')
for row in history:require(row['task_id'] in expected and row['submitted_values']==[expected[row['task_id']]],'saved value mismatch')
require(read('evaluation.json')['success'] is True,'oracle did not pass')
require(read('finish.json')['primary_review_complete'] is True,'missing finish')
require(read('fixture-exit.json')['exit_code']==0 and read('transport/exit.json')['code']==0,'nonzero runner or transport')
require(len(read('cleanup.json'))==3 and all(type(p['returncode']) is int for p in read('cleanup.json')),'live or missing child')
closed=reports[31]
require(closed['status']=='closed' and closed['connection_close_attempted'] is True and closed['release']['verified'] is True and closed['release']['keys_down']==[] and closed['release']['buttons_down']==[],'close failed')
require(not any(b['type']=='image' for b in replies[30]['result']['content']),'omitted image delivered')
require(reports[30]['operation_invoked'] is False and reports[32]['operation_invoked'] is False,'retrieval invoked operation')
require(reports[29]['result']==reports[32]['result'] and reports[29]['source']==reports[32]['source'],'retained result changed')
require(replies[29]['result']['content'][1]==replies[32]['result']['content'][1],'retained image changed')

build=json.loads(raw['results-local/guarded-mcp-build-02/manifest.json'])
require(sha(raw['results-local/guarded-mcp-build-02/runtime.pyz'])==build['sha256'],'runtime archive mismatch')
require(build['source_revision']=='2998586f5497e12940fe89992a398a2098298887','wrong runtime source')
checks=json.loads(raw['results-local/guarded-mcp-check-02/result.json'])
require(checks['status']=='PASS' and all(s['returncode']==0 for s in checks['suites']),'contract checks failed')
for suite in checks['suites']:
    for log in suite['logs'].values():require(sha(raw['results-local/guarded-mcp-check-02/'+log['file']])==log['sha256'],'test log hash')
print(f'PASS: {len(raw)} files; six exact saves; 20 source-bound declarations; stale refusal; retained image; close. No speed/token/comprehension claim.')