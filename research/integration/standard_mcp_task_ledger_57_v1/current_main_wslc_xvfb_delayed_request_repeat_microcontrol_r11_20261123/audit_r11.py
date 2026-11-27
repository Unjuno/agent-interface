#!/usr/bin/env python3
import json
from pathlib import Path
folder=Path(__file__).resolve().parent/'runs/key-off'
def need(ok,msg):
    if not ok: raise RuntimeError(msg)
need((folder/'container.exit-code.txt').read_text().strip()=='0','R11 container failed')
r=json.loads((folder/'result.json').read_text())
need(r['global_auto_repeat']==1 and r['a_per_key_repeat_enabled'] is False,'A key-off control readback mismatch')
need(r['a_keypress_count']==1 and r['a_keyrelease_count']==1,'R11 A event count mismatch')
need(r['b_keypress_count']==1,'R11 delayed B press count mismatch')
need(r['final_keymap']=={'a_down':False,'b_down':False},'R11 final keymap not neutral')
need(1950 <= r['delayed_sync_elapsed_ms'] <= 2100,'R11 delay outside declared range')
print(json.dumps({'status':'SCOPED_DELAYED_XTEST_CONTROL_PASS_NOT_PRODUCT_ACCEPTANCE','delay_ms':r['delayed_sync_elapsed_ms'],'a_events':[1,1],'b_press':1,'final_keymap':r['final_keymap']},indent=2))