#!/usr/bin/env python3
import json,sys
p=json.load(sys.stdin)
if set(p) != {'policy','keycode','current_epoch','old_shift_down','bootstrap','events'}: raise SystemExit('bad fields')
if type(p['keycode']) is not int or type(p['old_shift_down']) is not bool: raise SystemExit('bad types')
if p['policy']=='CARRY_OLD_STATE':
    down=p['old_shift_down']
elif p['policy']=='REBOOTSTRAP_ON_RECONNECT':
    b=p['bootstrap']
    if not isinstance(b,dict) or b.get('epoch')!=p['current_epoch'] or not isinstance(b.get('shift_down'),bool):
        print(json.dumps({'decision':'UNKNOWN','reason':'bootstrap_missing_or_foreign','shift_down':None},sort_keys=True)); raise SystemExit
    down=b['shift_down']
else: raise SystemExit('bad policy')
last=0
for e in p['events']:
    if set(e) != {'seq','epoch','kind','detail'}: raise SystemExit('bad event fields')
    if e['epoch']!=p['current_epoch'] or type(e['seq']) is not int or e['seq']<=last: raise SystemExit('bad event lineage')
    last=e['seq']
    if e['detail']==p['keycode']:
        if e['kind']=='KeyPress': down=True
        elif e['kind']=='KeyRelease': down=False
        else: raise SystemExit('bad kind')
print(json.dumps({'decision':'WAIT' if down else 'CONTINUE','reason':'reduced','shift_down':down},sort_keys=True))
