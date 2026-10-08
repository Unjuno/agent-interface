import json,subprocess,sys,traceback
from pathlib import Path
import map01_overlap_controller_v39 as controller

out=Path('/out')
class Client:
    def __init__(self,*args,**kwargs): pass
    def initialize(self): pass
    def close(self, timeout=1):
        with (out/'planner-close.jsonl').open('a') as stream: stream.write('{"event":"fake_planner_close"}\n')
class Planner:
    thread_id='construction-thread'
    def __init__(self,*args,**kwargs): pass
    def start_session(self): pass
controller.CodexAppServerClient=Client
controller.PersistentPlannerAdapter=Planner
controller.DoomStatusNumberReader=lambda *args,**kwargs: object()
controller.app_server_command=lambda: []
controller.win=str
controller.session_command=lambda args,runtime: [sys.executable,'/study/probe_controller_child_01.py']
original_popen=subprocess.Popen
children=[]
def owned_popen(*args,**kwargs):
    child=original_popen(*args,**kwargs);children.append(child);return child
controller.subprocess.Popen=owned_popen
sys.argv=['controller','--out','/out/controller','--model','construction-no-model',
          '--effort','low','--load-fixture-manifest','/unused','--iterations','1']
error=None
try:
    controller.main()
except BaseException as caught:
    error=caught
    (out/'controller-exception.txt').write_text(traceback.format_exc())
finally:
    subprocess.Popen=original_popen
assert len(children)==1
child=children[0]
pre={'controller_error_type':type(error).__name__, 'controller_error':str(error),
     'child_poll':child.poll(), 'child_commands_present':(out/'child-commands.jsonl').exists(),
     'fake_planner_close_present':(out/'planner-close.jsonl').exists(),
     'scope':'literal main, fake planner/readers, real command-waiting Python child; no game/model/input'}
(out/'BEFORE_EXTERNAL_CLEANUP.json').write_text(json.dumps(pre,indent=2))
cleanup={'actor':'probe checks controller cleanup; no external finish', 'child_exit':child.poll(), 'finish_sent':False}
if child.poll() is None:
    child.kill();child.wait(timeout=3)
    cleanup['emergency_probe_kill']=True
(out/'EXTERNAL_CLEANUP.json').write_text(json.dumps(cleanup,indent=2))
print(json.dumps({'before':pre,'external_cleanup':cleanup}))
assert pre['controller_error_type']=='RuntimeError'
assert pre['controller_error']=='v28 requires a loaded fixture receipt'
assert pre['child_poll']==0 and pre['child_commands_present'] is True
assert pre['fake_planner_close_present'] is True
assert cleanup['child_exit']==0
