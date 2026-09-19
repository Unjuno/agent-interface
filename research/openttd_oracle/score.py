"""Read-only score over engine observations and a separately fixed tile contract."""
import argparse, copy, hashlib, json
from pathlib import Path

def score(observation, contract):
    tiles=observation['tiles']; edges=observation['edges']
    expected=contract['target']+contract['forbidden']
    if len(tiles)!=len(expected) or {t['id'] for t in tiles}!=set(expected):
        raise ValueError('missing/duplicate/unexpected tile observation')
    if any(type(t['road']) is not bool or type(t['owner']) is not int for t in tiles):
        raise ValueError('invalid tile types')
    indexed={t['id']:t for t in tiles}
    desired=list(zip(contract['target'],contract['target'][1:]))
    if len(edges)!=len(desired) or [(e[0],e[1]) for e in edges]!=desired:
        raise ValueError('missing or unexpected connection observation')
    if any(len(e)!=4 or type(e[2]) is not bool or type(e[3]) is not bool for e in edges):
        raise ValueError('invalid connection types')
    checks={'target_owned_roads':all(indexed[t]['road'] and indexed[t]['owner']==contract['owner'] for t in contract['target']),
            'bidirectional_connections':all(e[2] and e[3] for e in edges),
            'forbidden_row_clear':not any(indexed[t]['road'] for t in contract['forbidden'])}
    return {'success':all(checks.values()),'checks':checks}

def audit(root):
    manifest=json.loads((root/'manifest.json').read_text());research=Path(__file__).resolve().parent.parent
    for name,digest in manifest['sources'].items():assert hashlib.sha256((research/name).read_bytes()).hexdigest()==digest,name
    results=[]
    for seed in manifest['plan']['seeds']:
        p=root/str(seed);r=json.loads((p/'result.json').read_text());assert r['completed'] and r['all_owned_processes_exited']
        records=[json.loads(l.split('AIO ',1)[1]) for l in (p/'stderr.txt').read_text().splitlines() if 'AIO {' in l]
        assert [s['stage'] for s in records]==list(manifest['plan']['stages'])
        initial=records[0];x,y,w=initial['x'],initial['y'],initial['width']
        contract={'target':[y*w+x+i for i in range(3)],'forbidden':[(y+1)*w+x+i for i in range(3)],'owner':0}
        scored={s['stage']:score(s,contract) for s in records}
        assert {k:v['success'] for k,v in scored.items()}==manifest['plan']['stages'],scored
        complete=records[2]
        assert not score(complete,dict(contract,owner=1))['success']
        disconnected=copy.deepcopy(complete);disconnected['edges'][0][2]=False
        assert not score(disconnected,contract)['success']
        malformed=copy.deepcopy(complete);malformed['tiles'].pop()
        try:score(malformed,contract)
        except ValueError:pass
        else:raise AssertionError('missing observation accepted')
        results.append({'seed':seed,'contract':contract,'engine_stages':scored,
                        'counterfactual_controls':{'wrong_required_owner':True,'disconnected_observation':True,'missing_tile_rejected':True}})
    return {'scope':'oracle calibration only; no assistant gameplay or runtime promotion','results':results}

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('root',type=Path);a=ap.parse_args();r=audit(a.root)
    (a.root/'audit.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
