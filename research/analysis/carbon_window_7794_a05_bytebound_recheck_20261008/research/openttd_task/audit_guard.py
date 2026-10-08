"""Audit paired old-coordinate negative and corrected visual positive evidence."""
import copy,hashlib,json,sys
from pathlib import Path
from PIL import Image
from guarded_score import score,indexed
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'observation_tiles'))
from tile_transport import Decoder

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def episode(root,expected):
    m=json.loads((root/'manifest.json').read_text())
    for name,h in m['sources'].items():assert sha(HERE.parent/name)==h,name
    assert sha(HERE/'results/cohort-03/baseline.sav')==m['save_sha256']
    cleanup=json.loads((root/'cleanup.json').read_text());assert all(cleanup.values())
    r=json.loads((root/'evaluation.json').read_text());actual=score(r['observation'],r['baseline'])
    assert actual['success']==expected and all(actual[k]==r[k] for k in actual)
    logs=[json.loads(l.split('AIT ',1)[1]) for l in (root/'game-stderr.txt').read_text().splitlines() if 'AIT {' in l]
    assert logs[0]==r['baseline'] and logs[-1]==r['observation']
    assert not score(r['baseline'],r['baseline'])['success']
    events=[json.loads(l) for l in (root/'events.jsonl').read_text().splitlines()]
    decoder=Decoder('live-control');frames=[e for e in events if e['event']=='observation']
    for i,e in enumerate(frames,1):
        assert i==e['sequence'];frame=decoder.accept((root/f'{i:03d}.ait').read_bytes())
        with Image.open(root/Path(e['image']).name) as im:assert im.size==(frame.width,frame.height) and im.mode==frame.mode and im.tobytes()==frame.pixels
    terminals=[e for e in events if e['event']=='terminal'];assert terminals and all(e['status']=='completed' and e['release']['verified'] for e in terminals)
    return r,{'controller_scope':m['scope'],'exact_frames':len(frames),'programs':len(terminals),'initial_capture_to_last_terminal_ms':(terminals[-1]['terminal_ns']-frames[0]['capture_ns'])/1e6,'score':actual,'cleanup':cleanup}

def main():
    negative=HERE/'results/guard-01/episode';positive=HERE/'results/guard-self-use-01'
    n,nr=episode(negative,False);p,pr=episode(positive,True)
    assert indexed(n['baseline'])==indexed(p['baseline'])
    assert nr['score']['legacy_success'] and nr['score']['changed_surrounding_tiles']==[681]
    malformed=[]
    missing=copy.deepcopy(p['observation']);missing['guard'].pop();malformed.append(missing)
    duplicate=copy.deepcopy(p['observation']);duplicate['guard'][0]=duplicate['guard'][1];malformed.append(duplicate)
    contradiction=copy.deepcopy(p['observation'])
    next(t for t in contradiction['guard'] if t['id']==678)['road']=False;malformed.append(contradiction)
    invalid=copy.deepcopy(p['observation']);invalid['guard'][0]['road']=1;malformed.append(invalid)
    for sample in malformed:
        try:score(sample,p['baseline'])
        except ValueError:pass
        else:raise AssertionError('malformed guard accepted')
    owned=copy.deepcopy(p['observation']);owned['guard'][0]['owner']=99
    assert not score(owned,p['baseline'])['success']
    report={'negative_replay':nr,'corrected_visual_episode':pr,'same_initial_42_tile_guard':True,'malformed_records_rejected':len(malformed),'synthetic_outside_owner_change_rejected':True,'audit_source_sha256':sha(Path(__file__)), 'limits':'road presence/owner within 42 tiles only; not full world or all side effects; not held-out agent performance'}
    (HERE/'results/guard-audit.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))

if __name__=='__main__':main()
