"""Finite comparison: existing callback-capable form vs compiled graph."""
import copy, json, time
from runtime.guarded_x11_v1 import compiled, form

class Stop(Exception):
    def __init__(self,reason): self.reason=reason

def run(bridge,refs,token,route):
    started=time.monotonic_ns(); deadline=started+10_000_000_000
    initial_scope=bridge.scope; revision=bridge.binding_revision
    trace=[]; inputs=[]; observations=[]; original_save=bridge._save
    def instrument(name,row):
        known=time.monotonic_ns()
        if row.get('event')=='effect_checked': trace.append({'known_ns':known,**copy.deepcopy(row)})
        if name.startswith('result-') and 'execution' in row: inputs.append(copy.deepcopy(row))
        original_save(name,row)
    bridge._save=instrument
    def perceive(native,rgb):
        color=rgb.getpixel((50,160))
        return {'field_present':rgb.crop(refs['field']['box']).tobytes()==refs['field']['pixels'],
                'submit_present':rgb.crop(refs['save']['box']).tobytes()==refs['save']['pixels'],
                'field_accepted':color in ((40,180,60),(30,110,60)),'saved_cue':color==(30,110,60)}
    def verify(payload,native,rgb): return {'status':'succeeded','evidence_ref':payload['observation']['evidence_ref']}
    try:
        if route=='compiled':
            interface={'format':'compiled-gui-interface-v1','interface_id':'composition-comparison','session_scope':bridge.scope,'surface':compiled.surface(bridge),'predicates':['field_present','submit_present','field_accepted','saved_cue'],
              'symbols':{'field':{'kind':'target_reference','target_reference':'field','identity_predicate':'field_present','dependencies':['field_present']},'save':{'kind':'target_reference','target_reference':'save','identity_predicate':'submit_present','dependencies':['submit_present','field_accepted']}},
              'actions':{'enter':{'target_symbol':'field','operation':'enter_exact_token','expected_effect':{'field_accepted':True}},'save':{'target_symbol':'save','operation':'activate_save','expected_effect':{'saved_cue':True}}},
              'method':{'name':'enter-then-save','version':'1','initial_state':'empty','max_transitions':2,'max_runtime_ms':10000,'states':{
                'empty':{'branches':[{'when':{'field_present':True,'field_accepted':False,'saved_cue':False},'outcome':'action','action':'enter','next_state':'filled','reason':None}]},
                'filled':{'branches':[{'when':{'field_accepted':True,'submit_present':True},'outcome':'action','action':'save','next_state':'done','reason':None}]},
                'done':{'branches':[{'when':{'saved_cue':True},'outcome':'complete','action':None,'next_state':None,'reason':None}]}}}}
            bindings={'enter':{'interaction':'click','offset':refs['field']['offset'],'tail':[{'op':'key_chord','keys':['CTRL','A']},{'op':'text','text':token},{'op':'wait_update','timeout_ms':100}]},'save':{'interaction':'click','offset':refs['save']['offset'],'tail':[{'op':'wait_update','timeout_ms':100}]}}
            raw=compiled.run(bridge,interface,bindings,perceive=perceive,verify_effect=verify)
            observations=raw['observations']; outcome,reason,completed=raw['outcome'],raw['reason'],raw['completed_transitions']
        elif route=='form':
            completed=0
            def capture():
                if time.monotonic_ns()>=deadline: raise Stop('budget_exhausted')
                native=bridge.observe(); image=bridge.history[native['sequence']][1]
                predicates=perceive(native,image.copy())
                if bridge.scope!=initial_scope or bridge.binding_revision!=revision: raise Stop('association_changed')
                observations.append({'sequence':native['sequence'],'captured_ns':native['capture_ns'],'predicates':predicates,'evidence_ref':'observation-'+str(native['sequence']),'evidence_digest':native['native']['artifact']['sha256']})
                if time.monotonic_ns()>=deadline: raise Stop('budget_exhausted')
                return predicates
            class BudgetBridge:
                def click(self,*args,**kwargs):
                    native,rgb=bridge.history[bridge.sequence]
                    resolution=bridge.store.resolve_point(args[0],args[1],native,rgb,time.monotonic_ns(),session_scope=initial_scope)
                    if not resolution['eligible']: raise Stop('authority_unavailable')
                    expiry=min(deadline,resolution['valid_until_ns'])
                    return bridge.click(*args,**kwargs,expires_at_ns=expiry)
            def on_step(name,result):
                nonlocal completed
                releases=result.get('execution',{}).get('releases',[])
                neutral=bool(releases) and all(r.get('verified') is True and r.get('keys_down')==[] and r.get('buttons_down')==[] for r in releases)
                if not neutral: raise Stop('release_unverified')
                if result.get('status')!='completed' or result.get('recovery_required') is not False: raise Stop('execution_failed')
                completed+=1
                predicates=capture(); action='enter' if name=='entered' else 'save'
                expected='field_accepted' if name=='entered' else 'saved_cue'
                if predicates[expected] is not True: raise Stop('effect_failed')
                verdict=verify({'observation':observations[-1]},None,None)
                instrument('baseline-effect-'+str(completed)+'.json',{'event':'effect_checked','action':action,'status':verdict['status'],'evidence_ref':observations[-1]['evidence_ref']})
                if time.monotonic_ns()>=deadline: raise Stop('budget_exhausted')
                if name=='entered' and predicates['submit_present'] is not True: raise Stop('unknown_state')
            try:
                predicates=capture()
                if not predicates['field_present'] or predicates['field_accepted'] or predicates['saved_cue']: raise Stop('unknown_state')
                raw=form.fill_and_submit(BudgetBridge(),{'field':('field',refs['field']['offset']),'submit':('save',refs['save']['offset'])},token,wait_ms=100,on_step=on_step)
                outcome,reason='TASK_SUCCEEDED','method_complete'
            except Stop as stop:
                outcome='RUNTIME_FAILED' if stop.reason=='release_unverified' else 'SAFE_YIELD'; reason=stop.reason
                raw={'outcome':outcome,'reason':reason,'confirmed_completed_inputs':completed,'observations':observations,'replay_allowed':False}
        else: raise ValueError('unknown route')
        ended=time.monotonic_ns()
        original_save('method-raw.json',raw)
        original_save('method-timing.json',{'started_ns':started,'ended_ns':ended,'trace':trace,'scope':'local cue knowledge, not model feedback or semantic awareness'})
        neutral=all(bool(r['execution']['releases']) and all(v['verified'] and v['keys_down']==[] and v['buttons_down']==[] for v in r['execution']['releases']) for r in inputs)
        latest=bridge.history[bridge.sequence][0]
        result={'outcome':outcome,'reason':reason,'completed_inputs':completed,'local_observations':len(observations),'release_verified':neutral,'image_path':latest['native']['artifact']['path'],'image_sha256':latest['native']['artifact']['sha256'],'raw_receipt_ref':'method-raw.json','local_elapsed_ns':ended-started}
        original_save('method-common.json',result)
        return result
    finally:
        bridge._save=original_save
