"""Test-only interposition after frozen v2 guard, before ordinary Return input."""
import hashlib,json,shutil,time,zipfile
from pathlib import Path
from PIL import Image,ImageGrab
import guarded_modal_backend_v2 as guarded
from executor_v3 import Executor
from bound_modal_proposal import Context,propose
from modal_visual_predicate_v2 import ModalVisualPredicate

HERE=Path(__file__).resolve().parent
out=HERE/'results/modal-check-input-race-01';out.mkdir(exist_ok=False)
plan=dict(cases=['normal','post_check_focus_change'],injection='two Tab keys at entry to Previous.execute after guard passes',
          classification='DEVELOPMENT_KNOWN',claim='falsify atomic target binding, not estimate natural race frequency')
(out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
template=HERE/'results/modal-focus-01/tab-0.png'
config=json.loads((HERE/'results/modal-predicate-01/config.json').read_text())
predicate=ModalVisualPredicate(Image.open(template).convert('RGB'),**config)
original=guarded.Previous.execute;rows=[]
for case in plan['cases']:
    root=out/case;root.mkdir();s=guarded.suite.Session();backend=None;engine=None;events=[];injections=[]
    try:
        goal,output,_=guarded.suite.prepare(s,'calc',991022,'unused')
        guarded.suite.base.CHAR_GAP_MS=0;driver=guarded.suite.base.Driver(s,settle_ms=0)
        driver.text('532');driver.key('Return');driver.text('590');driver.key('Return');driver.chord('Control_L','s');time.sleep(.5)
        backend=guarded.Backend(s,root,events.append);engine=Executor(backend,events.append);backend.snapshot('source',0)
        obs=events[-1];binding=obs['pointer_binding']
        context=Context(s.name,obs['sequence'],obs['capture_ns'],binding['surface'],binding['focus'],tuple(binding['geometry']))
        status,proposal=propose(predicate,backend.pixels(),context,context,[386,322,507,174],time.perf_counter_ns())
        assert proposal is not None,status
        def interposed(self,step,cancel,identifier,index):
            if self is backend and identifier=='confirm' and index==0:
                entry=dict(entered_ns=time.perf_counter_ns(),binding_before=self.binding(),injected=case!='normal')
                if case!='normal':
                    driver.key('Tab');driver.key('Tab');time.sleep(.03)
                entry['binding_after']=self.binding()
                sample=ImageGrab.grab(xdisplay=s.name).convert('RGB')
                entry['sample_ns']=time.perf_counter_ns()
                entry['call_ns']=time.perf_counter_ns()
                try:return original(self,step,cancel,identifier,index)
                finally:
                    entry['returned_ns']=time.perf_counter_ns();injections.append(entry)
                    sample.save(root/'pre-return.png')
            return original(self,step,cancel,identifier,index)
        guarded.Previous.execute=interposed
        backend.arm_modal('confirm',proposal)
        engine.submit('confirm',[dict(op='key',key='Return')],backend.sequence,time.perf_counter_ns()+2_000_000_000)
        deadline=time.monotonic()+5
        while engine.active is not None and time.monotonic()<deadline:time.sleep(.01)
        assert engine.active is None
        engine.close();time.sleep(.5)
        ImageGrab.grab(xdisplay=s.name).convert('RGB').save(root/'after.png')
        terminal=next(r for r in events if r['event']=='terminal');guard=next(r for r in events if r['event']=='modal_guard')
        assert terminal['release']['verified']
        shutil.copy2(output,root/'sheet.xlsx')
        try:score=guarded.suite.evaluate('calc',output,goal)
        except Exception as exc:score=dict(success=None,error=type(exc).__name__,message=str(exc))
        with zipfile.ZipFile(root/'sheet.xlsx') as z:
            format_evidence=dict(has_xlsx_workbook='xl/workbook.xml' in z.namelist(),
                                 mimetype=z.read('mimetype').decode() if 'mimetype' in z.namelist() else None)
        rows.append(dict(case=case,guard=guard,terminal=terminal,injections=injections,independent_evaluation=score,format_evidence=format_evidence))
        (out/'results.json').write_text(json.dumps(rows,indent=2)+'\n')
    finally:
        guarded.Previous.execute=original
        if engine:engine.close()
        if backend:backend.close();(root/'owner-events.json').write_text(json.dumps(backend.owner.records,indent=2)+'\n')
        (root/'events.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in events))
        if (s.tmp/'application.log').exists():shutil.copy2(s.tmp/'application.log',root/'application.txt')
        s.close();shutil.rmtree(s.tmp)
paths=[Path(__file__),HERE/'guarded_modal_backend_v2.py',HERE/'bound_modal_proposal.py',HERE/'modal_visual_predicate_v2.py',HERE/'modal_visual_predicate.py',HERE/'session_v16.py',HERE/'executor_v3.py',template]
(out/'sources.json').write_text(json.dumps({str(p.relative_to(HERE)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},indent=2)+'\n')
print(json.dumps([dict(case=r['case'],guard=r['guard']['status'],terminal=r['terminal']['status'],score=r['independent_evaluation'],format=r['format_evidence']) for r in rows],indent=2))
