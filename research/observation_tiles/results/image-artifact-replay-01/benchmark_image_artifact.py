"""Counterbalanced offline replay; no claim of live-agent latency measurement."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from PIL import Image
from tile_transport import Frame
from image_artifact import ImageArtifactSink


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('source',type=Path)
    ap.add_argument('--out',type=Path,required=True); args=ap.parse_args()
    args.out.mkdir(parents=True,exist_ok=False)
    policies={'full6':(6,False),'reuse6':(6,True),'reuse1':(1,True)}
    here=Path(__file__).resolve().parent
    manifest=dict(scope='offline archived real-frame replay, not a new GUI rollout',
                  source=str(args.source.resolve()),policies=policies,
                  order='rotate all three policies by episode index',
                  durability='ordinary filesystem writes, no fsync; warm OS caches possible',
                  sources={n:hashlib.sha256((here/n).read_bytes()).hexdigest() for n in
                           ('image_artifact.py','test_image_artifact.py','benchmark_image_artifact.py')})
    (args.out/'manifest.json').write_text(json.dumps(manifest,indent=2))
    for n in manifest['sources']: (args.out/n).write_bytes((here/n).read_bytes())
    rows=[]
    episodes=sorted(args.source.glob('*/observations.jsonl'))
    if not episodes: raise ValueError('No source episodes')
    for index,observations in enumerate(episodes):
        records=[json.loads(x) for x in observations.read_text().splitlines()]
        frames=[]
        for r in records:
            with Image.open(observations.parent/'frames'/(r['sha256']+'.png')) as im:
                frame=Frame(im.width,im.height,im.mode,im.tobytes())
            assert hashlib.sha256(f'{frame.width},{frame.height},{frame.mode}:'.encode()+frame.pixels).hexdigest()==r['sha256']
            frames.append(frame)
        names=list(policies); names=names[index%3:]+names[:index%3]
        for name in names:
            level,reuse=policies[name]
            folder=args.out/observations.parent.name/name
            sink=ImageArtifactSink(folder,compress_level=level,reuse=reuse)
            outputs=[sink.publish(f) for f in frames]
            # Decode only after every timed publication in this episode/arm.
            for output,frame in zip(outputs,frames):
                with Image.open(output['image']) as im:
                    assert (im.width,im.height,im.mode,im.tobytes())==(frame.width,frame.height,frame.mode,frame.pixels)
            row=dict(episode=observations.parent.name,policy=name,samples=len(frames),
                     prepared_ms=sum(o['image_prepare_ns'] for o in outputs)/1e6,
                     files_written=sum(not o['image_reused'] for o in outputs),
                     png_disk_bytes=sum(p.stat().st_size for p in folder.glob('*.png')),
                     exact=True,observations=outputs)
            rows.append(row)
            (folder/'measurements.json').write_text(json.dumps(row,indent=2))
    summary=dict(episodes=len(episodes),source_frames=sum(r['samples'] for r in rows if r['policy']=='full6'),
                 decoded_artifacts=sum(r['samples'] for r in rows),errors=0,policies={})
    for name in policies:
        arm=[r for r in rows if r['policy']==name]
        summary['policies'][name]={k:sum(r[k] for r in arm) for k in ('prepared_ms','files_written','png_disk_bytes')}
    # Cluster by original app/seed pair, keeping both source trajectories together.
    pairs=sorted(set(r['episode'].rsplit('-',1)[0] for r in rows))
    rng=np.random.default_rng(424243); indexes=rng.integers(0,len(pairs),(10000,len(pairs)))
    summary['comparisons']={}
    for control,candidate in [('full6','reuse6'),('reuse6','reuse1')]:
        values=np.array([[sum(r['prepared_ms'] for r in rows if r['episode'].rsplit('-',1)[0]==pair and r['policy']==arm)
                          for arm in (control,candidate)] for pair in pairs])
        sums=values.sum(axis=0); boot=values[indexes].sum(axis=1)
        summary['comparisons'][control+'->'+candidate]=dict(time_reduction_percent=float(100*(1-sums[1]/sums[0])),
            ci95_percent=np.quantile(100*(1-boot[:,1]/boot[:,0]),[.025,.975]).tolist())
    (args.out/'summary.json').write_text(json.dumps(summary,indent=2))
    print(json.dumps(summary,indent=2))


if __name__=='__main__': main()
