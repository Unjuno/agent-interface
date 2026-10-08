"""Replay retained race evidence without activating a GUI."""
import hashlib,json
from pathlib import Path
from PIL import Image
from openpyxl import load_workbook
from session_v9 import Decoder
from modal_visual_predicate_v2 import ModalVisualPredicate
HERE=Path(__file__).resolve().parent;root=HERE/'results/modal-check-input-race-01'
for name,h in json.loads((root/'sources.json').read_text()).items():
    assert hashlib.sha256((HERE/name).read_bytes()).hexdigest()==h,name
predicate=ModalVisualPredicate(Image.open(HERE/'results/modal-focus-01/tab-0.png').convert('RGB'),
                              **json.loads((HERE/'results/modal-predicate-01/config.json').read_text()))
report=[]
for row in json.loads((root/'results.json').read_text()):
    d=root/row['case'];negative=row['case']!='normal';guard=row['guard'];injection,=row['injections']
    assert guard['status']=='requires_new_admission' and row['terminal']['status']=='completed'
    assert row['terminal']['release']['verified']
    assert guard['checked_ns']<injection['entered_ns']<=injection['sample_ns']<=injection['call_ns']<injection['returned_ns']
    assert injection['binding_before']==injection['binding_after']==guard['after']
    assert injection['injected']==negative
    with Image.open(d/'confirm-guard.png') as im:guard_match=predicate.inspect_at(im.convert('RGB'),[0,0])
    with Image.open(d/'pre-return.png') as im:input_match=predicate.inspect_at(im.convert('RGB'),[0,0])
    assert guard_match['status']=='visual_candidate'
    assert (input_match['status']=='visual_candidate')== (not negative)
    wb=load_workbook(d/'sheet.xlsx');values=[wb.active['A1'].value,wb.active['A2'].value];wb.close()
    assert values==([None,None] if negative else [532,590])
    assert row['independent_evaluation']['actual']==values
    assert row['independent_evaluation']['success']==(not negative)
    decoder=Decoder('live-control');count=0
    for event in map(json.loads,(d/'events.jsonl').read_text().splitlines()):
        if event['event']!='observation':continue
        count+=1;frame=decoder.accept((d/f'{count:03d}.ait').read_bytes())
        with Image.open(d/Path(event['image']).name) as im:assert im.size==(frame.width,frame.height) and im.tobytes()==frame.pixels
    report.append(dict(case=row['case'],exact_public_frames=count,saved_values=values,
                       guard_predicate=guard_match,pre_return_predicate=input_match,
                       check_to_ordinary_execute_ms=(injection['call_ns']-guard['checked_ns'])/1e6,
                       unchanged_x11_binding=True,
                       evidence_sha256={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (d/'confirm-guard.png',d/'pre-return.png',d/'after.png',d/'sheet.xlsx')}))
(HERE/'results/modal-check-input-race-audit.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
