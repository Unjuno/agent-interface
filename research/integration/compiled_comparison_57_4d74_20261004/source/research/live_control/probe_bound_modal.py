"""Known captured pixels with explicit synthetic clock/context negatives."""
from dataclasses import replace
import hashlib,json
from pathlib import Path
from PIL import Image
from modal_visual_predicate_v2 import ModalVisualPredicate
from bound_modal_proposal import Context,propose
HERE=Path(__file__).resolve().parent;out=HERE/'results/bound-modal-01';out.mkdir(exist_ok=False)
root=HERE/'results/modal-translation-01'
config=json.loads((HERE/'results/modal-predicate-01/config.json').read_text())
predicate=ModalVisualPredicate(Image.open(HERE/'results/modal-focus-01/tab-0.png').convert('RGB'),**config)
rows=[]
for row in json.loads((root/'results.json').read_text()):
    image=Image.open(root/row['image']).convert('RGB')
    context=Context('test-session',1,1_000_000_000,11,12,tuple(row['geometry_before']))
    result,proposal=propose(predicate,image,context,context,row['base_geometry'],1_010_000_000)
    assert (proposal is not None)==(row['expected_focus']=='excel')
    if proposal is not None:
        assert proposal.revalidate(context,image,1_020_000_000)=='requires_new_admission'
        negatives={}
        for key,value in dict(session='other',sequence=2,capture_ns=1_000_000_001,window=13,focus=14,geometry=(1,2,507,174)).items():
            negatives[key]=proposal.revalidate(replace(context,**{key:value}),image,1_020_000_000)
            assert negatives[key]==key+'_changed'
        assert proposal.revalidate(context,image,1_250_000_000)=='expired'
        assert proposal.revalidate(context,image,999_999_999)=='clock_before_capture'
        other=Image.open(root/row['image'].replace('excel','odf')).convert('RGB')
        assert proposal.revalidate(context,other,1_020_000_000)=='pixels_changed'
        assert propose(predicate,image,context,replace(context,focus=14),row['base_geometry'],1_010_000_000)[1] is None
        rows.append(dict(image=row['image'],accepted_only_as_proposal=True,negative_contexts=negatives))
    else:rows.append(dict(image=row['image'],status=result['status']))
(out/'results.json').write_text(json.dumps(rows,indent=2)+'\n')
paths=[Path(__file__),HERE/'bound_modal_proposal.py',HERE/'modal_visual_predicate.py',HERE/'modal_visual_predicate_v2.py',HERE/'results/modal-focus-01/tab-0.png',root/'results.json']+list(root.glob('*.png'))
(out/'sources.json').write_text(json.dumps({str(p.relative_to(HERE)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},indent=2)+'\n')
print('Four captured-image cases pass; session/sequence/time/window/focus/geometry/pixel/age/unstable-capture negatives pass. No input executed.')
