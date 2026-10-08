from __future__ import annotations
import os,re,subprocess
from pathlib import Path
from Xlib import XK
MODE_SWITCH=XK.string_to_keysym('Mode_switch')
def resolve_xkb(display_name,xauthority,layout,variant,out_dir):
    env=os.environ.copy(); env['DISPLAY']=display_name; env['XAUTHORITY']=xauthority
    cmd=['setxkbmap','-layout',layout]
    if variant: cmd+=['-variant',variant]
    cmd+=['-print']; src=subprocess.run(cmd,env=env,check=True,text=True,capture_output=True).stdout
    source=out_dir/'layout.src.xkb'; resolved=out_dir/'layout.resolved.xkb'; source.write_text(src,encoding='utf-8')
    subprocess.run(['xkbcomp','-xkb','-w','0',str(source),str(resolved)],check=True,text=True,capture_output=True)
    return resolved.read_text(encoding='utf-8')
def parse_codes(xkb_text): return {m.group(1):int(m.group(2)) for m in re.finditer(r'<([^>]+)>\s*=\s*(\d+)\s*;',xkb_text)}
def project_group1_four_levels(xkb_text,first_code,current_mapping):
    codes=parse_codes(xkb_text); width=max(4,max(len(r) for r in current_mapping)); rows=[[0]*width for _ in current_mapping]; matched=0
    for m in re.finditer(r'key\s+<([^>]+)>\s*\{(.*?)\};',xkb_text,re.S):
        name,body=m.group(1),m.group(2); sm=re.search(r'symbols\[Group1\]\s*=\s*\[(.*?)\]',body,re.S)
        if sm is None: sm=re.search(r'\[(.*?)\]',body,re.S)
        code=codes.get(name)
        if not sm or code is None or not(first_code<=code<first_code+len(rows)): continue
        vals=[]
        for token in [x.strip() for x in sm.group(1).split(',')][:4]:
            if token in ('','NoSymbol','VoidSymbol'): vals.append(0); continue
            ks=XK.string_to_keysym(token)
            if ks==0 and len(token)==1: ks=ord(token)
            vals.append(int(ks))
        while len(vals)<4: vals.append(0)
        rows[code-first_code][:4]=vals; matched+=1
    ralt=codes.get('RALT')
    if ralt is None or not(first_code<=ralt<first_code+len(rows)): raise RuntimeError('RALT keycode unavailable')
    rows[ralt-first_code][:4]=[MODE_SWITCH,MODE_SWITCH,0,0]
    return rows,matched,ralt
def bind_mode_switch_mod5(d,ralt):
    mods=[list(x) for x in d.get_modifier_mapping()]
    for row in mods:
        while ralt in row: row.remove(ralt)
    mods[7].append(ralt)
    status=d.set_modifier_mapping(mods); d.sync()
    if status!=0: raise RuntimeError(f'SetModifierMapping status {status}')
    return [[int(v) for v in row] for row in mods]
