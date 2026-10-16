import json,hashlib
from collections import Counter
from pathlib import Path
from PIL import Image
from session_v9 import Decoder
p=Path(__file__).resolve().parent
root=p/'results/journal-stall-02'
for name,digest in json.loads((root/'sources.json').read_text()).items():assert hashlib.sha256((p/name).read_bytes()).hexdigest()==digest
rows=[]
for result in json.loads((root/'results.json').read_text()):
 d=root/result['case'];events=[json.loads(x) for x in (d/'events.jsonl').read_text().splitlines()];receipts=[json.loads(x) for x in (d/'receipts.jsonl').read_text().splitlines()]
 order_ok=[r['source_event'] for r in receipts]==[r['event'] for r in events]
 assert Counter(r['source_event'] for r in receipts)==Counter(r['event'] for r in events)
 assert order_ok == (result['case']!='write_cancel')
 assert len(receipts)==result['journal_confirmed']
 assert result['terminal']['status']==('expired' if result['case'].endswith('expiry') else 'cancelled')
 assert not any(r.get('operation')=='continue_move' or r.get('continuation') for r in events)
 decoder=Decoder('live-control');count=0
 for r in events:
  if r['event']!='observation':continue
  count+=1;f=decoder.accept((d/f'{count:03d}.ait').read_bytes())
  with Image.open(d/Path(r['image']).name) as im:assert im.size==(f.width,f.height) and im.tobytes()==f.pixels
 rows.append(dict(case=result['case'],frames=count,receipts=len(receipts),receipt_order_preserved=order_ok,status=result['terminal']['status']))
(root/'audit.json').write_text(json.dumps(rows,indent=2)+'\n');print(json.dumps(rows))
