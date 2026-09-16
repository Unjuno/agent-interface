from __future__ import annotations
import os,re,subprocess
from pathlib import Path
from Xlib import XK
def resolve_xkb(display_name,xauthority,layout,variant,out_dir):
    env=os.environ.copy();env['DISPLAY']=display_name;env['XAUTHORITY']=xauthority
    cmd=['setxkbmap','-layout',layout]+((['-variant',variant]) if variant else [])+['-print']
    src=subprocess.run(cmd,env=env,check=True,text=True,capture_output=True).stdout
    source=out_dir/'layout.src.xkb'; resolved=out_dir/'layout.resolved.xkb'; source.write_text(src)
    subprocess.run(['xkbcomp','-xkb','-w','0',str(source),str(resolved)],check=True,text=True,capture_output=True)
    return resolved.read_text()
def project_group1_two_levels(xkb_text,first_code,current_mapping):
    codes={m.group(1):int(m.group(2)) for m in re.finditer(r'<([^>]+)>\s*=\s*(\d+)\s*;',xkb_text)}
    rows=[(list(row[:2])+[0,0])[:2] for row in current_mapping];matched=0
    for m in re.finditer(r'key\s+<([^>]+)>\s*\{(.*?)\};',xkb_text,re.S):
        name,body=m.group(1),m.group(2); sm=re.search(r'symbols\[Group1\]\s*=\s*\[(.*?)\]',body,re.S) or re.search(r'\[(.*?)\]',body,re.S); code=codes.get(name)
        if not sm or code is None or not(first_code<=code<first_code+len(rows)): continue
        vals=[]
        for token in [x.strip() for x in sm.group(1).split(',')][:2]:
            if token in ('','NoSymbol','VoidSymbol'): vals.append(0);continue
            keysym=XK.string_to_keysym(token)
            if keysym==0 and len(token)==1: keysym=ord(token)
            vals.append(int(keysym))
        while len(vals)<2: vals.append(0)
        rows[code-first_code]=vals; matched+=1
    return rows,matched
