import copy, hashlib, json, sys, zipfile
from pathlib import Path
archive=Path(sys.argv[1]).resolve();spec=json.loads(Path(sys.argv[2]).read_text())
sys.path.insert(0,str(archive))
from runtime.core_v1 import compiled_gui
if not compiled_gui.__file__.startswith(str(archive)+"/"):
    raise RuntimeError("not executing the archive")
rows=[]
def trial(expected, observed, effect=False):
    s=copy.deepcopy(spec);sequence=[0];inputs=[];verifications=[]
    if effect:s['actions']['enter']['expected_effect']={'phase':expected}
    else:s['method']['states']['empty']['branches'][0].update(when={'phase':expected},outcome='complete',action=None,next_state=None)
    def observe(request):
        sequence[0]+=1
        phase=(0 if sequence[0]==1 else observed) if effect else observed
        return dict(sequence=sequence[0],captured_ns=0,surface='form',predicates={'phase':phase},evidence_ref='frame'+str(sequence[0]),evidence_digest='digest'+str(sequence[0]))
    def admit(request):
        return dict(eligible=True,status='revalidated',authorization='one-use',expected_sequence=request['observation']['sequence'],valid_until_ns=100000000)
    def execute(request):
        inputs.append(request)
        return dict(status='completed',action_id='action',effect_ref='effect',release=dict(verified=True,keys_down=[],buttons_down=[]))
    def verify(request):
        verifications.append(request)
        return dict(status='succeeded',evidence_ref=request['observation']['evidence_ref'])
    result=compiled_gui.run(s,dict(observe=observe,admit=admit,execute=execute,verify_effect=verify,cancelled=lambda:False),clock=lambda:0)
    same=type(expected) is type(observed)
    want=('SAFE_YIELD','effect_failed') if effect else (('TASK_SUCCEEDED','method_complete') if same else ('SAFE_YIELD','unknown_state'))
    if (result['outcome'],result['reason']) != want or len(inputs)!=(1 if effect else 0) or verifications:
        raise RuntimeError('typed continuation regression')
    if effect and (result['completed_transitions']!=1 or result['pending_effect']['action']!='enter'):
        raise RuntimeError('lost prefix/effect')
    rows.append(dict(expected=expected,observed=observed,effect=effect,outcome=result['outcome'],reason=result['reason'],inputs=len(inputs)))
for expected,observed in ((0,False),(False,0),(1,True),(True,1)):
    trial(expected,observed);trial(expected,observed,True)
for value in (0,False,1,True,2,-1,'ready'):trial(value,value)
if any(name.startswith('research') for name in sys.modules):raise RuntimeError('research import')
print(json.dumps(dict(status='PASS_SCOPED',module=compiled_gui.__file__,archive_sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),rows=rows),indent=2))
