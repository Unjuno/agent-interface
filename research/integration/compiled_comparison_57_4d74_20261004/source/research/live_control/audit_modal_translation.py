"""Replay geometry translations and verify wrong/stale coordinates abstain."""
import hashlib,json
from pathlib import Path
from PIL import Image
from modal_visual_predicate_v2 import ModalVisualPredicate
HERE=Path(__file__).resolve().parent;root=HERE/'results/modal-translation-01'
for name,h in json.loads((root/'sources.json').read_text()).items():assert hashlib.sha256((HERE/name).read_bytes()).hexdigest()==h
config=json.loads((HERE/'results/modal-predicate-01/config.json').read_text())
predicate=ModalVisualPredicate(Image.open(HERE/'results/modal-focus-01/tab-0.png').convert('RGB'),**config)
rows=json.loads((root/'results.json').read_text());hashes={}
for row in rows:
    image=Image.open(root/row['image']).convert('RGB')
    actual=predicate.inspect_at(image,row['offset']);assert actual==row['translated']
    assert (actual['status']=='visual_candidate')==(row['expected_focus']=='excel')
    assert predicate.inspect_at(image,[0,0])['status']=='abstain'
    assert predicate.inspect_at(image,[2000,0])['status']=='unsupported_region'
    assert row['geometry_before']==row['geometry_after']
    hashes[row['image']]=hashlib.sha256((root/row['image']).read_bytes()).hexdigest()
(root/'audit.json').write_text(json.dumps(dict(verified_cases=4,unchanged_template_and_threshold=True,stale_offset_abstains=True,out_of_bounds_rejected=True,image_hashes=hashes),indent=2)+'\n')
print('4 translated cases replay exactly; stale offset and bounds controls pass.')
