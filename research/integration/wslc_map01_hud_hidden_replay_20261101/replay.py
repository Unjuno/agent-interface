"""Post-hoc exact HUD-template replay; no controls or new game execution."""
import hashlib,io,json,subprocess,zipfile
from PIL import Image
BASE='f2bd781bfb88f5d24b43cb016ad90183b2156e05'
def blob(path,expected):
    data=subprocess.check_output(['git','show',BASE+':'+path])
    assert hashlib.sha256(data).hexdigest()==expected
    return zipfile.ZipFile(io.BytesIO(data))
old=blob('research/integration/wslc_map01_hud_template_review_20261031/v03.zip',
         'ab3cb73e220d5f4733d3f4bf85c9524edd8f7553bea6c86ef8246d2014b7b5b5')
new=blob('research/integration/wslc_map01_scripted_newseeds_20261101/public.zip',
         '05265fb0e0cd25745e44a25c2a7340943bd21b2508f51d787081db0caecf0085')
def image(z,name):return Image.open(io.BytesIO(z.read(name))).convert('RGB')
refs={name:image(old,name+'.png').tobytes() for name in ('50','49')}
box=(32,408,90,450)
def measure(im):
    data=im.crop(box).tobytes()
    differences={name:sum(abs(a-b) for a,b in zip(data,ref))/len(data) for name,ref in refs.items()}
    matches=[name for name,ref in refs.items() if data==ref]
    return {'exact':matches[0] if len(matches)==1 else 'unknown','mean_abs_rgb':differences,
            'crop_sha256':hashlib.sha256(data).hexdigest()}
positive=[measure(image(old,'output/frame-000.png')),measure(image(old,'output/frame-003.png'))]
assert [x['exact'] for x in positive]==['50','49']
rows=[]
for ident in ('es01','es02','es03','es04'):
    result=json.loads(new.read(ident+'/output/result.json'))
    samples=result['samples'];before=next(x for x in samples if x['label']=='before');end=samples[-1]
    for phase,sample in [('before',before),('end',end)]:
        measured=measure(image(new,f'{ident}/output/scene-{phase}.png'))
        rows.append({'allocation':ident,'phase':phase,'pixel_result':measured,
                     'adjacent_simulator_ammo':sample['ammo'],
                     'sampler_is_not_simultaneous_with_screenshot':True})
print(json.dumps({'status':'completed','scope':'post-hoc; no input; no new allocation',
                  'positive_controls':positive,'rows':rows},indent=2))
