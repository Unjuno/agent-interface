"""Audit saved-task restore records without launching OpenTTD."""
import argparse,hashlib,json,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'openttd_oracle'))
from score import score

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def records(p):
    return [json.loads(l.split('AIT ',1)[1]) for l in (p/'stderr.txt').read_text().splitlines() if 'AIT {' in l]

def audit(root):
    m=json.loads((root/'manifest.json').read_text())
    for name,h in m['sources'].items():assert sha(HERE.parent/name)==h,name
    h=sha(root/'baseline.sav');base=records(root/'setup')[0];expected={k:v for k,v in base.items() if k!='stage'}
    contract={'target':[t['id'] for t in base['tiles'][:3]],'forbidden':[t['id'] for t in base['tiles'][3:]],'owner':0}
    counts={}
    for phase in ['setup','unsaved','restore-1','restore-2']:
        p=root/phase;r=json.loads((p/'result.json').read_text())
        assert r['all_owned_processes_exited'] and 'error' not in r
        assert sha(p/'screen.png')==r['screen_sha256']
        assert r['save_after']==h
        if phase=='setup':assert r['save_created']==h
        else:assert r['save_before']==h
        if phase=='unsaved':
            assert not r['ready'] and 'AIT_ERROR saved contract required' in (p/'stderr.txt').read_text()
            assert records(p)==[]
        else:
            assert r['ready']
            rs=records(p);assert rs
            if phase.startswith('restore'):assert rs[0]['stage']=='restored'
            for s in rs:
                assert {k:v for k,v in s.items() if k!='stage'}==expected
                assert not score(s,contract)['success']
            counts[phase]=len(rs)
    return {'scope':'saved task preparation, no shared-runtime or assistant gameplay',
            'save_sha256':h,'contract':contract,'matching_observations':counts,
            'unsaved_observer_rejected':True,'all_owned_processes_exited':True,
            'limits':'six tiles and two edges only; no full-world determinism, no crash-after-input reset, no timing claim'}

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('root',type=Path);a=ap.parse_args();r=audit(a.root)
    (a.root/'audit.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
