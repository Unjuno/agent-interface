"""Recount retained public replies, without a server, capture or input."""
import copy
import hashlib
import json
from pathlib import Path
import sys
import tarfile
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from runtime.cli_v1.receipt_references import compact_receipt, expand_receipt

def require(value, message):
    if not value:
        raise ValueError(message)

root = Path(__file__).resolve().parent
inputs = json.loads((root / 'inputs.json').read_text())
sources = {}
for name in {item['source'] for item in inputs}:
    archive = root.parent / name / 'raw.tar.gz'
    with tarfile.open(archive) as retained:
        sources[name] = (hashlib.sha256(archive.read_bytes()).hexdigest(),
                        {m.name: retained.extractfile(m).read() for m in retained.getmembers() if m.isfile()})
rows = []
for item in inputs:
    data = item['reply_text'].encode()
    require(hashlib.sha256(data).hexdigest() == item['reply_sha256'], 'reply hash')
    archive_hash, members = sources[item['source']]
    require(archive_hash == item['archive_sha256'], 'source archive identity')
    require(members[item['member']] == data, 'exact original member')
    reply = json.loads(data)
    shown = json.loads(reply['result']['content'][0]['text'])
    full = expand_receipt(shown['receipt'])
    projected = compact_receipt(full, report_refs=True)
    require(expand_receipt(projected) == full, 'lossless receipt expansion')
    candidate = copy.deepcopy(shown)
    candidate['receipt'] = projected
    require({k:v for k,v in candidate.items() if k != 'receipt'} ==
            {k:v for k,v in shown.items() if k != 'receipt'}, 'unchanged envelope')
    new_reply = copy.deepcopy(reply)
    new_reply['result']['content'][0]['text'] = json.dumps(candidate, allow_nan=False)
    require(new_reply['result']['content'][1:] == reply['result']['content'][1:], 'unchanged image blocks')
    original_bytes = len(reply['result']['content'][0]['text'].encode())
    projected_bytes = len(new_reply['result']['content'][0]['text'].encode())
    rows.append({'source':item['source'],'member':item['member'],'tool':reply['tool'],
                 'original_schema':shown['receipt']['schema'], 'projected_schema':projected['schema'],
                 'original_text_bytes':original_bytes,'projected_text_bytes':projected_bytes,
                 'saved_text_bytes':original_bytes-projected_bytes})
summary = {'scope':'offline exact retained text projection; no new capture or input; not model tokens/cost',
           'replies':len(rows),'original_text_bytes':sum(r['original_text_bytes'] for r in rows),
           'projected_text_bytes':sum(r['projected_text_bytes'] for r in rows),'rows':rows}
expected = root / 'result.json'
if '--record' in sys.argv:
    require(not expected.exists(), 'never replace frozen result')
    expected.write_text(json.dumps(summary,indent=2)+'\n')
else:
    require(json.loads(expected.read_text()) == summary, 'frozen recount')
print(json.dumps(summary,indent=2))
