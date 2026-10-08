"""Execute synthetic success/negative controls inside a committed-source zipapp."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from probe import spec

CODE = r'''
import json, sys
sys.path.insert(0, sys.argv[1])
from runtime.core_v1.compiled_gui import run
interface = json.loads(sys.argv[2])
verdict = json.loads(sys.argv[3])
count = {'observe':0,'execute':0,'verify':0}
def observe(p):
    count['observe'] += 1
    i=count['observe']
    return dict(sequence=i,captured_ns=0,surface='form',predicates={'phase':i-1},evidence_ref='frame'+str(i),evidence_digest='digest'+str(i))
def admit(p):
    return dict(eligible=True,status='revalidated',authorization='one-use',expected_sequence=p['observation']['sequence'],valid_until_ns=100000000)
def execute(p):
    count['execute'] += 1
    return dict(status='completed',action_id=str(count['execute']),effect_ref='effect',release=dict(verified=True,keys_down=[],buttons_down=[]))
def verify(p):
    count['verify'] += 1
    return verdict
result=None; exception=None
try:
    result=run(interface,dict(observe=observe,admit=admit,execute=execute,verify_effect=verify,cancelled=lambda:False),clock=lambda:0)
except ValueError:
    exception='ValueError'
print(json.dumps(dict(outcome=result['outcome'] if result else None,reason=result['reason'] if result else None,count=count,exception=exception,research_imported=any(n.startswith('research') for n in sys.modules))))
'''

if __name__ == '__main__':
    archive, output = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve()
    cases = [({'status':'succeeded','evidence_ref':None},None,None,1,'ValueError'),
             ({'status':'succeeded','evidence_ref':'witness'},'TASK_SUCCEEDED','method_complete',2,None),
             ({'status':'failed','evidence_ref':None},'SAFE_YIELD','effect_failed',1,None),
             ({'status':'unavailable','evidence_ref':None},'SAFE_YIELD','effect_unavailable',1,None)]
    rows = []
    for verdict, outcome, reason, steps, exception in cases:
        child = subprocess.run([sys.executable,'-I','-S','-c',CODE,str(archive),json.dumps(spec()),json.dumps(verdict)],
                               capture_output=True,timeout=15)
        actual = json.loads(child.stdout) if child.returncode == 0 else None
        want = {'outcome':outcome,'reason':reason,'exception':exception,'count':{'observe':steps+1,'execute':steps,'verify':steps},'research_imported':False}
        rows.append({'verdict':verdict,'actual':actual,'expected':want,'exit_code':child.returncode,
                     'stderr_sha256':hashlib.sha256(child.stderr).hexdigest(),'pass':actual==want and child.returncode==0})
    result={'archive_sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'rows':rows,'pass':all(x['pass'] for x in rows)}
    with output.open('x',encoding='utf-8',newline='\n') as stream:
        json.dump(result,stream,indent=2,sort_keys=True);stream.write('\n')
    print(json.dumps({'pass':result['pass'],'rows':len(rows),'archive_sha256':result['archive_sha256']}))
    sys.exit(0 if result['pass'] else 1)
