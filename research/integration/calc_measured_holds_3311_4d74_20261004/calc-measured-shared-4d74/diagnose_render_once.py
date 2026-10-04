import hashlib,json,pathlib
from PIL import Image
R=pathlib.Path(__file__).resolve().parent;D=R/'runs/measured_shared11';raw=json.loads((D/'raw.json').read_text());attempts=[json.loads(line) for line in (D/'OCR_ATTEMPTS.jsonl').read_text().splitlines()]
rows=[]
for call in attempts:
    p=D/pathlib.PurePosixPath(call['crop']).name;im=Image.open(p).convert('RGB');colors=im.getcolors(im.width*im.height)
    rows.append({'crop':p.name,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'size':list(im.size),'distinct_rgb_colors':len(colors),'all_white':colors==[(im.width*im.height,(255,255,255))],'ocr_stdout':call['stdout']})
artifact=raw['images'][1]['native']['artifact'];p=D/'guarded/images'/pathlib.PurePosixPath(artifact['path']).name
out={'original_png_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'original_digest_match':hashlib.sha256(p.read_bytes()).hexdigest()==artifact['sha256'],'rows':rows,'conclusion':'Both OCR input crops are entirely white. Actual saved first document independently scores correct. Capture does not show useful rendered numeric feedback. Timing/render mechanism unproven; do not call this a Tesseract glyph failure.','next':'Prospective bounded read-only observation continuation; no input replay; retain each capture/OCR attempt and stop reason'}
target=R/'RENDER_DIAGNOSTIC.json'
if target.exists():raise RuntimeError('first diagnostic retained')
target.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out))
