"""Read-only diagnosis; does not retrain, replay native input, or regrade G08."""
import hashlib,json,pathlib
from PIL import Image
from digit_reader import split
R=pathlib.Path(__file__).resolve().parent;D=R/'runs/compiled_digits08'
raw=json.loads((D/'raw.json').read_text(encoding='utf-8'));model=json.loads((R/'DIGIT_TEMPLATES.json').read_text())['glyphs']
image=raw['images'][1];art=image['native']['artifact'];p=D/'guarded/images'/art['path'].rsplit('/',1)[-1]
if hashlib.sha256(p.read_bytes()).hexdigest()!=art['sha256']:raise RuntimeError('original PNG hash')
rows=[]
for label,box in zip(['23','31','713'],[(37,161,124,175),(127,161,215,175),(217,161,305,175)]):
    items=[]
    for i,bits in enumerate(split(Image.open(p),box)):
        variants=[]
        for template,digit in model.items():
            if len(template)==len(bits) and [len(line) for line in template.splitlines()]==[len(line) for line in bits.splitlines()]:
                variants.append({'digit':digit,'different_bits':sum(a!=b for a,b in zip(template,bits)),'template':template})
        best=min((v['different_bits'] for v in variants),default=None)
        items.append({'expected_diagnostic_label':label[i] if i<len(label) else None,'recognized':model.get(bits),'bits':bits,'closest_same_shape':[v for v in variants if v['different_bits']==best]})
    rows.append({'cell_label_from_saved_oracle':label,'segments':items})
out={'scope':'post-failure diagnostic only; saved truth labels never supplied to controller','original_png_sha256':art['sha256'],'rows':rows,'training_changed':False,'original_disposition':'FAIL_HELDOUT_DIGIT_TRANSFER_HOLD_COMPARISON'}
target=R/'GLYPH_DIAGNOSTIC.json'
if target.exists():raise RuntimeError('diagnostic output retained')
target.write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'cells':[{'label':r['cell_label_from_saved_oracle'],'glyphs':[{'expected':g['expected_diagnostic_label'],'recognized':g['recognized'],'nearest':[(v['digit'],v['different_bits']) for v in g['closest_same_shape']]} for g in r['segments']]} for r in rows]}))
