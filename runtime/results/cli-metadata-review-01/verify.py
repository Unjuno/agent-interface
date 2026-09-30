import hashlib,json,tarfile,base64
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
  if len(raw)!=row['bytes'] or hashlib.sha256(raw).hexdigest()!=row['sha256']:raise ValueError('member digest')
  data[row['path']]=raw
prefix='results-local/cli-metadata-review-01/'
def response(case):return json.loads(data[prefix+case+'.stdout.json'])
full=response('included-file');omitted=response('omitted-file');stdin=response('omitted-stdin')
if omitted!=dict(full,image=None,image_delivery='omitted_by_request'):raise ValueError('metadata parity')
if stdin['image_reference']!=omitted['image_reference'] or stdin['outcome_summary']!=omitted['outcome_summary']:raise ValueError('stdin parity')
if response('changed-report')['status']!='invalid_receipt':raise ValueError('digest refusal')
source=data['results-local/cli-summary-primary-01/call-4/report.json'];digest=hashlib.sha256(source).hexdigest()
if full['receipt']['source']['sha256']!=digest or stdin['receipt']['source']['sha256']!=digest:raise ValueError('source identity')
if hashlib.sha256(base64.b64decode(full['image']['data'])).hexdigest()!=full['image_reference']['sha256']:raise ValueError('image identity')
recipe=json.loads(data[prefix+'retrieval-recipe.json'])
if recipe['arguments']['no_image'] is not True or recipe['arguments']['expected_report_sha256']!=digest:raise ValueError('recipe')
print('PASS: archive identity, file/stdin parity, image/source identity and recipe digest')
