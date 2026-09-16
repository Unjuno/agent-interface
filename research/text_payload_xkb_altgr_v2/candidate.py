"""Whole-payload direct printable-ASCII lowering with one Mode_switch path for levels 2/3."""
from __future__ import annotations
from dataclasses import dataclass
import hashlib,json,time
from Xlib import X, XK
from Xlib.ext import xtest
SHIFT_L=XK.string_to_keysym('Shift_L'); MODE_SWITCH=XK.string_to_keysym('Mode_switch')
class Rejected(ValueError): pass
@dataclass(frozen=True)
class Stroke:
    code:int; shift:bool; mode_switch:bool; level:int
@dataclass(frozen=True)
class Plan:
    text:str; strokes:tuple[Stroke,...]; shift_code:int; mode_code:int; map_hash:str
def fingerprint(mapping): return hashlib.sha256(json.dumps(mapping,separators=(',',':')).encode()).hexdigest()
def prepare(text,mapping,first_code=8):
    if type(text) is not str or len(text)>16384: raise Rejected('INVALID_TEXT')
    if type(mapping) is not list or not mapping: raise Rejected('INVALID_KEYMAP')
    symbols={}; shift_code=0; mode_code=0
    for off,levels in enumerate(mapping):
        if not isinstance(levels,list) or len(levels)<4 or any(type(x) is not int or x<0 for x in levels): raise Rejected('INVALID_KEYMAP')
        code=first_code+off
        if levels[0]==SHIFT_L: shift_code=code
        if levels[0]==MODE_SWITCH: mode_code=code
        for level in range(4):
            symbol=levels[level]
            if not 32<=symbol<=126: continue
            cand=Stroke(code,level in (1,3),level in (2,3),level)
            rank=(int(cand.mode_switch)+int(cand.shift),int(cand.mode_switch),int(cand.shift),cand.code,cand.level)
            old=symbols.get(symbol)
            if old is None or rank<old[0]: symbols[symbol]=(rank,cand)
    strokes=[]
    for ch in text:
        if not 32<=ord(ch)<=126: raise Rejected('TEXT_OUTSIDE_PRINTABLE_ASCII')
        item=symbols.get(ord(ch))
        if item is None: raise Rejected('TEXT_NOT_DIRECTLY_REPRESENTABLE')
        st=item[1]
        if st.shift and not shift_code: raise Rejected('SHIFT_UNAVAILABLE')
        if st.mode_switch and not mode_code: raise Rejected('MODE_SWITCH_UNAVAILABLE')
        strokes.append(st)
    return Plan(text,tuple(strokes),shift_code,mode_code,fingerprint(mapping))
def keyboard_mapping(d):
    info=d.display.info; return [list(row) for row in d.get_keyboard_mapping(info.min_keycode,info.max_keycode-info.min_keycode+1)]
def modifier_mapping(d): return [[int(v) for v in row] for row in d.get_modifier_mapping()]
def modifier_fingerprint(mods): return hashlib.sha256(json.dumps(mods,separators=(',',':')).encode()).hexdigest()
def physical_state(d):
    bits=d.query_keymap(); return {'keys':[k for k in range(8,256) if bits[k//8]&(1<<(k%8))],'mask':int(d.screen().root.query_pointer().mask)}
def deliver(backend,text,*,target,observation,current_observation,revision,current_revision,expires_ns,pacing_s=.006):
    start=backend.emissions; receipt={'accepted':False,'error':None,'emissions':0,'preflight_rejected':True,'interrupted':False}; owned=set()
    def send(code,down):
        if down: owned.add(code)
        xtest.fake_input(backend.d,X.KeyPress if down else X.KeyRelease,code); backend.emissions+=1; backend.d.sync()
        if not down: owned.discard(code)
    try:
        vals=(target,observation,current_observation,revision,current_revision,expires_ns)
        if any(type(x) is not int or x<0 for x in vals) or target==0: raise Rejected('INVALID_CONTEXT')
        if time.monotonic_ns()>=expires_ns: raise Rejected('LEASE_EXPIRED')
        if observation!=current_observation: raise Rejected('STALE_OBSERVATION')
        if revision!=current_revision: raise Rejected('STALE_BINDING')
        mapping=keyboard_mapping(backend.d); plan=prepare(text,mapping,backend.d.display.info.min_keycode)
        mods=modifier_mapping(backend.d); mod_hash=modifier_fingerprint(mods)
        if any(st.shift for st in plan.strokes) and plan.shift_code not in mods[0]: raise Rejected('SHIFT_MODIFIER_UNAVAILABLE')
        if any(st.mode_switch for st in plan.strokes) and plan.mode_code not in mods[7]: raise Rejected('MODE_SWITCH_MODIFIER_UNAVAILABLE')
        state=physical_state(backend.d)
        if state['keys'] or state['mask']: raise Rejected('NON_NEUTRAL_INPUT')
        if getattr(backend.d.get_input_focus().focus,'id',None)!=target: raise Rejected('FOCUS_MISMATCH')
        if fingerprint(keyboard_mapping(backend.d))!=plan.map_hash: raise Rejected('KEYMAP_CHANGED')
        if modifier_fingerprint(modifier_mapping(backend.d))!=mod_hash: raise Rejected('MODIFIER_MAP_CHANGED')
        if time.monotonic_ns()>=expires_ns: raise Rejected('LEASE_EXPIRED')
        receipt.update(accepted=True,preflight_rejected=False,map_hash=plan.map_hash,modifier_hash=mod_hash,strokes=[st.__dict__ for st in plan.strokes],mode_code=plan.mode_code,shift_code=plan.shift_code)
        for st in plan.strokes:
            if time.monotonic_ns()>=expires_ns: raise Rejected('LEASE_EXPIRED_DURING_EXECUTION')
            if getattr(backend.d.get_input_focus().focus,'id',None)!=target: raise Rejected('FOCUS_CHANGED_DURING_EXECUTION')
            if st.mode_switch: send(plan.mode_code,True)
            if st.shift: send(plan.shift_code,True)
            send(st.code,True); send(st.code,False)
            if st.shift: send(plan.shift_code,False)
            if st.mode_switch: send(plan.mode_code,False)
            time.sleep(pacing_s)
    except Rejected as exc:
        receipt['error']=str(exc); receipt['interrupted']=receipt['accepted']
    finally:
        for code in sorted(owned): send(code,False)
        receipt['emissions']=backend.emissions-start; state=physical_state(backend.d); receipt['physical_after']=state; receipt['release_verified']=not state['keys'] and not state['mask']
    return receipt
