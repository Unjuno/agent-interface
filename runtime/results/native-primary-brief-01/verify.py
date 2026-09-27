"""Verify retained outcomes, images, full fallback and saved files; never replay."""
import base64,hashlib,io,json,tarfile,zipfile
from pathlib import Path
from xml.etree import ElementTree as ET
root=Path(__file__).parent
def require(ok,why):
    if not ok: raise ValueError(why)
with tarfile.open(root/'raw.tar.gz') as archive:
    members=archive.getmembers()
    require(all(m.isfile() for m in members),'regular files')
    require(len(members)==len({m.name for m in members}),'unique names')
    files={m.name:archive.extractfile(m).read() for m in members}
manifest=json.loads((root/'manifest.json').read_text())
require(set(files)==set(manifest),'inventory')
for n,digest in manifest.items(): require(hashlib.sha256(files[n]).hexdigest()==digest,n)
def read(n): return json.loads(files[n])
def lines(n): return [json.loads(x) for x in files[n].decode().splitlines()]
c='native-primary-brief-01';run=c+'-allocation/run/'
s=read(c+'/SUMMARY.json');t=lines(c+'/timing.jsonl');notes=lines(c+'/primary-review.jsonl')
require(read('SOURCE.json')['commit'].startswith(read(c+'/PLAN.json')['commit']),'source commit')
require(len(t)==s['mcp_calls']==12,'all calls')
images=errors=brief=0
for i,row in enumerate(t,1):
    request=read(c+f'/transport/request-{i}.json');reply=read(c+f'/transport/reply-{i}.json')
    require(request['id']==reply['id']==i,'identity')
    require(request['tool']==reply['tool']==row['tool'],'tool')
    require(request['arguments']==row['args'],'arguments')
    require(row['start']<=row['delivered'],'timing')
    require(reply['status']=='returned','transport')
    result=reply['result']
    if result.get('isError'):
        errors+=1; require(i==7 and 'validation error' in result['content'][0]['text'],'preserved caller error');continue
    v=json.loads(result['content'][0]['text'])
    for b in result['content']:
        if b['type']=='image':
            images+=1;data=base64.b64decode(b['data'],validate=True);ref=v['image_reference']
            require(hashlib.sha256(data).hexdigest()==ref['sha256'],'image digest')
            require(data==files[run+ref['relative_path']],'retained pixels')
    if 'presentation' in v:
        if v['presentation']['returned']=='brief':
            brief+=1; require(i in (3,4) and 'receipt' not in v,'normal-only brief')
            retrieval=v['presentation']['retrieve']['arguments'];stage=retrieval['stage']
            require(retrieval['decision_sha256']==hashlib.sha256(files[run+f'request-{stage}.json']).hexdigest(),'exact retrieval identity')
        else: require('receipt' in v,'full fallback')
require((images,errors,brief)==(8,1,2),'counts')
a=read(run+'actions.json');require(len(a)==5,'five actual inputs')
require(all(x['result']['status']=='completed' for x in a),'completed inputs')
requests=[read(run+f'request-{i}.json') for i in range(1,9)]
require(sum(x.get('interaction')=='observe' for x in requests)==2,'two observations')
require('PRIMARY COMPLETE' in notes[-1]['text'] and notes[-1]['at']<t[10]['start'],'review before scoring')
require(read(run+'evaluation.json')['success'] is True,'independent evaluation')
with zipfile.ZipFile(io.BytesIO(files[run+'sheet.xlsx'])) as book:
    sheet=ET.fromstring(book.read('xl/worksheets/sheet1.xml'))
ns={'s':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
cells={x.attrib['r']:x.find('s:v',ns).text for x in sheet.findall('.//s:c',ns) if x.find('s:v',ns) is not None}
require(cells.get('A1')=='877' and cells.get('A2')=='107','saved cells')
rect=next(e for e in ET.fromstring(files[run+'shape.svg']).iter() if e.attrib.get('id')=='r')
require({k:rect.get(k) for k in ('x','y','width','height','transform')}==dict(x='56',y='50',width='40',height='30',transform=None),'saved geometry')
terminal=json.loads(read(c+'/transport/reply-12.json')['result']['content'][0]['text'])['allocation']
require(terminal['status']=='terminal' and terminal['returncode']==0,'owner exit')
require(read(c+'/EXIT.json')['code']==0,'relay exit')
require(read('native-brief-check-01/result.json')['status']=='FAIL','initial failed check retained')
require(read('native-brief-check-02/result.json')['status']=='PASS','corrected check')
require(read('native-brief-stdio-01/CHECK.json')['status']=='PASS','retained MCP check')
for stage in (1,2,3,4,6):
    full=read(f'native-brief-stdio-01/stage-{stage}-full.json')
    projected=read(f'native-brief-stdio-01/stage-{stage}-brief.json')
    require(full['content'][1:]==projected['content'][1:],'MCP image parity')
    fv=json.loads(full['content'][0]['text']);pv=json.loads(projected['content'][0]['text'])
    if pv['presentation']['returned']=='brief':
        restored=read(f'native-brief-stdio-01/stage-{stage}-retrieved.json')
        require(len(restored['content'])==1 and json.loads(restored['content'][0]['text'])['receipt']==fv['receipt'],'exact full retrieval')
    else: require(pv['receipt']==fv['receipt'],'unchanged critical receipt')
require(abs(s['first_send_to_finish_callback_ms']-(t[10]['delivered']-t[0]['start']))<1e-6,'elapsed')
print(f'PASS {len(files)} files; 12 calls, 1 schema error, 2 brief responses, saved effects and retrieval verified')
