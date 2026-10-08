from pathlib import Path
import hashlib,json
root=Path(__file__).resolve().parent
record=json.loads((root/'recorded-reply-reuse.json').read_text())
source=root.parent/'primary-target-tools-live-04'/'case'
def require(ok,message):
    if not ok:raise ValueError(message)
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
for arm in record['arms']:
    directory=root/'recorded-reply-reuse-01'/('reuse' if arm['reuseReviewedImages'] else 'full')
    images=list((directory/'exchange').glob('image-*.png'))
    require(len(images)==arm['image_callbacks'],'image count changed')
    for attempt in range(1,8):
        require(json.loads((directory/'host'/f'reply-{attempt}.json').read_text())==json.loads((source/'host'/f'reply-{attempt}.json').read_text()),'original reply object changed')
    for ref in arm['references']:
        require(ref['base_attempt']==3,'wrong base')
        require(ref['base_reply_sha256']==digest(directory/'host'/'reply-3.json'),'wrong base reply identity')
        require(ref['base_review_sha256']==digest(directory/'host'/'review-3.json'),'wrong base review identity')
        require(ref['reply_sha256']==digest(directory/'host'/f"reply-{ref['attempt']}.json"),'wrong current reply identity')
        require(ref['image_sha256']==digest(directory/'exchange'/'image-5-1.png'),'wrong image identity')
        result=json.loads((directory/'exchange'/f"presentation-{ref['command']}.json").read_text())
        require(ref['schema']=='agent-interface/reviewed-image-reference-v1' and ref['mode']=='reviewed-image-reference','wrong reference type')
        require(not result['images'] and any(x=={k:v for k,v in ref.items() if k!='command'} for x in result['presented_text']),'reference omitted')
    require(digest(directory/'exchange'/'image-11-1.png')==digest(source/'exchange'/'image-11-1.png'),'changed final image omitted')
print(json.dumps({'status':'PASS_REUSE_IDENTITIES','scope':'Recorded replies only; reply objects, current/base/review/image byte identities and final changed PNG verified'},indent=2))