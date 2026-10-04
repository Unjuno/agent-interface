"""Bounded Calc edit-mode/pacing control, grounded once by primary assistant."""
import argparse
import json
from pathlib import Path
import shutil
import time
import traceback
from openpyxl import load_workbook

from run_native_six_task_self_use_v1 import PrivateSession, suite
from native_handle_bridge_v1 import NativeHandleBridge
from run_native_calc_self_use_v1 import paced_text_tail


def allocation():
    # Counterbalanced payload order across edit/pacing conditions; two blocks.
    cases = []
    for block in range(2):
        conditions = [(edit, gap) for edit in (False, True) for gap in (0, 2, 10)]
        if block:
            conditions.reverse()
        for edit, gap in conditions:
            for payload in (('116', '476') if block == 0 else ('476', '116')):
                cases.append(dict(cell=f'{chr(65+len(cases)//8)}{len(cases)%8+1}', block=block,
                                  edit=edit, gap_ms=gap, text=payload))
    return cases


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    session = bridge = output = None
    cases = allocation()
    def save(name, value):
        (out/name).write_text(json.dumps(value, indent=2)+'\n')
    def request(name, source):
        path = out/(name+'.json')
        save(name+'-source.json', source)
        print(json.dumps({'request_file': str(path), 'source_sequence': source['sequence'],
                          'image': source['native']['artifact']['path']}), flush=True)
        end = time.monotonic()+300
        while not path.exists():
            if time.monotonic() > end:
                raise TimeoutError(name)
            time.sleep(.05)
        row=json.loads(path.read_text())
        if row['source_sequence'] != source['sequence']:
            raise ValueError('grounding source mismatch')
        return row
    try:
        save('allocation.json', cases)
        session=PrivateSession()
        _, output, _=suite.prepare(session, 'calc', 991085, '')
        window=int(next(line.split()[0] for line in session.windows().splitlines()
                        if 'sheet.xlsx' in line),16)
        bridge=NativeHandleBridge(session.name, {'app':window}, 'app', out/'bridge')
        grounding=request('namebox', bridge.observe())
        records=[]
        for i, case in enumerate(cases):
            source=bridge.observe()
            alias=f'namebox_{i}'
            offset=bridge.mint(alias,source['sequence'],grounding['point'],region_size=(24,14))
            tail=[{'op':'wait_update','timeout_ms':100},
                  {'op':'key_chord','keys':['CTRL','A']},
                  {'op':'text','text':case['cell']},
                  {'op':'key_chord','keys':['ENTER']},
                  {'op':'wait_update','timeout_ms':100}]
            if case['edit']:
                tail.append({'op':'key_chord','keys':['F2']})
            tail.append({'op':'wait_update','timeout_ms':100})
            tail += paced_text_tail([{'op':'text','text':case['text']}], case['gap_ms'])
            tail += [{'op':'key_chord','keys':['ENTER']},{'op':'wait_update','timeout_ms':100}]
            result=bridge.click(alias,offset,tail=tail)
            records.append(dict(case=case,result=result))
            save('cases.json',records)
            if result['status']!='completed':
                raise RuntimeError('case did not complete; no replay')
        source=bridge.observe()
        # Explicit primary review of the complete matrix before saving.
        action=request('save',source)
        offset=bridge.mint('save',source['sequence'],action['point'],region_size=(24,14))
        result=bridge.click('save',offset,tail=action.get('tail',[]))
        save('save-result.json',result)
        if result['status']!='completed':
            raise RuntimeError('save action failed')
        save('save-feedback.json',bridge.feedback('sheet.xlsx — LibreOffice Calc'))
        focused=bridge.backend.d.get_input_focus().focus.id
        bridge.close()
        bridge=NativeHandleBridge(session.name, {'app':focused}, 'app', out/'confirmation-bridge')
        action=request('confirm',bridge.observe())
        offset=bridge.mint('confirm',1,action['point'],region_size=(24,14))
        result=bridge.click('confirm',offset,tail=action.get('tail',[]))
        save('confirm-result.json',result)
        if result['status']!='completed':
            raise RuntimeError('confirmation failed')
        # Read saved output only after all action decisions are finished.
        time.sleep(.3)
        wb=load_workbook(output,read_only=True,data_only=False)
        scores=[dict(case,actual=wb.active[case['cell']].value,
                     exact=wb.active[case['cell']].value==int(case['text'])) for case in cases]
        wb.close()
        save('scores.json',scores)
        print(json.dumps({'exact':sum(r['exact'] for r in scores),'total':len(scores),
                          'failures':[r for r in scores if not r['exact']]}),flush=True)
    except Exception:
        (out/'error.txt').write_text(traceback.format_exc())
        raise
    finally:
        if output is not None and output.exists():
            shutil.copyfile(output,out/'sheet.xlsx')
        if bridge is not None:
            bridge.close()
        if session is not None:
            session.close()
            save('cleanup.json',[{'pid':p.pid,'returncode':p.poll()} for p in session.procs])


if __name__=='__main__':
    main()
