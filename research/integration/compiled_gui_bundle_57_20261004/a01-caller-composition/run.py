import copy, hashlib, json, sys
from pathlib import Path
from research.live_control.adaptive_acquisition_caller_v3 import run as run_caller
from runtime.core_v1.compiled_gui import run as run_compiled


def interface():
    return {
      'format':'compiled-gui-interface-v1','interface_id':'composition-smoke',
      'session_scope':'private-test-double','surface':'form',
      'predicates':['stage','field_changed','submit_target'],
      'symbols':{'field':{'kind':'target_reference','target_reference':'field-ref',
                          'identity_predicate':'submit_target','dependencies':['stage','submit_target']}},
      'actions':{
        'enter':{'target_symbol':'field','operation':'enter','expected_effect':{'field_changed':True}},
        'submit':{'target_symbol':'field','operation':'submit','expected_effect':{'stage':2}}},
      'method':{'name':'enter-then-submit','version':'1','initial_state':'editing',
        'max_transitions':2,'max_runtime_ms':10000,'states':{
          'editing':{'branches':[{'when':{'stage':0,'submit_target':True},'outcome':'action','action':'enter','next_state':'filled','reason':None}]},
          'filled':{'branches':[{'when':{'stage':1,'field_changed':True,'submit_target':True},'outcome':'action','action':'submit','next_state':'done','reason':None}]},
          'done':{'branches':[{'when':{'stage':2},'outcome':'complete','action':None,'next_state':None,'reason':None}]}}}}


def run_case(case, outer_effect='succeeded'):
    observation_count = [0]
    effects = iter(['succeeded','succeeded'])
    execution = []
    def observe(payload):
        observation_count[0] += 1
        n=observation_count[0]
        predicates = ({'stage':0,'field_changed':False,'submit_target':True} if n == 1 else
                      {'stage':1,'field_changed':True,'submit_target':case != 'changed'} if n == 2 else
                      {'stage':2,'field_changed':True,'submit_target':True})
        return {'sequence':n,'captured_ns':__import__('time').perf_counter_ns(),'surface':'form',
                'predicates':predicates,'evidence_ref':f'frame-{n}','evidence_digest':f'd{n}'}
    def execute(payload):
        record = run_compiled(interface(), {
          'observe':observe,
          'admit':lambda p:{'eligible':True,'status':'revalidated','authorization':'one-use','expected_sequence':p['observation']['sequence'],'valid_until_ns':__import__('time').perf_counter_ns()+1000000000},
          'execute':lambda p:{'status':'completed','action_id':'action-'+str(len(execution)+1),'effect_ref':'effect-'+str(len(execution)+1),'release':{'verified':True,'keys_down':[],'buttons_down':[]}},
          'verify_effect':lambda p:{'status':next(effects),'evidence_ref':p['observation']['evidence_ref']},
          'cancelled':lambda:False,'journal':lambda p:None})
        execution.append(copy.deepcopy(record))
        if record['outcome']=='TASK_SUCCEEDED': return {'status':'completed'}
        if record['outcome']=='SAFE_YIELD': return {'status':'safe_yield','reason':record['reason'],'completed_actions':record['completed_transitions']}
        return {'status':'failed'}
    events=[]
    spec={'target':'two-step form task','route':'reuse','coarse_origin':'caller_provided','provided_coarse':None,
          'cached_target':{'interface':interface(),'case':case},'local_repair_on':[],'repair_on':[],'session_id':'composition-a01-'+case}
    result=run_caller(spec, {
      'reuse_revalidate':lambda p:{'status':'revalidated'},
      'final_revalidate':lambda p:{'status':'revalidated'},
      'execute':execute,
      'verify_effect':lambda p:{'status':outer_effect},
      'journal':events.append})
    return {'result':result,'compiled':execution,'journal_events':events}


def main():
    out={'schema':'compiled-caller-composition-a01-v1','source_sha256':{},'cases':{}}
    for name,path in [('caller','research/live_control/adaptive_acquisition_caller_v3.py'),('compiled','runtime/core_v1/compiled_gui.py')]:
        out['source_sha256'][name]=hashlib.sha256(Path(path).read_bytes()).hexdigest()
    out['cases']['warm_positive']=run_case('positive')
    out['cases']['warm_changed']=run_case('changed')
    out['cases']['outer_effect_unavailable']=run_case('positive','unavailable')
    Path(sys.argv[1]).write_text(json.dumps(out,sort_keys=True,indent=2)+'\n')

if __name__=='__main__': main()
