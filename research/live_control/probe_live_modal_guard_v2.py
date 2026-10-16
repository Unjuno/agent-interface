"""Real guarded Return with normal Executor authority; known fixture negatives."""
import hashlib,json,shutil,subprocess,time
from dataclasses import replace
from pathlib import Path
from PIL import Image
from guarded_modal_backend_v2 import Backend,suite
from executor_v3 import Executor
from bound_modal_proposal import Context,propose
from modal_visual_predicate_v2 import ModalVisualPredicate
HERE=Path(__file__).resolve().parent;out=HERE/'results/live-modal-guard-02';out.mkdir(exist_ok=False)
config=json.loads((HERE/'results/modal-predicate-01/config.json').read_text());template=HERE/'results/modal-focus-01/tab-0.png'
predicate=ModalVisualPredicate(Image.open(template).convert('RGB'),**config);rows=[]
for case in ('normal','focus_change','move','age','session'):
    root=out/case;root.mkdir();s=suite.Session();backend=None;engine=None;events=[]
    try:
        goal,output,_=suite.prepare(s,'calc',991022,'unused');suite.base.CHAR_GAP_MS=0;driver=suite.base.Driver(s,settle_ms=0)
        driver.text('532');driver.key('Return');driver.text('590');driver.key('Return');driver.chord('Control_L','s');time.sleep(.5)
        backend=Backend(s,root,events.append);engine=Executor(backend,events.append);backend.snapshot('source',0)
        obs=events[-1];binding=obs['pointer_binding']
        context=Context(s.name,obs['sequence'],obs['capture_ns'],binding['surface'],binding['focus'],tuple(binding['geometry']))
        result,proposal=propose(predicate,backend.pixels(),context,context,[386,322,507,174],time.perf_counter_ns())
        assert proposal is not None,'no initial proposal'
        if case=='session':proposal=replace(proposal,context=replace(context,session='other-session'))
        backend.arm_modal('confirm',proposal)
        if case=='focus_change':driver.key('Tab');driver.key('Tab');time.sleep(.03)
        elif case=='move':subprocess.run(['wmctrl','-ir',hex(binding['surface']),'-e','0,440,250,-1,-1'],env=s.env,check=True);time.sleep(.03)
        elif case=='age':time.sleep(.3)
        engine.submit('confirm',[dict(op='key',key='Return')],backend.sequence,time.perf_counter_ns()+2_000_000_000)
        deadline=time.monotonic()+5
        while engine.active is not None and time.monotonic()<deadline:time.sleep(.01)
        assert engine.active is None
        terminal=next(r for r in events if r['event']=='terminal');guard=next(r for r in events if r['event']=='modal_guard')
        assert terminal['release']['verified']
        if case=='normal':assert terminal['status']=='completed'
        else:
            assert terminal['status']=='needs_decision'
            assert guard['input_before']['revision']==guard['input_after']['revision']
            assert not guard['input_after']['owned_buttons'] and not guard['input_after']['owned_keycodes']
        engine.close()
        score=suite.evaluate('calc',output,goal)
        assert score['success']==(case=='normal')
        shutil.copy2(output,root/'sheet.xlsx')
        rows.append(dict(case=case,guard=guard,terminal=terminal,independent_evaluation=score))
    finally:
        if engine:engine.close()
        if backend:backend.close();(root/'owner-events.json').write_text(json.dumps(backend.owner.records,indent=2)+'\n')
        (root/'events.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in events))
        if (s.tmp/'application.log').exists():shutil.copy2(s.tmp/'application.log',root/'application.txt')
        s.close();shutil.rmtree(s.tmp)
(out/'results.json').write_text(json.dumps(rows,indent=2)+'\n')
paths=[Path(__file__),HERE/'guarded_modal_backend_v2.py',HERE/'bound_modal_proposal.py',HERE/'modal_visual_predicate_v2.py',HERE/'modal_visual_predicate.py',HERE/'executor_v3.py',HERE/'session_v16.py',HERE/'input_owner_v9.py',template]
(out/'sources.json').write_text(json.dumps({str(p.relative_to(HERE)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},indent=2)+'\n')
print(json.dumps([dict(case=r['case'],guard=r['guard']['status'],terminal=r['terminal']['status'],success=r['independent_evaluation']['success']) for r in rows],indent=2))
