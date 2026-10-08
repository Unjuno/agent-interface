"""Audit the five-tile L-road fixture without launching a model loop."""
import argparse,copy,hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent
from guarded_l_score_v1 import contract_from_baseline,score

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def records(path):return [json.loads(line.split('AIT ',1)[1]) for line in (path/'stderr.txt').read_text().splitlines() if 'AIT {' in line]

def rejects(observation,baseline,change):
    candidate=copy.deepcopy(observation);change(candidate)
    try:score(candidate,baseline)
    except (ValueError,KeyError,TypeError):return True
    return False

def audit(root):
    manifest=json.loads((root/'manifest.json').read_text())
    for name,digest in manifest['sources'].items():assert sha(HERE.parent/name)==digest,name
    assert manifest['plan']['seed']==991003
    saved=root/'baseline.sav';save_digest=sha(saved)
    setup=records(root/'setup');restored=records(root/'restore-1');assert setup and restored
    baseline=restored[0];contract=contract_from_baseline(baseline)
    assert len(contract['target'])==5 and len(contract['forbidden'])==4 and len(contract['guard'])==49
    initial=score(baseline,baseline)
    assert initial['success'] is False
    assert initial['checks']=={'target_owned_roads':False,'ordered_bidirectional_connections':False,'forbidden_tiles_clear':True,'surrounding_road_owner_unchanged':True}
    assert initial['changed_surrounding_tiles']==[]
    expected={k:v for k,v in baseline.items() if k!='stage'};phases={}
    for phase in ('setup','unsaved','restore-1','restore-2'):
        directory=root/phase;result=json.loads((directory/'result.json').read_text())
        assert result['all_owned_processes_exited'] and 'error' not in result
        assert sha(directory/'screen.png')==result['screen_sha256'] and result['save_after']==save_digest
        if phase=='setup':
            assert result['save_created']==save_digest and result['target_contract']['target']==contract['target']
        elif phase=='unsaved':
            assert result['ready'] is False and records(directory)==[]
            assert 'AIT_ERROR saved contract required' in (directory/'stderr.txt').read_text();continue
        current=records(directory);assert current
        for observation in current:
            assert {k:v for k,v in observation.items() if k!='stage'}==expected
            assert score(observation,baseline)['success'] is False
        phases[phase]=len(current)
    assert rejects(baseline,baseline,lambda r:r['edges'].pop())
    assert rejects(baseline,baseline,lambda r:r['guard'].pop())
    contradiction=lambda r:r['tiles'][0].update({'road':not r['tiles'][0]['road']})
    assert rejects(baseline,baseline,contradiction)
    observer='\n'.join(path.read_text() for path in sorted((HERE/'observer_l_v1').glob('*.nut')))
    for token in ('BuildRoad','RemoveRoad','BuildSign','ScrollCompanyClients'):assert token not in observer
    return {'audit_passed':True,'scope':'new L-objective fixture preparation; no model or shared-runtime task control',
            'seed':991003,'save_sha256':save_digest,'contract':contract,'initial_checks':initial['checks'],
            'matching_observations':phases,'unsaved_observer_rejected':True,'observer_mutation_tokens_absent':True,
            'malformed_controls':{'missing_edge_rejected':True,'missing_guard_rejected':True,'contradictory_overlap_rejected':True},
            'all_owned_processes_exited':True}

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('root',type=Path);args=parser.parse_args();result=audit(args.root)
    (args.root/'audit.json').write_bytes((json.dumps(result,indent=2)+'\n').encode('utf-8'));print(json.dumps(result,indent=2))
