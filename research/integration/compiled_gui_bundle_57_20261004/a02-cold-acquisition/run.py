"""A02 cold caller-to-compiled-runtime integration test double."""
import copy, hashlib, json, sys, time
from pathlib import Path
from adaptive_acquisition_caller_v3 import ModelFailure, run as run_caller
from runtime.core_v1.compiled_gui import run as run_compiled


def interface():
    return {
      'format':'compiled-gui-interface-v1','interface_id':'composition-a02',
      'session_scope':'private-test-double','surface':'form',
      'predicates':['stage','field_changed','submit_target'],
      'symbols':{'field':{'kind':'target_reference','target_reference':'field-ref','identity_predicate':'submit_target','dependencies':['stage','submit_target']}},
      'actions':{'enter':{'target_symbol':'field','operation':'enter','expected_effect':{'field_changed':True}},'submit':{'target_symbol':'field','operation':'submit','expected_effect':{'stage':2}}},
      'method':{'name':'enter-then-submit','version':'1','initial_state':'editing','max_transitions':2,'max_runtime_ms':10000,'states':{
        'editing':{'branches':[{'when':{'stage':0,'submit_target':True},'outcome':'action','action':'enter','next_state':'filled','reason':None}]},
        'filled':{'branches':[{'when':{'stage':1,'field_changed':True,'submit_target':True},'outcome':'action','action':'submit','next_state':'done','reason':None}]},
        'done':{'branches':[{'when':{'stage':2},'outcome':'complete','action':None,'next_state':None,'reason':None}]}}}}

USAGE={'input_tokens':100,'cached_input_tokens':25,'cache_write_input_tokens':0,'output_tokens':10,'reasoning_output_tokens':3}

def model_result(output, call_id):
    return {'call_id':call_id,'output':output,'usage':copy.deepcopy(USAGE),
      'requested_model':'test-double-model','requested_effort':'none','cost':None,
      'visible_images_submitted':1,'wait_ns':10_000_000}

def run_case(case):
    target={'interface':interface()}; obs_count=[0]; compiled=[]; events=[]; model_calls=[]; effects=[]
    def observe(payload):
        obs_count[0]+=1; n=obs_count[0]
        predicates=({'stage':0,'field_changed':False,'submit_target':True} if n==1 else
                    {'stage':1,'field_changed':True,'submit_target':True} if n==2 else
                    {'stage':2,'field_changed':True,'submit_target':True})
        return {'sequence':n,'captured_ns':time.perf_counter_ns(),'surface':'form','predicates':predicates,
                'evidence_ref':f'frame-{n}','evidence_digest':f'd{n}'}
    def execute(payload):
        receipt=run_compiled(interface(), {
          'observe':observe,
          'admit':lambda p:{'eligible':True,'status':'revalidated','authorization':'one-use','expected_sequence':p['observation']['sequence'],'valid_until_ns':time.perf_counter_ns()+1_000_000_000},
          'execute':lambda p:{'status':'completed','action_id':f'action-{len(compiled)+1}','effect_ref':f'effect-{len(compiled)+1}','release':{'verified':True,'keys_down':[],'buttons_down':[]}},
          'verify_effect':lambda p:{'status':'succeeded','evidence_ref':p['observation']['evidence_ref']},
          'cancelled':lambda:False,'journal':lambda row:None})
        compiled.append(copy.deepcopy(receipt))
        if receipt['outcome']=='TASK_SUCCEEDED': return {'status':'completed'}
        if receipt['outcome']=='SAFE_YIELD': return {'status':'safe_yield','reason':receipt['reason'],'completed_actions':receipt['completed_transitions']}
        return {'status':'failed'}
    def model(stage):
        if case=='no_match' and stage=='coarse_model':
            result=model_result({'status':'no_match','target':None},'a02-no-match')
        elif case=='model_failure' and stage=='coarse_model':
            raise ModelFailure('synthetic upstream failure',call_id='a02-failed',usage=None,visible_images_submitted=1,wait_ns=12_000_000)
        elif stage=='coarse_model': result=model_result({'status':'candidate','point':[5,6]},'a02-coarse')
        else: result=model_result({'status':'target_reference','target':target},'a02-anchor')
        model_calls.append({'stage':stage,'result':copy.deepcopy(result)})
        return result
    adapters={'observe_source':lambda p:{'image_ref':'source-frame'},'coarse_model':lambda p:model('coarse_model'),
      'acquire_anchor':lambda p:{'image_ref':'anchor-frame'},'anchor_model':lambda p:model('anchor_model'),
      'final_revalidate':lambda p:{'status':'revalidated'},'execute':execute,
      'verify_effect':lambda p:(effects.append(copy.deepcopy(p)) or {'status':'succeeded'}),
      'journal':events.append}
    spec={'target':'two-step form task','route':'cold','coarse_origin':'model_produced','provided_coarse':None,
      'cached_target':None,'local_repair_on':[],'repair_on':[],'session_id':'composition-a02-'+case}
    result=run_caller(spec,adapters,clock=time.perf_counter_ns,id_factory=iter([f'a02-{case}-1',f'a02-{case}-2']).__next__)
    return {'result':result,'compiled':compiled,'model_adapter_returns':model_calls,'outer_effect_calls':effects,'journal_events':events}

def main():
    out={'schema':'compiled-caller-composition-a02-v1','source_sha256':{},'cases':{}}
    for name,path in [('caller','research/live_control/adaptive_acquisition_caller_v3.py'),('compiled','runtime/core_v1/compiled_gui.py')]:
        out['source_sha256'][name]=hashlib.sha256(Path(path).read_bytes()).hexdigest()
    for case in ('positive','no_match','model_failure'): out['cases'][case]=run_case(case)
    Path(sys.argv[1]).write_text(json.dumps(out,sort_keys=True,indent=2)+'\n')
if __name__=='__main__': main()
