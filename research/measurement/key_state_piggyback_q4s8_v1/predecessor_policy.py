"""Research-only Shift-state reduction. No X11, filesystem, or input capability."""
from __future__ import annotations
import json, sys
MODES=('KEY_EDGES','FOCUS_KEYMAP')

def integer(v,lo=0,hi=2**63-1):return type(v) is int and lo<=v<=hi

def decode(s):
    if type(s) is not str or len(s)!=64 or any(c not in '0123456789abcdef' for c in s):raise ValueError('bad keymap')
    return bytes.fromhex(s)

def classify(p:dict,mode:str)->dict:
    def answer(status,down=None):return dict(status=status,shift_down=down,authority='none',input_dispatched=False)
    try:
        keys={'epoch','expected_epoch','window','keycode','seed_keymap','seed_focused','first_ordinal','events','coverage_complete'}
        if type(p) is not dict or set(p)!=keys or mode not in MODES:return answer('UNKNOWN')
        if type(p['epoch']) is not str or not p['epoch'] or p['epoch']!=p['expected_epoch']:return answer('UNKNOWN')
        if not integer(p['window'],1) or not integer(p['keycode'],8,255) or not integer(p['first_ordinal']):return answer('UNKNOWN')
        if p['seed_focused'] is not True or p['coverage_complete'] is not True or type(p['events']) is not list:return answer('UNKNOWN')
        code=p['keycode'];seed=decode(p['seed_keymap']);down=bool(seed[code//8]&(1<<(code%8)))
        known=True;focused=True;pending=False
        for i,e in enumerate(p['events']):
            if type(e) is not dict or not integer(e.get('ordinal')) or e['ordinal']!=p['first_ordinal']+i:return answer('UNKNOWN')
            if e.get('send_event') is not False or not integer(e.get('type')):return answer('UNKNOWN')
            t=e['type']
            if t in (2,3):
                if not integer(e.get('window'),1) or e['window']!=p['window'] or not integer(e.get('keycode'),8,255):return answer('UNKNOWN')
                if mode=='FOCUS_KEYMAP' and pending:known=False;pending=False
                if e['keycode']==code:down=t==2
            elif t in (9,10):
                if e.get('window')!=p['window'] or not integer(e.get('window'),1) or not integer(e.get('mode'),0,3) or not integer(e.get('detail'),0,7):return answer('UNKNOWN')
                if mode=='FOCUS_KEYMAP':
                    known=False;focused=t==9 and e['mode']==0
                    pending=focused
            elif t==11:
                m=decode(e.get('keymap'))
                if mode=='FOCUS_KEYMAP':
                    if not pending or not focused:return answer('UNKNOWN')
                    down=bool(m[code//8]&(1<<(code%8)));known=True;pending=False
            else:return answer('UNKNOWN')
        if mode=='FOCUS_KEYMAP' and (not known or not focused or pending):return answer('UNKNOWN')
        return answer('WAIT' if down else 'TYPE',down)
    except (ValueError,KeyError,TypeError):return answer('UNKNOWN')

if __name__=='__main__':
    if len(sys.argv)!=2:raise SystemExit(64)
    p=json.loads(sys.stdin.buffer.read())
    print(json.dumps(classify(p,sys.argv[1]),sort_keys=True))
