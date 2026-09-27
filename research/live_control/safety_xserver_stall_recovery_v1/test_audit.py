import copy, json, sys
from pathlib import Path
import audit

def load(p): return json.loads(Path(p).read_text())

def expect_reject(base, mutate):
    x=copy.deepcopy(base); mutate(x); assert audit.validate(x), x

def main():
    base=load(sys.argv[1]); cand=load(sys.argv[2])
    assert not audit.validate(base), audit.validate(base)
    assert not audit.validate(cand), audit.validate(cand)
    controls=[
      (cand,lambda x:x.__setitem__('pre_resume_receipt',True)),
      (cand,lambda x:x['watchdog_receipt'].__setitem__('verified_ns',x['server_cont_ns']-1)),
      (cand,lambda x:x['watchdog_receipt'].__setitem__('authority','task')),
      (cand,lambda x:x.__setitem__('down_at_measure',True)),
      (cand,lambda x:x['events_final'].append(copy.deepcopy(x['events_final'][-1]))),
      (cand,lambda x:x['events_final'].append({'event':'KeyPress','keysym':'F8','keycode':74,'ts_ns':x['measure_ns']})),
      (base,lambda x:x.__setitem__('down_at_measure',False)),
      (base,lambda x:x.__setitem__('post_measure_cleanup_ns',None)),
      (base,lambda x:x.__setitem__('final_down',True)),
      (base,lambda x:x.__setitem__('server_proc_state_after_stop','S')),
    ]
    for b,m in controls: expect_reject(b,m)
    print(json.dumps({'controls_rejected':len(controls),'status':'PASS'},sort_keys=True))
if __name__=='__main__': main()
