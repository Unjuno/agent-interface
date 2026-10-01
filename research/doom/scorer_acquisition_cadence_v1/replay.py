"""Offline replay in a separately extracted evidence workspace; no GUI/model calls."""
import argparse, hashlib, json
from pathlib import Path
from audit import analyze, rows
from summarize import summarize

def run(root, pixels=True):
    root=Path(root);here=Path(__file__).resolve().parent
    plan=json.loads((here/'plan.json').read_text())
    for n,h in plan['source_sha256'].items():
        if hashlib.sha256((here/n).read_bytes()).hexdigest()!=h:raise ValueError('frozen source '+n)
    checked_images=0
    for spec in plan['cases']:
        out=root/'evidence'/spec['id'];r=analyze(out,root/'runtime',here)
        if not r['hard_pass']:raise ValueError(r['failures'])
        if pixels:
            from PIL import Image
            typed={}
            for e in rows(out/'runtime/events.jsonl'):
                if e.get('event')=='typed_observation':typed[e['sequence']]=e
                if e.get('event')!='observation':continue
                path=out/'runtime'/Path(e['image']).name
                with Image.open(path) as im:actual=hashlib.sha256(im.convert('RGB').tobytes()).hexdigest()
                if actual!=e['frame_rgb_sha256']:raise ValueError('image pixels '+str(path))
                t=typed.get(e['sequence'])
                if t and t.get('frame_rgb_sha256')!=actual:raise ValueError('typed/full image identity')
                checked_images+=1
    result=summarize(root/'evidence',root/'runtime')
    retained=json.loads((here/'results/summary.json').read_text())
    if result!=retained:raise ValueError('replayed aggregate differs')
    return {'cases':len(plan['cases']),'exact_images':checked_images,'acquisitions':result['totals']['valid_acquisitions'],
            'decision':result['decision'],'source_freeze_pass':True,'replayed_summary_exact':True}
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('root',type=Path);ap.add_argument('--no-pixels',action='store_true');a=ap.parse_args()
    print(json.dumps(run(a.root,not a.no_pixels),indent=2))
