#!/usr/bin/env python3
"""Construction-only mutation check for audit.py; never invokes X input."""
import importlib.util, json
from pathlib import Path
p=Path(__file__).with_name('audit.py'); spec=importlib.util.spec_from_file_location('audit',p); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
def ev(kind): return {'type':kind,'window_id':9,'keycode':25,'serial':1,'time':1}
def route(name, held_at_a_up):
    fourth=ev('KeyRelease')
    return {'route':name,'steps':[
      {'actor':'A','edge':'DOWN','keymap_down':True,'core_events':[ev('KeyPress')]},
      {'actor':'B','edge':'DOWN','keymap_down':True,'core_events':[ev('KeyPress')]},
      {'actor':'A','edge':'UP','keymap_down':held_at_a_up,'core_events':[] if held_at_a_up else [ev('KeyRelease')]},
      {'actor':'B','edge':'UP','keymap_down':False,'core_events':[fourth]}], 'x_errors':[]}
def raw(device_held):
    calls=[{'route':r,'actor':a,'edge':e,'return_code':1} for r in ('core','device') for a,e in (('A','DOWN'),('B','DOWN'),('A','UP'),('B','UP'))]
    return {'schema':'x11-xtest-device-cross-client-raw-a01-v1','status':'CANDIDATE_COMPLETE','candidate_exit':0,'display':':87',
      'devices_found':[[5,'Virtual core XTEST keyboard']],'device_name':'Virtual core XTEST keyboard','device_id':5,
      'client_connections':{'receiver':True,'observer':True,'A':True,'B':True,'A_and_B_distinct':True},'initial_keymap_down':False,
      'device_handles_open':{'A':True,'B':True,'same_server_device_id':5},'cleanup':{'displays_closed':4},'x_errors':[],
      'api_calls':calls,'keycode':25,'window_id':9,'routes':[route('core',False),route('device',device_held)]}
def check(name, data, expected, expected_exit):
    result=m.audit(json.dumps(data).encode())
    if result['verdict']!=expected or result['audit_exit']!=expected_exit:
        raise RuntimeError(name+' expected '+expected+' got '+json.dumps(result,sort_keys=True))
    return {'case':name,'verdict':result['verdict'],'audit_exit':result['audit_exit'],'checks_passed':sum(c['ok'] for c in result['checks']),'checks_total':len(result['checks'])}
results=[check('ordinary-shared-device',raw(False),'DEVICE_PATH_DOES_NOT_ISOLATE',0),
         check('counterfactual-isolated-device',raw(True),'DEVICE_PATH_ISOLATES',0)]
bad=raw(False); bad['routes'][0]['steps'][2]['core_events']=[]
results.append(check('corrupt-control',bad,'INDETERMINATE_STOP',1))
out=Path(__file__).with_name('precheck'); out.mkdir(exist_ok=True)
(out/'audit_mutation_precheck.json').write_text(json.dumps({'schema':'audit-mutation-precheck-v1','input_events':0,'results':results},indent=2,sort_keys=True)+'\n',encoding='utf-8')
print(json.dumps(results,sort_keys=True))
