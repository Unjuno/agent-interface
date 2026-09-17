from __future__ import annotations
import json, sys, time
from Xlib import X, display

WIDTH=320; HEIGHT=240; SX=144; SY=104; SW=32; SH=32
COLORS={
    'VALID_CONTINUATION': (0,65535,0),
    'AMBIGUOUS_BOUNDARY': (65535,65535,0),
    'HARD_INVALIDATION': (65535,0,0),
}

def emit(obj):
    print(json.dumps(obj, sort_keys=True), flush=True)

def sleep_until_ns(target):
    while True:
        now=time.perf_counter_ns()
        rem=target-now
        if rem<=0: return
        if rem>2_000_000:
            time.sleep((rem-500_000)/1e9)
        elif rem>100_000:
            time.sleep(rem/2e9)

D=display.Display()
S=D.screen()
root=S.root
black=S.default_colormap.alloc_color(0,0,0).pixel
pixels={name:S.default_colormap.alloc_color(*rgb).pixel for name,rgb in COLORS.items()}
win=root.create_window(40,40,WIDTH,HEIGHT,0,S.root_depth,X.InputOutput,X.CopyFromParent,background_pixel=black,event_mask=X.ExposureMask)
win.map(); D.sync()
gcs={name:win.create_gc(foreground=pixel) for name,pixel in pixels.items()}
current='VALID_CONTINUATION'

def transition(state, case_id=None, kind='state'):
    global current
    begin=time.perf_counter_ns()
    win.fill_rectangle(gcs[state], SX,SY,SW,SH)
    D.sync()
    applied=time.perf_counter_ns()
    current=state
    emit({'event':kind,'case_id':case_id,'state':state,'begin_ns':begin,'applied_ns':applied})
    return applied

transition(current, kind='initial_state')
emit({'event':'ready','xid':win.id,'width':WIDTH,'height':HEIGHT,'sentinel':[SX,SY,SW,SH]})

for raw in sys.stdin:
    if not raw.strip(): continue
    cmd=json.loads(raw)
    op=cmd['cmd']
    if op=='set':
        transition(cmd['state'], cmd.get('case_id'), kind='set_state')
    elif op=='schedule':
        case_id=cmd['case_id']
        horizon_ns=int(cmd['horizon_ns'])
        start_ns=time.perf_counter_ns()+20_000_000
        emit({'event':'schedule_start','case_id':case_id,'start_ns':start_ns,'horizon_ns':horizon_ns})
        for event in cmd['events']:
            target=start_ns+int(event['offset_ns'])
            sleep_until_ns(target)
            transition(event['state'],case_id,kind='scheduled_state')
        sleep_until_ns(start_ns+horizon_ns)
        emit({'event':'schedule_done','case_id':case_id,'end_ns':time.perf_counter_ns()})
    elif op=='exit':
        emit({'event':'exit','t_ns':time.perf_counter_ns()})
        break
    else:
        emit({'event':'error','error':f'unknown command {op}'})
        break
D.close()
