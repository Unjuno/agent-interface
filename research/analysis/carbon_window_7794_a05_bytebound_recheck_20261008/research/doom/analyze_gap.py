"""Exploratory rendering diagnostic; crop checks are not game-success oracles."""
import hashlib,json
from pathlib import Path
from PIL import Image
from audit import audit

HERE=Path(__file__).resolve().parent

def main():
    root=HERE/'results/gap-01';manifest=json.loads((root/'manifest.json').read_text())
    for name,digest in manifest['sources'].items():
        assert hashlib.sha256((HERE/name).read_bytes()).hexdigest()==digest
    reports=[]
    for gap in ('0','20'):
        folder=root/gap;result=audit(folder)
        result['scope']='scripted exploratory gap probe; no assistant operation or game-success claim'
        (folder/'audit.json').write_text(json.dumps(result,indent=2))
        events=[json.loads(x) for x in (folder/'events.jsonl').read_text().splitlines()]
        frames=[]
        for row in events:
            if row['event']!='observation':continue
            with Image.open(folder/Path(row['image']).name) as im:
                world=im.convert('RGB').crop((321,181,961,580))
                pixels=list(world.getdata())
                frames.append(dict(sequence=row['sequence'],world_sha256=hashlib.sha256(world.tobytes()).hexdigest(),
                    nonblack_fraction=sum(any(c>15 for c in rgb) for rgb in pixels)/len(pixels)))
        reports.append(dict(gap_seconds=int(gap),frames=frames,
                            scope='post-hoc fixed crop, excludes HUD; no semantic correctness verdict'))
    (root/'render-diagnostic.json').write_text(json.dumps(reports,indent=2))
    folder=HERE/'results/shared-assistant-01'
    rows=[json.loads(x) for x in (folder/'events.jsonl').read_text().splitlines()]
    first=next(r for r in rows if r['event']=='observation')
    admission=next(r for r in rows if r['event']=='input_admission')
    values=[]
    for accepted in (r for r in rows if r['event']=='accepted'):
        image=next(r for r in rows if r['event']=='observation' and r['id']==accepted['id'])
        values.append(dict(id=accepted['id'],accept_to_local_image_ready_ms=(image['image_ready_ns']-accepted['accepted_ns'])/1e6))
    result=dict(initial_capture_to_first_input_admission_ms=(admission['admitted_ns']-first['capture_ns'])/1e6,
                programs=values,scope='local runtime clock; image-ready is not useful-feedback receipt or model-only latency',
                task_success=False,task_disposition='abandoned after black observation persisted; unfinished and alive at score')
    (folder/'interaction-analysis.json').write_text(json.dumps(result,indent=2))
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
