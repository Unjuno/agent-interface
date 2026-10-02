import json,sys
x=json.load(sys.stdin)
policy=x['policy'];intent=x['intent'];plan=x['plan'];cur=x['current']
allowed={'UNDO':'EDITOR','CONFIRM':'MODAL'}
raw={'UNDO':['CTRL','z'],'CONFIRM':['Return']}
reason=None;keys=None
if policy=='RAW_KEYSYM':
    keys=raw[intent]
elif policy=='SNAPSHOT_SYMBOLIC':
    if plan['layout_hash']!=cur['layout_hash']: reason='REFUSE_STALE_LAYOUT'
    elif plan['mode']!=cur['mode']: reason='REFUSE_STALE_CONTEXT'
    elif allowed[intent]!=plan['mode']: reason='REFUSE_CONTEXT'
    else: keys=raw[intent]
elif policy=='CURRENT_SYMBOLIC':
    if allowed[intent]!=cur['mode']: reason='REFUSE_CONTEXT'
    else: keys=raw[intent]
else: raise SystemExit('unknown policy')
out={'decision':'EMIT' if keys else reason,'keys':keys,'grants_action_authority':False}
print(json.dumps(out,sort_keys=True))
