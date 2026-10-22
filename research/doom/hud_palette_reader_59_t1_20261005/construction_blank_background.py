"""Pre-repair blank-template feasibility, not a formal run or accuracy gate."""
import hashlib,json,sys
from pathlib import Path
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'research/doom'))
from doom_hud_signal_v1 import _wad_lumps,_render_patch,FREEDOOM2_SHA256
wad=Path(sys.argv[1]); lumps=_wad_lumps(wad,FREEDOOM2_SHA256)
palettes=np.frombuffer(lumps['PLAYPAL'],dtype=np.uint8).reshape(-1,256,3)
archive=ROOT/'research/doom/v16_comparison_unknown_59_4d74_20261004/guarded/run/episode/runtime'
rows=[]
for seq,palette_index in [(31,0),(35,9)]:
 p=Image.fromarray(_render_patch(lumps['STBAR'],palettes[palette_index]))
 canvas=Image.new('RGBA',(320,200));canvas.paste(p,(0,168))
 target=canvas.resize((640,480),Image.Resampling.NEAREST).convert('RGB')
 with Image.open(archive/f'{seq:03}.png') as opened:frame=opened.convert('RGB')
 for signal,x in [('health',102),('ammo',10)]:
  expected=np.array(target.crop((x,411,x+26,449)))
  actual=np.array(frame.crop((321+x,180+411,321+x+26,180+449)))
  rows.append({'sequence':seq,'palette':palette_index,'signal':signal,'stbar_source_size':p.size,'blank_exact_fraction':float(np.all(actual==expected,axis=2).mean()),'is_known_blank':signal=='ammo' or seq==31})
print(json.dumps({'purpose':'ordinary construction feasibility; no threshold search','rows':rows},indent=2))
