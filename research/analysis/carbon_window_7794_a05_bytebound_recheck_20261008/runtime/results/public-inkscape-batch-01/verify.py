import hashlib,json,tarfile,xml.etree.ElementTree as ET
from pathlib import Path
root=Path(__file__).parent
rows=json.loads((root/'manifest.json').read_text())['files']
with tarfile.open(root/'raw.tar.gz') as archive:
 members=archive.getmembers()
 if len(members)!=len(rows) or {m.name for m in members}!={r['path'] for r in rows}:raise ValueError('member mismatch')
 data={}
 for row in rows:
  member=archive.getmember(row['path'])
  if not member.isfile():raise ValueError('non-file member')
  raw=archive.extractfile(member).read()
  if len(raw)!=row['bytes'] or hashlib.sha256(raw).hexdigest()!=row['sha256']:raise ValueError('digest mismatch')
  data[row['path']]=raw
base='results-local/public-inkscape-batch-01/'
svg=ET.fromstring(data[base+'drawing.svg'])
rects=[{k:float(node.attrib[k]) for k in ['x','y','width','height']} for node in svg.iter('{http://www.w3.org/2000/svg}rect')]
if len(rects)!=2 or not all(q['width']>0 and q['height']>0 and q['x']>=0 and q['y']>=0 and q['x']+q['width']<=400 and q['y']+q['height']<=240 for q in rects):raise ValueError('rectangle page predicate')
a,b=rects
if not (a['x']+a['width']<=b['x'] or b['x']+b['width']<=a['x'] or a['y']+a['height']<=b['y'] or b['y']+b['height']<=a['y']):raise ValueError('overlap')
if not all(q['returncode'] is not None for q in json.loads(data[base+'cleanup.json'])):raise ValueError('live owned process')
def metadata(attempt):
 reply=json.loads(data[base+f'host-records/reply-{attempt}.json'])
 return reply,[json.loads(b['text']) for b in reply['result']['content'] if b['type']=='text' and 'call_id' in b['text']][0]
for attempt in (1,2,3):
 reply,report=metadata(attempt)
 receipt=json.loads(data[base+f'host-records/review-{attempt}.json'])
 if receipt['reply_sha256']!=hashlib.sha256(data[base+f'host-records/reply-{attempt}.json']).hexdigest():raise ValueError('review reply mismatch')
 if len([b for b in reply['result']['content'] if b['type']=='image'])!=1:raise ValueError('missing image')
 if attempt>1 and (report['outcome_summary']['execution_status']!='completed' or report['outcome_summary']['input_release_verified'] is not True):raise ValueError('dispatch release')
_,summary=metadata(2);lookup,full=metadata(4)
if summary['receipt']['source']['sha256']!=full['receipt']['source']['sha256']:raise ValueError('retrieval identity')
if any(b['type']=='image' for b in lookup['result']['content']):raise ValueError('unexpected lookup image')
_,closed=metadata(5)
if closed['status']!='closed' or closed['release']['verified'] is not True:raise ValueError('close release')
print('PASS: member digests, SVG task predicates, review attribution, lookup identity and recorded cleanup')
