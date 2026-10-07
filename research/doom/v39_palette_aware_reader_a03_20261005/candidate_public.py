"""One-shot saved-pixel palette-aware paired HUD diagnostic; no input authority."""
import os
os.environ['OMP_NUM_THREADS']='1'; os.environ['OPENBLAS_NUM_THREADS']='1'; os.environ['MKL_NUM_THREADS']='1'
import hashlib, json, platform, sys, time
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
from PIL import Image, __version__ as pillow_version

ROOT=Path(__file__).resolve().parent
SOURCE=ROOT/'source'
sys.path.insert(0,str(SOURCE))
from doom_hud_signal_v1 import _render_patch, _wad_lumps
from doom_hud_signal_v3 import DoomStatusNumberReader
from doom_hud_signal_v1 import FREEDOOM2_SHA256


def sha_bytes(data): return hashlib.sha256(data).hexdigest()
def sha_file(path): return sha_bytes(Path(path).read_bytes())
def mini(row): return {'status':row.get('status'),'value':row.get('value'),'reason':row.get('reason')}
def observed_value(row):
    return row.get('status')=='observed' and type(row.get('value')) is int

def resolve(palette_rows):
    candidates=[]
    for row in palette_rows:
        h,a=row['health'],row['ammo']
        if observed_value(h) and observed_value(a):
            candidates.append((row['palette'],(h['value'],a['value'])))
    pairs=sorted({pair for _,pair in candidates})
    if not pairs: return {'status':'unknown','reason':'no_common_palette','value':None,'palettes':[]}
    if len(pairs)!=1: return {'status':'unknown','reason':'ambiguous_pairs','value':None,'palettes':[],'candidate_pairs':[list(p) for p in pairs]}
    pair=pairs[0]
    return {'status':'observed','reason':None,'value':{'health':pair[0],'ammo':pair[1]},
            'palettes':[i for i,p in candidates if p==pair]}

