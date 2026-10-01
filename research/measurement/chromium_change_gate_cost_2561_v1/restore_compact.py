"""Restore exact measured RGB bytes; derived PNGs are NOT original captures.
No browser/experiment is launched. The frozen raw auditor runs on an explicitly
re-encoded view only. Original rows, PNG digests and timing bytes stay unchanged.
"""
from __future__ import annotations
import argparse, base64, copy, hashlib, io, json, lzma, shutil, subprocess, sys
from pathlib import Path, PurePosixPath
from PIL import Image

def sha(b): return hashlib.sha256(b).hexdigest()
def save(p,obj): p.write_text(json.dumps(obj,sort_keys=True,indent=2)+'\n')

def restore(source: Path, out: Path):
    manifest=json.loads((source/'COMPACT_MANIFEST.json').read_text())
    joined=b''
    for part in manifest['parts']:
        name=part['name']
        if Path(name).name!=name:raise ValueError('unsafe part name')
        content=(source/name).read_bytes()
        if sha(content)!=part['sha256']:raise ValueError('part hash')
        joined+=content.strip()
    blob=base64.b64decode(joined,validate=True)
    if sha(blob)!=manifest['compressed_sha256']:raise ValueError('compressed hash')
    dec=lzma.LZMADecompressor();payload=dec.decompress(blob,max_length=40_000_001)
    if not dec.eof or dec.unused_data or len(payload)>40_000_000:raise ValueError('bounded decode')
    if sha(payload)!=manifest['payload_sha256']:raise ValueError('payload hash')
    n=int.from_bytes(payload[:8],'big');meta=json.loads(payload[8:8+n]);pixels=payload[8+n:]
    if len(pixels)!=300*76800:raise ValueError('raster denominator')
    out.mkdir(parents=True,exist_ok=False)
    for name,item in meta['files'].items():
        rel=PurePosixPath(name)
        if rel.is_absolute() or '..' in rel.parts:raise ValueError('unsafe file path')
        b=item['content'].encode('utf-8')
        if sha(b)!=item['sha256']:raise ValueError('file hash')
        target=out/rel;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(b)
    rows=[json.loads(l) for l in (out/'formal-01/rows.jsonl').read_text().splitlines()]
    order=list(dict.fromkeys(im['rgb_sha256'] for r in rows for im in r['images']))
    if len(order)!=300:raise ValueError('distinct RGB denominator')
    derived=out/'derived-view';derived.mkdir();(derived/'frames').mkdir()
    for p in (out/'formal-01').iterdir():
        if p.name!='rows.jsonl':shutil.copyfile(p,derived/p.name)
    mappings={};previous=bytes(76800)
    for i,h in enumerate(order):
        delta=pixels[i*76800:(i+1)*76800]
        gray=bytes(a^b for a,b in zip(delta,previous));previous=gray
        image=Image.frombytes('L',(320,240),gray).convert('RGB');rgb=image.tobytes()
        if sha(rgb)!=h:raise ValueError('original measured RGB identity')
        encoded=io.BytesIO();image.save(encoded,format='PNG');png=encoded.getvalue();ph=sha(png)
        (derived/'frames'/(ph+'.png')).write_bytes(png)
        mappings[h]={'png_sha256':ph,'png_bytes':len(png),'rgb_sha256':h}
    transformed=copy.deepcopy(rows)
    for r in transformed:
        r['images']=[mappings[im['rgb_sha256']] for im in r['images']]
    (derived/'rows.jsonl').write_text(''.join(json.dumps(r,sort_keys=True)+'\n' for r in transformed))
    proc=subprocess.run([sys.executable,str(out/'audit.py'),str(derived),'--controls'],capture_output=True,text=True,timeout=60)
    (out/'DERIVED_AUDIT.stdout').write_text(proc.stdout);(out/'DERIVED_AUDIT.stderr').write_text(proc.stderr)
    if proc.returncode:raise RuntimeError('frozen auditor rejected derived view')
    got=json.loads(proc.stdout);expected=json.loads((out/'AUDIT.json').read_text())
    # Byte encoding size is expected to differ; every scientific field must match.
    got_science={k:v for k,v in got.items() if k!='png_bytes'}
    old_science={k:v for k,v in expected.items() if k!='png_bytes'}
    if got_science!=old_science:raise ValueError('original/derived audit disagreement')
    result={'status':'PASS_COMPACT_PIXEL_REVALIDATION','original_rgb_hashes_matched':300,
            'original_rows_sha256':sha((out/'formal-01/rows.jsonl').read_bytes()),
            'derived_rows_sha256':sha((derived/'rows.jsonl').read_bytes()),
            'scientific_audit_fields_equal':True,'original_png_encodings_in_compact_bundle':False,
            'derived_png_bytes':got['png_bytes'],'original_png_bytes':expected['png_bytes'],
            'formal_result':got['status'],'model_calls':0,'browser_calls':0,'new_measurements':0,
            'scope':'decoded original RGB retained exactly; PNG encodings regenerated as an explicit view; original metadata unchanged'}
    save(out/'COMPACT_REVALIDATION.json',result);print(json.dumps(result,indent=2))

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--source',type=Path,default=Path(__file__).resolve().parent)
    ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();restore(a.source,a.out)
