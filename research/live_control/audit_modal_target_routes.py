"""Audit route-specific failures, exact observations and independently saved effects."""
import hashlib,json
from pathlib import Path
from PIL import Image
from openpyxl import load_workbook
from session_v9 import Decoder
from modal_visual_predicate_v2 import ModalVisualPredicate
HERE=Path(__file__).resolve().parent
predicate=ModalVisualPredicate(Image.open(HERE/'results/modal-focus-01/tab-0.png').convert('RGB'),
                              **json.loads((HERE/'results/modal-predicate-01/config.json').read_text()))
expected={'key_normal':True,'key_focus':False,'key_move':True,'click_normal':True,
          'click_focus':True,'click_move':False,'key_occlusion':True,'click_occlusion':False}
report=[]
for cohort in ('modal-target-route-01','modal-target-occlusion-01'):
    root=HERE/'results'/cohort
    for name,h in json.loads((root/'sources.json').read_text()).items():
        assert hashlib.sha256((HERE/name).read_bytes()).hexdigest()==h,name
    for row in json.loads((root/'results.json').read_text()):
        case=row['case'];route,fault=case.split('_');d=root/case;guard=row['guard'];entry,=row['injections']
        assert guard['status']=='requires_new_admission'
        terminal=row['terminal'];assert terminal['status']==('needs_decision' if case=='click_move' else 'completed')
        assert terminal['release']['verified']
        assert guard['checked_ns']<entry['entered_ns']<=entry['sample_ns']<=entry['call_ns']<entry['returned_ns']
        same=entry['binding_before']==entry['binding_after'];assert same==(fault!='move')
        assert entry['binding_before']==guard['after']
        if case=='click_move':
            # Owner revision counts attempted mutation, including rejected move.
            assert guard['input_before']['pointer']==guard['input_after']['pointer']
            assert not guard['input_after']['owned_buttons'] and not guard['input_after']['owned_keycodes']
            assert not any(e.get('event')=='pointer_admission' for e in map(json.loads,(d/'events.jsonl').read_text().splitlines()))
        if fault=='occlusion':assert entry['overlay_event_types']==([4,5] if route=='click' else [])
        with Image.open(d/'confirm-guard.png') as im:assert predicate.inspect_at(im.convert('RGB'),[0,0])['status']=='visual_candidate'
        with Image.open(d/'pre-return.png') as im:pre=predicate.inspect_at(im.convert('RGB'),[0,0])
        assert (pre['status']=='visual_candidate')==(fault=='normal')
        wb=load_workbook(d/'sheet.xlsx');values=[wb.active['A1'].value,wb.active['A2'].value];wb.close()
        assert values==([532,590] if expected[case] else [None,None])
        assert row['independent_evaluation']['actual']==values and row['independent_evaluation']['success']==expected[case]
        decoder=Decoder('live-control');count=0
        for event in map(json.loads,(d/'events.jsonl').read_text().splitlines()):
            if event['event']!='observation':continue
            count+=1;frame=decoder.accept((d/f'{count:03d}.ait').read_bytes())
            with Image.open(d/Path(event['image']).name) as im:assert im.size==(frame.width,frame.height) and im.tobytes()==frame.pixels
        report.append(dict(cohort=cohort,case=case,terminal=terminal['status'],saved_values=values,
                           exact_public_frames=count,unchanged_x11_binding=same,pre_action_predicate=pre,
                           check_to_ordinary_execute_ms=(entry['call_ns']-guard['checked_ns'])/1e6,
                           evidence_sha256={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (d/'confirm-guard.png',d/'pre-return.png',d/'after.png',d/'sheet.xlsx')}))
assert {r['case'] for r in report}==set(expected)
(HERE/'results/modal-target-routes-audit.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps([dict(case=r['case'],terminal=r['terminal'],values=r['saved_values'],frames=r['exact_public_frames']) for r in report],indent=2))
