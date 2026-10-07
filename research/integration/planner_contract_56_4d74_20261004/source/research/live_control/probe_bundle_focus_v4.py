"""Corrected key-admission trigger for real X11 focus fault in the registered nine-step bundle; no reruns."""
import contextlib
import json
import shutil
import threading
import time
from pathlib import Path
from Xlib import X,display
from cause_servo_session_v1 import Backend,suite
from executor_v8 import Executor
from report_pages_v2 import digest

HERE=Path(__file__).resolve().parent
root=HERE/'results/bundle-focus-04';root.mkdir(exist_ok=False)
source=HERE/'results/bundle-pair-01/B/bundle/steps.json'
steps=json.loads(source.read_text())
assert len(steps)==9
names=['probe_bundle_focus_v4.py','cause_servo_session_v1.py','cause_session_v1.py','executor_v8.py',
       'post_release_observation_v2.py','lease_cause_v1.py','lease_cause_v2.py','input_owner_v10.py','session_v21.py','session_v15.py','session_v13.py','session_v9.py']
plan=dict(seed=224,cases=[['select_all_modifier',3,'key']],
          bundle_source_sha256=digest(source.read_bytes()),sources={n:digest((HERE/n).read_bytes()) for n in names},
          protocol='Keyboard events lack step/id; use enclosing single-worker step_started context. Block emitter after chosen physical admission; transfer focus using separate X connection, verify release before unblocking, keep unrelated focus through passive capture and fresh observe; verify no tail and cause isolation.',
          scope='Scripted private X11 backend probe, not socket delivery, model speed, full transaction rollback or general error coverage.')
(root/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
rows=[]
for name,target,kind in plan['cases']:
    out=root/name;out.mkdir()
    blocked,resume,done=threading.Event(),threading.Event(),threading.Event()
    events=[];current={'id':None,'step':None};result=dict(case=name,target_step=target,kind=kind,success=False)
    session=backend=engine=controller=original=sink=output=None
    try:
        def emit(event):
            event['probe_emitted_ns']=time.perf_counter_ns();events.append(event)
            if event['event']=='step_started':current.update(id=event['id'],step=event['step'])
            chosen=(current['step']==target and current['id']=='bundle' and
                    ((kind=='button' and event['event']=='pointer_admission' and event.get('operation')=='button_down') or
                     (kind=='key' and event['event']=='input_admission' and event.get('key')=='Control_L')))
            if chosen and not blocked.is_set():
                blocked.set()
                assert resume.wait(2),'probe output not resumed'
            if event['event']=='terminal':done.set()
        with (out/'setup.txt').open('w') as log,contextlib.redirect_stdout(log):
            session=suite.Session();_,output,_=suite.prepare(session,'inkscape',224,'')
            backend=Backend(session,out,emit);controller=display.Display(session.name)
        backend.snapshot('initial',0);engine=Executor(backend,emit)
        deadline=time.perf_counter_ns()+30_000_000_000
        engine.submit('bundle',steps,backend.sequence,deadline)
        assert blocked.wait(4),'target admission not reached'
        code=controller.keysym_to_keycode(suite.base.XK.string_to_keysym('Control_L'))
        def down():
            if kind=='button':return bool(controller.screen().root.query_pointer().mask & X.Button1Mask)
            bitmap=controller.query_keymap();return bool(bitmap[code//8] & (1<<(code%8)))
        assert down(),'physical input not down at blocked admission'
        result['physical_down_verified']=True
        original=controller.get_input_focus().focus
        sink=controller.screen().root.create_window(0,0,100,80,0,controller.screen().root_depth,override_redirect=True)
        sink.map();sink.set_input_focus(X.RevertToParent,X.CurrentTime);controller.sync()
        result['focus_transfer_ns']=time.perf_counter_ns()
        stop=time.monotonic()+1
        while down() and time.monotonic()<stop:time.sleep(.002)
        result['physical_release_while_output_blocked']=not down() and not done.is_set() and not resume.is_set()
        assert result['physical_release_while_output_blocked']
        resume.set()  # Keep unrelated focus throughout passive capture and fresh observe.
        assert done.wait(3),'terminal not reached'
        terminal=next(e for e in events if e['event']=='terminal')
        cause=terminal['interruption']['record']
        assert terminal['status']=='needs_decision' and terminal['decision_reason']=='focus_changed'
        assert terminal['steps_completed']==target and cause['reason']=='focus_changed'
        assert terminal['release']['verified'] and not down()
        admitted=[e for e in events if e['event'] in ('pointer_admission','input_admission')]
        assert all(e.get('step',target)<=target and e['admitted_ns']<=cause['verified_ns'] for e in admitted)
        assert not any(e['event']=='step_started' and e['step']>target for e in events)
        result['release_to_terminal_ms']=(terminal['terminal_ns']-cause['verified_ns'])/1e6
        result['terminal']=terminal;result['no_tail_admission']=True
        with engine.lock:assert engine.active is None
        done.clear()
        engine.submit('fresh-observation',[dict(op='observe')],backend.sequence,deadline)
        assert done.wait(3)
        fresh=[e for e in events if e['event']=='terminal'][-1]
        assert fresh['status']=='completed' and fresh['interruption'] is None
        result['fresh_observation_same_deadline_no_cause']=True
        assert controller.get_input_focus().focus.id==sink.id
        post=terminal['post_release_observation'];assert post['captures']==2 and not post['stopped'] and post['error'] is None
        observed=[e for e in events if e['event']=='observation' and e['sequence'] in post['sequences']]
        assert len(observed)==2
        for e in observed:
            assert e['input_focus_before']==sink.id and e['input_focus_after']==sink.id
            for side in ('input_state_before','input_state_after'):
                state=e[side];assert not state['owned_buttons'] and not state['owned_keycodes']
                assert state['active_lease_deadline_ns'] is None
        result['foreign_focus_persisted_without_input']=True;result['success']=True
    except Exception as exc:
        result['error']=repr(exc)
    finally:
        resume.set();cleanup={}
        if original is not None:
            original.set_input_focus(X.RevertToParent,X.CurrentTime);controller.sync()
        if sink is not None:sink.destroy();controller.sync()
        for label,resource in [('engine',engine),('backend',backend),('controller',controller),('session',session)]:
            if resource is not None:
                try:resource.close();cleanup[label]='close returned'
                except Exception as exc:cleanup[label]=repr(exc);result['success']=False
        if output is not None and output.exists():shutil.copy2(output,out/'shape.svg')
        result.update(events=events,owner_records=backend.owner.records if backend else [],cleanup=cleanup)
        (out/'report.json').write_text(json.dumps(result,indent=2)+'\n')
    rows.append({k:v for k,v in result.items() if k not in ('events','owner_records','terminal')})
(root/'summary.json').write_text(json.dumps(rows,indent=2)+'\n')
print(json.dumps(rows))
if not all(r['success'] for r in rows):raise SystemExit(1)
