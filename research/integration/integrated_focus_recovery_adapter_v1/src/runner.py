import json,sys
from pathlib import Path
from adapter import execute_with_policy

class FakeClient:
    def __init__(self,recovery=None,terminal_reason='focus_mismatch'):
        self.submit_calls=[]; self.recovery_queries=0; self.last_program=None
        self.recovery=recovery or {'focus':'B','surface':'B','geometry':[20,30,800,600],
                                   'authority':'none','task_input_granted':False,
                                   'evidence_role':'current_observation'}
        self.terminal_reason=terminal_reason
    def check(self,*args,**kwargs): return {'eligible':True}, {'noop':True}
    def submit(self,label,steps,timeout=10):
        self.submit_calls.append({'label':label,'steps':steps})
        self.last_program={'terminal':{'status':'rejected','reason':self.terminal_reason},'steps':steps}
        return self.last_program
    def observe_only(self):
        self.recovery_queries+=1
        return dict(self.recovery)

def case(case_id,policy):
    c=FakeClient()
    out=execute_with_policy(c,{'task_id':case_id,'token':'t'}, {'field':'f','submit':'s'},policy)
    return {'case_id':case_id,'policy':policy,**out,
            'submit_calls':c.submit_calls,'last_terminal':c.last_program['terminal']}

def main():
    schedule=json.loads(Path(sys.argv[1]).read_text())
    rows=[case(r['id'],r['policy']) for r in schedule]
    Path(sys.argv[2]).write_text(json.dumps(rows,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'rows':len(rows)}))
if __name__=='__main__': main()
