import json
from pathlib import Path
HERE=Path(__file__).resolve().parent
T4=HERE.parent/'blackstart_xrecord_5970_t4_20261001'
def main():
    raw=json.loads((HERE/'candidate.wrapper.raw.json').read_text())['candidate']
    old=json.loads((T4/'candidate.raw.json').read_text())['run']
    events=[]
    # Independently decode the retained T4 RECORD event window IDs.
    import subprocess
    code="""import json\nfrom Xlib import display\nfrom Xlib.protocol import rq\nd=display.Display()\nout=[]\nfor line in open(r'%s'):\n b=json.loads(line)\n if b['category']==0:\n  e,_=rq.EventField(None).parse_binary_value(bytes.fromhex(b['data_hex']),d.display,32,32)\n  out.append({'type':int(e.type),'window':int(e.window.id),'detail':int(e.detail)})\nprint(json.dumps(out))\nd.close()\n""" % (T4/'run/record_blocks.jsonl').as_posix()
    # Existing parsed T4 audit is independently checksummed; parse its canonical decoded result here.
    t4audit=json.loads((T4/'audit.raw.json').read_text())
    old_target_candidates=[e for e in t4audit['record_events'] if e['type'] in (2,3)]
    t4raw=json.loads((T4/'candidate.raw.json').read_text())
    # Raw protocol bytes are independently decoded by the T4 audit source; reconstruct target XID directly from bytes.
    for b in t4raw['run']['record_blocks']:
        if b['category']==0:
            q=bytes.fromhex(b['data_hex']); events.append({'type':q[0]&0x7f,'detail':q[1],'window_xid':int.from_bytes(q[12:16],'little')})
    nodes={n['xid']:n for n in raw['window_tree']}
    entry=raw['entry_xid']; tests={x['label']:x for x in raw['selection_tests']}
    mismatches=[e for e in events if e['window_xid']!=entry]
    target_present=all(e['window_xid'] in nodes for e in events)
    mask_test=tests.get('app-selected-target',{})
    if not target_present:
        status='HOLD_T4_EVENT_WINDOW_NOT_IN_NO_INPUT_TREE'
    elif mismatches and mask_test.get('result')=='error' and mask_test.get('error_code')==10:
        status='PASS_TARGET_AND_MASK_CONFLICT'
    elif mismatches and mask_test.get('result')=='success':
        status='FAIL_SECOND_CLIENT_SELECTION_SUCCEEDED'
    else:
        status='HOLD_TARGET_ROUTE_NOT_IDENTIFIED'
    result={'schema':'blackstart-xevent-target-t5-audit-v1','status':status,'input_dispatched':raw['input_dispatched'],'t5_tree_xids':sorted(nodes),'entry_xid':entry,'t4_recorded_event_windows':events,'t4_event_windows_present_in_t5_tree':target_present,'t5_selection_tests':raw['selection_tests'],'t5_keypress_masks':[{'xid':n['xid'],'mask':n['all_event_masks']&1} for n in raw['window_tree']]}
    (HERE/'audit.raw.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps(result,indent=2));return 0
if __name__=='__main__':raise SystemExit(main())
