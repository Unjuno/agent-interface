from pathlib import Path
import sys,json,copy
sys.path.insert(0,'research/live_control')
from agent_review import review_native
from receipt_references import expand_native_receipt
size=lambda v:len(json.dumps(v,ensure_ascii=False,separators=(',',':')).encode('utf-8'))
root=Path('results-local/native-compact-self-use-01');rows=[]
for n in range(1,4):
 full=review_native(root/f'reply-{n}.json',root)
 compact=review_native(root/f'reply-{n}.json',root,compact=True)
 assert expand_native_receipt(compact['receipt'])==full['receipt']
 assert compact['image']==full['image']
 full_image_bytes=size(full);compact_image_bytes=size(compact)
 full.pop('image');compact.pop('image')
 row={'stage':n,'full_metadata_bytes':size(full),'compact_metadata_bytes':size(compact),'full_with_base64_bytes':full_image_bytes,'compact_with_base64_bytes':compact_image_bytes,'exact_roundtrip':True}
 rows.append(row)
(root/'comparison.json').write_text(json.dumps(rows,indent=2)+'\n')
print(json.dumps(rows))
