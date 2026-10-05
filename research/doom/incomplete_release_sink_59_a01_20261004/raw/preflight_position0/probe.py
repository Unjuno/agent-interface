import importlib.util, json, pathlib, sys, threading, types

source = pathlib.Path(sys.argv[1])
low = types.ModuleType('doom_typed_release_backend_v2')
class Previous: pass
low.Backend = Previous
low.suite = object()
owner = types.ModuleType('input_transition_owner_v4')
owner.InputOwner = object
sys.modules['doom_typed_release_backend_v2'] = low
sys.modules['input_transition_owner_v4'] = owner
spec = importlib.util.spec_from_file_location('tested_backend', source)
mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
results=[]
for accepted in (False, True):
    attempts=[]; delivered=[]
    def emit(row):
        attempts.append(dict(row))
        if row['release_batch_position'] == 0:
            if accepted: delivered.append(dict(row))
            raise OSError('sink boundary fault')
        delivered.append(dict(row))
    backend=mod.Backend.__new__(mod.Backend)
    backend._release_batch=threading.local(); backend.emit=emit
    context={'rows':[{'event':'input_release_transition','key':'a','release_batch_position':0}, {'event':'input_release_transition','key':'b','release_batch_position':1}], 'identifier':'p','step':4}
    err=RuntimeError('step failed')
    backend._finish_incomplete_release_batch(context,err,'step_exception')
    results.append({'sink_accept_before_raise':accepted,'attempt_positions':[r['release_batch_position'] for r in attempts], 'delivered_positions':[r['release_batch_position'] for r in delivered], 'original_error_type':type(err).__name__, 'original_error_text':str(err), 'publication_metadata':getattr(err,'release_batch_publication',None), 'context_rows_after':context['rows'], 'notes':getattr(err,'__notes__',[])})
print(json.dumps(results,sort_keys=True))
