"""Verify retained self-use records and saved effects; no replay or extraction."""
import base64,hashlib,io,json,tarfile,zipfile
from pathlib import Path
from xml.etree import ElementTree as ET
root=Path(__file__).parent
def require(ok,why):
    if not ok:raise ValueError(why)
with tarfile.open(root/'raw.tar.gz') as archive:
    members=archive.getmembers()
    require(all(m.isfile() for m in members),'regular files only')
    require(len(members)==len({m.name for m in members}),'unique paths')
    files={m.name:archive.extractfile(m).read() for m in members}
manifest=json.loads((root/'manifest.json').read_text())
require(set(files)==set(manifest),'inventory')
for name,digest in manifest.items():require(hashlib.sha256(files[name]).hexdigest()==digest,name)
def read(name):return json.loads(files[name])
def lines(name):return [json.loads(row) for row in files[name].decode().splitlines()]
c='native-primary-twoapp-client-01';run=c+'-allocation/run/'
summary=read(c+'/SUMMARY.json');timings=lines(c+'/host-timing.jsonl');notes=lines(c+'/primary-review.jsonl')
require(read(c+'/PLAN.json')['base']==read('SOURCE.json')['commit'],'pinned source')
require(len(timings)==summary['mcp_calls']==11,'all call timings')
images=0
for i,timing in enumerate(timings,1):
    request=read(c+f'/transport/request-{i}.json');reply=read(c+f'/transport/reply-{i}.json')
    require(request['id']==reply['id']==timing['call']==i,'call identity')
    require(request['tool']==reply['tool']==timing['tool'],'tool identity')
    require(reply['status']=='returned' and not reply['result']['isError'],'returned tool result')
    require(timing['sent_host_ms']<=timing['resolved_host_ms']<=timing['presented_callback_host_ms'],'timing order')
    blocks=[b for b in reply['result']['content'] if b['type']=='image'];images+=len(blocks)
    require(len(blocks)==timing['image_blocks'],'image count')
    if blocks:
        metadata=json.loads(reply['result']['content'][0]['text']);ref=metadata['image_reference']
        data=base64.b64decode(blocks[0]['data'],validate=True)
        require(hashlib.sha256(data).hexdigest()==ref['sha256'],'image digest')
        require(data==files[run+ref['relative_path']],'same retained pixels')
require(images==summary['image_blocks']==8,'total images')
actions=read(run+'actions.json')
require(len(actions)==summary['input_programs']==5,'input program count')
require(all(a['result']['status']=='completed' and all(r['verified'] for r in a['result']['execution']['releases']) for a in actions),'completed inputs and releases')
requests=[read(run+f'request-{i}.json') for i in range(1,9)]
require(sum(r.get('interaction')=='observe' for r in requests)==summary['explicit_observations']==2,'explicit observations')
require(requests[-1].get('finish') is True,'explicit finish')
require(notes[-1]['complete'] is True and notes[-1]['host_ms']<timings[9]['sent_host_ms'],'primary review before oracle request')
require(abs(summary['first_send_to_finish_callback_ms']-(timings[9]['presented_callback_host_ms']-timings[0]['sent_host_ms']))<1e-6,'elapsed interval')
within=sum(t['presented_callback_host_ms']-t['sent_host_ms'] for t in timings[:10])
require(abs(within-summary['sum_send_to_callback_through_finish_ms'])<1e-6,'within-call sum')
require(abs(summary['between_call_intervals_through_finish_ms']-(summary['first_send_to_finish_callback_ms']-within))<1e-6,'between-call remainder')
require(read(run+'evaluation.json')['success'] is True,'independent evaluation')
with zipfile.ZipFile(io.BytesIO(files[run+'sheet.xlsx'])) as workbook:
    sheet=ET.fromstring(workbook.read('xl/worksheets/sheet1.xml'))
ns={'s':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
cells={x.attrib['r']:x.find('s:v',ns).text for x in sheet.findall('.//s:c',ns) if x.find('s:v',ns) is not None}
require(cells.get('A1')=='753' and cells.get('A2')=='599','saved Calc values')
svg=ET.fromstring(files[run+'shape.svg']);rect=next(e for e in svg.iter() if e.attrib.get('id')=='r')
require({k:rect.get(k) for k in ('x','y','width','height','transform')}=={'x':'56','y':'50','width':'40','height':'30','transform':None},'saved SVG geometry')
terminal=json.loads(read(c+'/transport/reply-11.json')['result']['content'][0]['text'])['allocation']
require(terminal['status']=='terminal' and terminal['returncode']==0,'owner terminal')
require(read(c+'/transport/exit.json')['code']==read(c+'/EXIT.json')['code']==0,'relay terminal')
print(f'PASS {len(files)} files; 11 calls, 8 images, 5 input programs, 2 observations; both saved effects verified')