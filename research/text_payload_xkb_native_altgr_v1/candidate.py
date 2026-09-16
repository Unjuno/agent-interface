"""Native-XKB whole-payload direct printable-ASCII lowering; no keymap mutation or Compose."""
from __future__ import annotations
from dataclasses import dataclass
import hashlib,json,re,time
from Xlib import X, XK
from Xlib.ext import xtest
class Rejected(ValueError): pass
@dataclass(frozen=True)
class Stroke:
    code:int; shift:bool; level3:bool; level:int
@dataclass(frozen=True)
class Plan:
    text:str; strokes:tuple[Stroke,...]; shift_code:int; level3_code:int; xkb_sha256:str

def xkb_sha(text:str)->str:return hashlib.sha256(text.encode()).hexdigest()
def parse_direct_table(text:str):
    codes={m.group(1):int(m.group(2)) for m in re.finditer(r'<([^>]+)>\s*=\s*(\d+)\s*;',text)}
    symbols={}; shift_code=0; level3_code=0
    for m in re.finditer(r'key\s+<([^>]+)>\s*\{(.*?)\};',text,re.S):
        name,body=m.group(1),m.group(2); code=codes.get(name)
        if code is None:continue
        sm=re.search(r'symbols\[Group1\]\s*=\s*\[(.*?)\]',body,re.S) or re.search(r'\[(.*?)\]',body,re.S)
        if not sm:continue
        toks=[x.strip() for x in sm.group(1).split(',')][:4]
        vals=[]
        for tok in toks:
            if tok in ('','NoSymbol','VoidSymbol'): vals.append(0);continue
            ks=XK.string_to_keysym(tok)
            if ks==0 and len(tok)==1:ks=ord(tok)
            vals.append(int(ks))
        while len(vals)<4:vals.append(0)
        if vals[0]==XK.string_to_keysym('Shift_L'):shift_code=code
        if vals[0]==XK.string_to_keysym('ISO_Level3_Shift'):level3_code=code
        for level,ks in enumerate(vals):
            if not 32<=ks<=126:continue
            st=Stroke(code,level in (1,3),level in (2,3),level)
            rank=(int(st.level3)+int(st.shift),int(st.level3),int(st.shift),code,level)
            old=symbols.get(ks)
            if old is None or rank<old[0]:symbols[ks]=(rank,st)
    return symbols,shift_code,level3_code,codes

def prepare(text:str,xkb_text:str)->Plan:
    if type(text) is not str or len(text)>16384:raise Rejected('INVALID_TEXT')
    table,shift,level3,_=parse_direct_table(xkb_text); strokes=[]
    for ch in text:
        if not 32<=ord(ch)<=126:raise Rejected('TEXT_OUTSIDE_PRINTABLE_ASCII')
        item=table.get(ord(ch))
        if item is None:raise Rejected('TEXT_NOT_DIRECTLY_REPRESENTABLE')
        st=item[1]
        if st.shift and not shift:raise Rejected('SHIFT_UNAVAILABLE')
        if st.level3 and not level3:raise Rejected('LEVEL3_UNAVAILABLE')
        strokes.append(st)
    return Plan(text,tuple(strokes),shift,level3,xkb_sha(xkb_text))
def keyboard_mapping(d):
    i=d.display.info;return [list(r) for r in d.get_keyboard_mapping(i.min_keycode,i.max_keycode-i.min_keycode+1)]
def core_hash(d):return hashlib.sha256(json.dumps(keyboard_mapping(d),separators=(',',':')).encode()).hexdigest()
def modifier_mapping(d):
    try:return [[int(v) for v in row] for row in d.get_modifier_mapping()]
    except TypeError:
        m=d.get_modifier_mapping();k=getattr(m,'keycodes_per_modifier',0);f=list(getattr(m,'keycodes',[]));return [f[i*k:(i+1)*k] for i in range(8)]
def modifier_hash(d):return hashlib.sha256(json.dumps(modifier_mapping(d),separators=(',',':')).encode()).hexdigest()
def physical_state(d):
    bits=d.query_keymap();return {'keys':[k for k in range(8,256) if bits[k//8]&(1<<(k%8))],'mask':int(d.screen().root.query_pointer().mask)}
def deliver(backend,plan:Plan,*,target:int,current_xkb_text:str,expected_core_hash:str,expected_modifier_hash:str,expires_ns:int,pacing_s=.002):
    start=backend.emissions;receipt={'accepted':False,'error':None,'emissions':0,'preflight_rejected':False,'interrupted':False};owned=set()
    def send(code,down):
        if down:owned.add(code)
        xtest.fake_input(backend.d,X.KeyPress if down else X.KeyRelease,code);backend.emissions+=1;backend.d.sync()
        if not down:owned.discard(code)
    try:
        if time.monotonic_ns()>=expires_ns:raise Rejected('LEASE_EXPIRED')
        if xkb_sha(current_xkb_text)!=plan.xkb_sha256:raise Rejected('XKB_CHANGED')
        if core_hash(backend.d)!=expected_core_hash:raise Rejected('CORE_MAP_CHANGED')
        if modifier_hash(backend.d)!=expected_modifier_hash:raise Rejected('MODIFIER_MAP_CHANGED')
        mods=modifier_mapping(backend.d)
        if any(st.shift for st in plan.strokes) and plan.shift_code not in mods[0]:raise Rejected('SHIFT_MODIFIER_UNAVAILABLE')
        if any(st.level3 for st in plan.strokes) and plan.level3_code not in mods[7]:raise Rejected('LEVEL3_MODIFIER_UNAVAILABLE')
        state=physical_state(backend.d)
        if state['keys'] or state['mask']:raise Rejected('NON_NEUTRAL_INPUT')
        if getattr(backend.d.get_input_focus().focus,'id',None)!=target:raise Rejected('FOCUS_MISMATCH')
        receipt.update(accepted=True,strokes=[st.__dict__ for st in plan.strokes],shift_code=plan.shift_code,level3_code=plan.level3_code,xkb_sha256=plan.xkb_sha256,core_hash=expected_core_hash,modifier_hash=expected_modifier_hash)
        for st in plan.strokes:
            if time.monotonic_ns()>=expires_ns:raise Rejected('LEASE_EXPIRED_DURING_EXECUTION')
            if getattr(backend.d.get_input_focus().focus,'id',None)!=target:raise Rejected('FOCUS_CHANGED_DURING_EXECUTION')
            if st.level3:send(plan.level3_code,True)
            if st.shift:send(plan.shift_code,True)
            send(st.code,True);send(st.code,False)
            if st.shift:send(plan.shift_code,False)
            if st.level3:send(plan.level3_code,False)
            time.sleep(pacing_s)
    except Rejected as exc:
        receipt['error']=str(exc);receipt['interrupted']=receipt['accepted']
    finally:
        for code in sorted(owned):send(code,False)
        receipt['emissions']=backend.emissions-start;st=physical_state(backend.d);receipt['physical_after']=st;receipt['release_verified']=not st['keys'] and not st['mask']
    return receipt
