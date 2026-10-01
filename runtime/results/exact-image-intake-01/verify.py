import base64,hashlib,io,json,tarfile
from pathlib import Path
from PIL import Image

def require(ok,message):
    if not ok:raise ValueError(message)
p=Path(__file__).resolve().parent;root=p.parents[2]
manifest=json.loads((p/'manifest.json').read_text())
for name,identity in manifest['files'].items():
    raw=(p/name).read_bytes()
    require(len(raw)==identity['bytes'] and hashlib.sha256(raw).hexdigest()==identity['sha256'],name)
result=json.loads((p/'result.json').read_text());totals={k:0 for k in result['totals']}
require(hashlib.sha256((p/'exact_gate.py').read_bytes()).hexdigest()==result['source']['sha256'],'frozen gate identity')
controls=json.loads((p/'controls.json').read_text())
require(controls['returncode']==0 and 'Ran 3 tests' in controls['stderr'] and 'OK' in controls['stderr'],'frozen controls')
for stream in result['streams']:
    archive=root/stream['archive'];require(hashlib.sha256(archive.read_bytes()).hexdigest()==stream['archive_sha256'],'input archive')
    counts={k:0 for k in totals};previous=None;base=0;sequence=0
    with tarfile.open(archive) as t:
        names=[x.name for x in t.getmembers() if x.isfile() and '/host/reply-' in x.name and x.name.endswith('.json')]
        names.sort(key=lambda n:int(n.rsplit('reply-',1)[1][:-5]))
        require(names==[x['member'] for x in stream['rows']],'all replies accounted')
        for row in stream['rows']:
            raw=t.extractfile(row['member']).read();reply=json.loads(raw)
            require(hashlib.sha256(raw).hexdigest()==row['reply_sha256'],'reply identity')
            content=reply['result']['content'];texts=[x['text'] for x in content if x['type']=='text'];pictures=[x for x in content if x['type']=='image']
            require([hashlib.sha256(x.encode()).hexdigest() for x in texts]==row['text_sha256'],'full text context')
            require(len(pictures)==row['image_count'] and reply['id']==row['attempt'],'reply shape')
            counts['calls']+=1
            if not pictures:continue
            require(len(pictures)==1,'single image')
            encoded=base64.b64decode(pictures[0]['data'],validate=True)
            im=Image.open(io.BytesIO(encoded));im.load();current=(im.width,im.height,im.mode,im.tobytes())
            sequence+=1;same=current==previous
            if not same:base=sequence
            value=json.loads(texts[0]);reference=value.get('image_reference',{});observation=value.get('observation_report',{}).get('observation',{})
            capture=reference.get('recorded_capture',observation)
            require(row['capture_started_ns']==capture['capture_started_ns'] and row['native_window_id']==capture['native_window_id'],'capture metadata')
            digest=hashlib.sha256(encoded).hexdigest()
            require(digest==row['image_sha256']==reference.get('sha256',observation.get('artifact',{}).get('sha256')),'image identity')
            require(row['omitted'] is same and row['sequence']==sequence and row['base_sequence']==base,'exact equality/base')
            require(row['metadata_preserved'] is True and row['pixels_reconstructed'] is True,'reconstruction claim')
            require([im.width,im.height]==row['dimensions'] and im.mode==row['mode'] and len(encoded)==row['png_bytes'],'frame shape')
            counts['images']+=1;counts['png_bytes']+=len(encoded)
            if same:counts['omitted_images']+=1;counts['omitted_png_bytes']+=len(encoded)
            previous=current
    for key,value in counts.items():
        require(stream[key]==value,'stream totals');totals[key]+=value
require(totals==result['totals'],'global totals')
print('PASS:',json.dumps(totals),'— reconstruction only; live adapter remains HOLD')
