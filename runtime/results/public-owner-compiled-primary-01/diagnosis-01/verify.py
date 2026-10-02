import hashlib,json
from pathlib import Path

def require(ok,message):
    if not ok: raise ValueError(message)
def read(path): return json.loads(path.read_text())
def verify_cases(root):
    root=Path(root); results=[]
    for case,expected in [('normal-compiled','association_changed'),('short-compiled','effect_failed')]:
        base=root/case; owner=read(base/'owner.json'); bridge=base/owner['bridge_relative']
        reports={read(p)['observation_id']:read(p) for p in bridge.glob('public-observation-*.json')}
        accepted=[read(p) for p in bridge.glob('observation-*.json')]
        require(len(reports)==7,'physical capture count')
        require(len(accepted)==(6 if case=='normal-compiled' else 7),'accepted observation count')
        require(sorted(x['sequence'] for x in accepted)==list(range(1,len(accepted)+1)),'history sequence')
        for report in reports.values():
            require(report['side_effect_authority'] is False and report['input_dispatched'] is False,'capture must have no authority')
            a=report['observation']['artifact']; path=base/'compiled-call'/'images'/Path(a['path']).name
            # The first public observation belongs to the observe call root.
            if not path.exists():
                suffix=a['path'].split('/'+case+'/',1)[1];path=base/suffix
            require(path.resolve().is_relative_to(base.resolve()),'artifact escapes case')
            require(hashlib.sha256(path.read_bytes()).hexdigest()==a['sha256'],'PNG identity')
        for observation in accepted:
            require(observation['observation_id'] in reports,'history capture absent')
            require(observation['native']==reports[observation['observation_id']]['observation'],'history capture identity')
        result=read(base/'owner-compiled-result.json'); receipt=result['method_receipt']
        require(receipt['outcome']=='SAFE_YIELD' and receipt['reason']==expected,'typed failure')
        require(receipt['completed_transitions']==1 and [x['action'] for x in receipt['transitions']]==['select'],'no move or Save')
        require(receipt['pending_effect']['action']=='select','unresolved select')
        require(receipt['transitions'][0]['release_verified'] is True,'input release')
        require(result['replay_allowed'] is False and result['task_success'] is None,'no invented task success or replay')
        rejected=set(reports)-{x['observation_id'] for x in accepted}
        if case=='normal-compiled':
            events=[read(p) for p in bridge.glob('capture-binding-changed-*.json')]
            require(len(events)==1 and len(rejected)==1,'rejected capture ledger')
            event=events[0];require(event['before']['focus']==6291463 and event['after']['focus']==6291464,'recorded focus change')
            require(event['before']['surface']==event['after']['surface'] and event['before']['geometry']==event['after']['geometry'],'recorded surface and geometry')
            rejected_report=read(bridge/event['public_report'])
            require(rejected_report['observation_id'] in rejected and event['last_valid_sequence']==6,'rejected frame not accepted')
            require(event['authority_granted'] is False and event['replay_allowed'] is False,'rejected frame has no authority')
            require(result['feedback']['image'] is None and result['feedback']['image_status']=='needs_review','obsolete final image withheld')
            require([x['sequence'] for x in receipt['observations']]==[2],'graph prefix retained')
        else:
            require(not rejected,'short capture acceptance')
            require([x['sequence'] for x in receipt['observations']]==[2,7],'short graph history')
            require(receipt['observations'][-1]['predicates']['selected_shape'] is False,'selection failed')
        evaluation=read(base/'evaluation.json');cleanup=read(base/'cleanup.json')
        require(evaluation['success'] is False and evaluation['after_all_owned_processes_terminal'] is True,'independent task failure')
        require(evaluation['rectangles']==[{'x':50.0,'y':50.0,'width':40.0,'height':30.0,'transform':None}],'persisted geometry unchanged')
        require(hashlib.sha256((base/'two-rectangles.svg').read_bytes()).hexdigest()==evaluation['svg_sha256'],'actual saved SVG identity')
        require(evaluation['svg_sha256']=='d3609147876f3f2d0949c4e2199b2befaf8854cb81804ab0025934e699512f04','persisted SVG identity')
        require(cleanup['host_exit']==0 and cleanup['all_owned_processes_terminal'] is True,'owned lifecycle terminal')
        results.append({'case':case,'physical_captures':len(reports),'accepted_observations':len(accepted),'rejected_captures':len(rejected),'reason':expected,'movement_reached':False,'Save':0})
    return {'cases':results,'physical_captures':14,'accepted_observations':13,'status':'HOLD_LIVE_PUBLIC_OWNER_QUALIFICATION'}

if __name__=='__main__':
    print(json.dumps(verify_cases(Path(__file__).resolve().parent.parent),indent=2))