def main():
    started=datetime.now(timezone.utc).isoformat(); t0=time.perf_counter_ns()
    freeze=json.loads((ROOT/'FREEZE.executed.json').read_text(encoding='utf-8'))
    for rel,expected in freeze['files_sha256'].items():
        if rel in {'candidate.py','prepare_freeze.py','audit.py'}: continue
        if sha_file(ROOT/rel)!=expected: raise SystemExit('STOP public input/source hash mismatch: '+rel)
    wad_value=os.environ.get('FREEDOOM2_WAD')
    if not wad_value: raise SystemExit('FREEDOOM2_WAD must point to the hash-pinned WAD')
    wad=Path(wad_value)
    if sha_file(wad)!=freeze['wad_sha256'] or freeze['wad_sha256']!=FREEDOOM2_SHA256:
        raise SystemExit('STOP WAD hash mismatch')
    event_path=ROOT/'input/guarded/runtime/events.jsonl'
    rows=[json.loads(line) for line in event_path.read_text(encoding='utf-8').splitlines()]
    typed={row['sequence']:row for row in rows if row.get('event')=='typed_observation'}
    full={row['sequence']:row for row in rows if row.get('event')=='observation'}
    if set(typed)!=set(range(1,36)) or set(full)!=set(range(1,36)):
        raise SystemExit('STOP episode observation identity mismatch')
    lumps=_wad_lumps(wad,freeze['wad_sha256'])
    raw_playpal=lumps['PLAYPAL']
    if len(raw_playpal)%768: raise SystemExit('STOP incomplete PLAYPAL')
    palettes=np.frombuffer(raw_playpal,dtype=np.uint8).reshape(-1,256,3)
    if len(palettes)!=freeze['palette_count_expected']: raise SystemExit('STOP palette count mismatch')
    glyph_size=(26,38)
    template_sets=[]
    for palette in palettes:
        group=[]
        for digit in range(10):
            patch=Image.fromarray(_render_patch(lumps[f'STTNUM{digit}'],palette))
            resized=np.asarray(patch.resize(glyph_size,Image.Resampling.NEAREST))
            group.append((resized[:,:,:3],resized[:,:,3]>0))
        template_sets.append(group)
    readers={sig:DoomStatusNumberReader(wad,signal_id=sig) for sig in ('health','ammo')}
    image_results=[]
    for seq in range(1,36):
        obs=typed[seq]
        path=ROOT/'input/guarded/runtime'/f'{seq:03}.png'
        with Image.open(path) as opened: frame=opened.convert('RGB')
        rgb_sha=sha_bytes(frame.tobytes())
        if rgb_sha!=obs.get('frame_rgb_sha256') or rgb_sha!=full[seq].get('frame_rgb_sha256'):
            raise SystemExit(f'STOP frame RGB mismatch sequence {seq}')
        palette_rows=[]
        for index,templates in enumerate(template_sets):
            pairrow={'palette':index}
            for sig,reader in readers.items():
                reader.templates=templates
                pairrow[sig]=mini(reader.read_frame(obs,frame))
            palette_rows.append(pairrow)
        # Palette 0 is exactly the established fixed-template baseline.
        baseline={sig:palette_rows[0][sig] for sig in ('health','ammo')}
        recorded={sig:mini(obs['signals'][sig]) for sig in ('health','ammo')}
        image_results.append({'sequence':seq,'frame_rgb_sha256':rgb_sha,'baseline_palette0':baseline,
            'recorded_typed':recorded,'palette_rows':palette_rows,'resolved':resolve(palette_rows)})
    blank=Image.new('RGB',(1280,800),(0,0,0))
    blank_obs={'sequence':999,'capture_ns':1,'pointer_binding':typed[1]['pointer_binding']}
    blank_rows=[]
    for index,templates in enumerate(template_sets):
        row={'palette':index}
        for sig,reader in readers.items():
            reader.templates=templates
            row[sig]=mini(reader.read_frame(blank_obs,blank))
        blank_rows.append(row)
    synthetic={
      'no_common_palette':{'rows':[{'palette':0,'health':{'status':'observed','value':97},'ammo':{'status':'unknown','value':None}},
                                    {'palette':1,'health':{'status':'unknown','value':None},'ammo':{'status':'observed','value':47}}]},
      'ambiguous_pairs':{'rows':[{'palette':0,'health':{'status':'observed','value':97},'ammo':{'status':'observed','value':47}},
                                  {'palette':9,'health':{'status':'observed','value':100},'ammo':{'status':'observed','value':47}}]},
      'same_pair_multiple_palettes':{'rows':[{'palette':0,'health':{'status':'observed','value':97},'ammo':{'status':'observed','value':47}},
                                             {'palette':9,'health':{'status':'observed','value':97},'ammo':{'status':'observed','value':47}}]}}
    for c in synthetic.values(): c['resolved']=resolve(c['rows'])
    held=set(freeze['heldout_sequences'])
    heldout=[r for r in image_results if r['sequence'] in held]
    holdout_equal=sum(r['resolved']['status']==r['recorded_typed']['health']['status']==r['recorded_typed']['ammo']['status']=='observed' and
        r['resolved']['value']=={'health':r['recorded_typed']['health']['value'],'ammo':r['recorded_typed']['ammo']['value']}
        for r in heldout)
    seq31=next(r for r in image_results if r['sequence']==31)['resolved']
    seq35=next(r for r in image_results if r['sequence']==35)['resolved']
    blank_resolved=resolve(blank_rows)
    passed=(holdout_equal==33 and seq31.get('value')=={'health':97,'ammo':47} and
       seq35.get('value')=={'health':100,'ammo':47} and blank_resolved['status']=='unknown' and
       synthetic['no_common_palette']['resolved']['status']=='unknown' and
       synthetic['ambiguous_pairs']['resolved']['status']=='unknown' and
       synthetic['same_pair_multiple_palettes']['resolved']['value']=={'health':97,'ammo':47})
    finished=datetime.now(timezone.utc).isoformat()
    raw={'schema':'v39-palette-aware-reader-a03-raw','started_at':started,'finished_at':finished,
      'base_commit':freeze['base_commit'],'freeze_sha256':sha_file(ROOT/'FREEZE.executed.json'),
      'source_sha256':freeze['source_sha256'],'wad_sha256':freeze['wad_sha256'],
      'python':platform.python_version(),'pillow':pillow_version,'numpy':np.__version__,
      'cpu_policy':'single process; OMP/OPENBLAS/MKL thread counts set to 1; no OS memory/CPU enforcement',
      'criteria':freeze['decision'],'case_count':35,'palette_count':len(palettes),
      'heldout_count':len(held),'heldout_exact_matches':holdout_equal,
      'sequence31_resolved':seq31,'sequence35_resolved':seq35,
      'blank_no_hud_control':{'palette_rows':blank_rows,'resolved':blank_resolved},
      'synthetic_controls':synthetic,'images':image_results,
      'real_game_used':False,'real_input_used':False,'model_used':False,
      'runtime_modified':False,'input_authority_granted':False,
      'elapsed_ms':(time.perf_counter_ns()-t0)/1e6,
      'disposition':'PASS_COMPATIBILITY_ONLY' if passed else 'FAIL_OR_HOLD_AS_PREREGISTERED'}
    target=Path(os.environ.get('PALETTE_A03_OUTPUT',str(ROOT/'output/raw.json')))
    if target.exists(): raise SystemExit('STOP output collision')
    target.write_text(json.dumps(raw,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'disposition':raw['disposition'],'frames':35,'heldout_exact_matches':holdout_equal,
      'seq31':seq31,'seq35':seq35,'blank':blank_resolved,'elapsed_ms':raw['elapsed_ms']}))
if __name__=='__main__': main()
