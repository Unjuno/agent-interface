"""Replay score against engine-authored positive and negative states."""
import copy
import hashlib
import json
from pathlib import Path
from mindustry_flow_score_v1 import score

HERE=Path(__file__).resolve().parent

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())

def main():
    root=HERE/'results/mindustry-flow-01';manifest=read(root/'manifest.json');plan=manifest['plan']
    for name,digest in manifest['sources'].items():assert sha(HERE.parent/name)==digest,name
    results=read(root/'results.json');assert [r['case'] for r in results]==plan['cases']
    scores={}
    for result in results:
        out=root/result['case']
        assert result['ready'] and result['all_owned_processes_exited'] and result['windows'].strip()
        assert sha(out/'screen.png')==result['screen_sha256']
        before,after=read(out/'before.json'),read(out/'after.json')
        value=score(before,after,plan)
        assert value['contract_satisfied'] is plan['expected_success'][result['case']],(result['case'],value)
        scores[result['case']]=value
    before,after=read(root/'complete/before.json'),read(root/'complete/after.json')
    controls={}
    for name in ('missing_tile','duplicate_tile','open_window','too_early','boolean_copper','claimed_authority'):
        bad=copy.deepcopy(after)
        if name=='missing_tile':bad['tiles'].pop()
        elif name=='duplicate_tile':bad['tiles'][-1]=bad['tiles'][0]
        elif name=='open_window':bad['paused']=False
        elif name=='too_early':bad['tick']=before['tick']+1
        elif name=='boolean_copper':bad['copper']=True
        elif name=='claimed_authority':bad['task_success']=True
        value=score(before,bad,plan)
        assert value['status']=='UNKNOWN' and value['contract_satisfied'] is None,(name,value)
        controls[name]=value
    report={'scope':'engine-authored scoring calibration, not agent benchmark performance',
            'cases':scores,'malformed_or_open_controls':controls,
            'score_sha256':sha(HERE/'mindustry_flow_score_v1.py'),'audit_sha256':sha(Path(__file__)),
            'score_implementation_timing':'implemented after first complete-state inspection; contract plan frozen before engine runs',
            'agent_task_success':None}
    (root/'audit.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))

if __name__=='__main__':main()
