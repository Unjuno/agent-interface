"""Post-run replay of retained images, resolver decisions and app receipts."""
import argparse, base64, gzip, hashlib, io, json
from collections import Counter, defaultdict
from pathlib import Path
from PIL import Image
from resolver import ARMS, regions, resolve
from fixture import CASES


def audit(paths):
    counts={a:Counter() for a in ARMS};checks=Counter();groups=defaultdict(set)
    cases={a:{} for a in ARMS};details=[]
    for path in paths:
        raw=Path(path).read_bytes();p=json.loads(gzip.decompress(raw))
        receipts=defaultdict(list)
        for e in p['receipts']:receipts[e['token']].append(e)
        assert len(p['records'])==len(CASES)*len(ARMS)
        for r in p['records']:
            observations=r['observations'];assert len(observations)==3
            for i,o in enumerate(observations):
                png=base64.b64decode(p['pngs'][o['image_sha256']],validate=True)
                assert hashlib.sha256(png).hexdigest()==o['image_sha256']
                im=Image.open(io.BytesIO(png)).convert('RGB')
                assert im.size==(800,600)
                assert hashlib.sha256(im.tobytes()).hexdigest()==o['pixel_sha256']
                assert regions(im)==o['regions'];checks['image_and_regions']+=1
                groups[(r['layout'],r['case'],i)].add(o['pixel_sha256'])
            decision=resolve(r['arm'],observations[0]['regions'],observations[1]['regions'],
                             observations[2]['regions'],observations[2]['native'],p['plan']['grid_size'])
            assert decision==r['decision'];checks['decision_replay']+=1
            assert r['empty'] is True;checks['empty_input']+=1
            es=receipts[r['token']]
            if decision['point'] is None:
                assert r['press_ns'] is None and not es;status='abstain'
            else:
                assert r['release_ns']>=r['press_ns']>=observations[2]['capture_ns']
                assert len(es)==1 and es[0]['trusted'] is True
                assert [es[0]['x'],es[0]['y']]==[round(x) for x in decision['point']]
                status={'target':'correct','decoy':'wrong_target','occluder':'wrong_target','background':'no_effect'}[es[0]['kind']]
            counts[r['arm']][status]+=1;cases[r['arm']].setdefault(r['case'],[]).append(status)
            details.append({'token':r['token'],'outcome':status,'decision':decision})
    assert all(len(s)==1 for s in groups.values());checks['matched_image_groups']=len(groups)
    good={'stable_small','linear_move','unexpected_jump','duplicate_native','canvas_only'}
    hybrid_ok=all(all(x==('correct' if c in good else 'abstain') for x in ss) for c,ss in cases['hybrid'].items())
    return {'scope':'staged calibrated mechanics, not VLM/general GUI efficacy','counts':counts,
            'cases':cases,'checks':checks,'hybrid_preregistered_gate':hybrid_ok,
            'decision':'RETAIN_SCOPED_HYBRID_MECHANICS' if hybrid_ok else 'FAIL_RETAIN_FIRST_OUTCOME','details':details}

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('archives',nargs='+');ap.add_argument('--out',type=Path,required=True)
    a=ap.parse_args();result=audit(a.archives)
    with a.out.open('x') as f:json.dump(result,f,sort_keys=True,indent=2)
    print(json.dumps({k:v for k,v in result.items() if k not in ('details','cases')},indent=2))
