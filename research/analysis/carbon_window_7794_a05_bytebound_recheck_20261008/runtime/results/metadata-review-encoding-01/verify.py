import hashlib,json,tarfile
from pathlib import Path
root=Path(__file__).parent
expected=json.loads((root/'manifest.json').read_text())['files']
with tarfile.open(root/'raw.tar.gz') as archive:
 members=archive.getmembers()
 if len(members)!=len(expected) or {m.name for m in members}!={r['path'] for r in expected}:raise ValueError('member mismatch')
 data={}
 for row in expected:
  member=archive.getmember(row['path'])
  if not member.isfile():raise ValueError('non-file member')
  value=archive.extractfile(member).read()
  if len(value)!=row['bytes'] or hashlib.sha256(value).hexdigest()!=row['sha256']:raise ValueError('member digest')
  data[row['path']]=value
base='results-local/metadata-review-encoding-01/'
for name,omitted_encodings in [('baseline',1),('candidate',0)]:
 prefix=base+name+'/'
 probe=json.loads(data[prefix+'probe.json'])
 if probe['rows'][0]['encoding_calls']!=omitted_encodings or probe['rows'][1]['encoding_calls']!=1:raise ValueError('encoding count')
 def metadata(label):return json.loads(json.loads(data[prefix+label+'.json'])['content'][0]['text'])
 full=metadata('included');omitted=metadata('omitted');bad=metadata('altered-image')
 if omitted.pop('image_delivery')!='omitted_by_request' or full!=omitted:raise ValueError('metadata parity')
 if bad['image_status']!='needs_review':raise ValueError('corruption refusal')
 if full['receipt']['source']['raw_report']!=json.loads(data[prefix+'lookup-original-report.json']):raise ValueError('raw report identity')
 if probe['input_dispatched'] is not False:raise ValueError('scope')
print('PASS: archive identity, recorded encoding counts, metadata parity and corruption refusal')
