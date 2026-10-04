import subprocess,time,json,pathlib,traceback,os
from Xlib import display
from runtime.backends.x11_v1.backend import X11Backend
from runtime.backends.x11_v1.session import X11RuntimeSession
import adaptive_acquisition_caller_v3 as caller
from converter import convert
root=pathlib.Path(__file__).resolve().parent
output={'rows':[],'model_calls':0,'source_authority':'fixture-only','errors':[],'uid':os.getuid()}
for index,name in enumerate(['completed','preinput_refusal','partial_wait_fault','release_omission']):
    row={'case':name,'calls':[],'events':[]};server=None;observer=None;backend=None
    try:
        address=f':{274+index}'
        server=subprocess.Popen(['Xvfb',address,'-screen','0','800x600x24','-nolisten','tcp'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        for _ in range(50):
            if server.poll() is not None:raise RuntimeError('Xvfb early exit')
            try:observer=display.Display(address);break
            except Exception:time.sleep(.02)
        if observer is None:raise RuntimeError('private display unavailable')
        class FixtureBackend(X11Backend):
            def key_state(self,key,down):
                super().key_state(key,down)
                row.setdefault('input_snapshots',[]).append({'key':key,'down':down,'keymap':list(observer.query_keymap())})
            def _wait_update(self,timeout_ms):
                if name=='partial_wait_fault':raise OSError('prospective injected wait fault')
                return super()._wait_update(timeout_ms)
            def release_all(self):
                if name=='release_omission' and not getattr(self,'omission_used',False):
                    self.omission_used=True
                    return {'keys_down':list(self.held_keycodes),'buttons_down':list(self.held_buttons),'verified':False,'monotonic_ns':time.monotonic_ns(),'fixture_fault':'first owned key release omitted'}
                return super().release_all()
        backend=FixtureBackend(address,{})
        session=X11RuntimeSession(backend)
        program=dict(schema='agent-interface/program-v1',program_id=name,source=dict(observation_seq=1,binding_revision=1),authority=dict(lease_id='private-converter-fixture',expires_at_ns=time.monotonic_ns()+5_000_000_000),terminal=dict(release_all_required=True),ops=[dict(op='key_state',key='Shift_L',down=True),dict(op='wait_update',timeout_ms=1),dict(op='release_all')])
        if name=='preinput_refusal':program['authority']['expires_at_ns']=1
        row['program']=program
        def execute(_):
            row['calls'].append('execute')
            receipt=session.dispatch(program,current_observation_seq=1,current_binding_revision=1)
            row['native_receipt']=receipt;row['keymap_after_dispatch']=list(observer.query_keymap())
            row['conversion']=convert(program,receipt)
            return row['conversion']['decision']
        def verify(_):row['calls'].append('verify');return {'status':'unavailable'}
        row['caller_result']=caller.run(json.loads((root/'caller_spec.json').read_text()),dict(reuse_revalidate=lambda _:{'status':'revalidated'},final_revalidate=lambda _:{'status':'revalidated'},execute=execute,verify_effect=verify,journal=row['events'].append))
        if name=='release_omission':
            row['sticky_followup']=session.dispatch(program,current_observation_seq=1,current_binding_revision=1)
            row['recovery']=session.recover_input()
        row['keymap_after_recovery']=list(observer.query_keymap())
        expected={'completed':'completed','preinput_refusal':'refused','partial_wait_fault':'execution_failed','release_omission':'release_unverified'}[name]
        if row['native_receipt']['status']!=expected:raise RuntimeError('native status gate')
        if any(row['keymap_after_recovery']):raise RuntimeError('neutral recovery keymap gate')
        if row['calls']!=(['execute','verify'] if name=='completed' else ['execute']):raise RuntimeError('caller callback gate')
        row['gate']='PASS_SCOPED_NATIVE_CONVERSION'
    except Exception:
        row['error']=traceback.format_exc();output['errors'].append(name)
    finally:
        try:
            if backend is not None:row['cleanup_release']=X11Backend.release_all(backend);row['cleanup_keymap']=list(observer.query_keymap());backend.close()
            if observer is not None:observer.close()
            if server is not None:server.terminate();row['xvfb_exit']=server.wait(timeout=2)
        except Exception:
            row['cleanup_error']=traceback.format_exc();output['errors'].append(name+' cleanup')
            if server is not None and server.poll() is None:server.kill();row['xvfb_exit']=server.wait();row['forced_kill']=True
        output['rows'].append(row)
    if output['errors']:break
output['censored_cases']=4-len(output['rows'])
print(json.dumps(output,indent=2));raise SystemExit(bool(output['errors']))
