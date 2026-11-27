#!/usr/bin/env python3
import json
from pathlib import Path
root=Path(__file__).resolve().parent/'runs'
def need(ok,msg):
    if not ok: raise RuntimeError(msg)
rows=[]
for mode in ('normal','optimized'):
 for condition,count,global_mode,per_key in (('baseline',15,1,True),('global_off',1,0,True),('key_off',1,1,False)):
  folder=root/mode/condition
  need((folder/'container.exit-code.txt').read_text().strip()=='0',f'{mode}/{condition} container failed')
  r=json.loads((folder/'result.json').read_text())
  need(r['keypress_count']==count,f'{mode}/{condition} KeyPress count {r["keypress_count"]}')
  need(r['keyrelease_count']==count,f'{mode}/{condition} KeyRelease count {r["keyrelease_count"]}')
  need(r['global_auto_repeat']==global_mode and r['per_key_repeat_enabled'] is per_key,f'{mode}/{condition} control readback mismatch')
  need(r['independent_keymap_down_after_release'] is False,f'{mode}/{condition} key remained down')
  rows.append({'mode':mode,'condition':condition,'keypresses':count,'keyreleases':count,'neutral':True})
print(json.dumps({'status':'SCOPED_XTEST_CONTROL_PASS_NOT_PRODUCT_ACCEPTANCE','runs':rows},indent=2))