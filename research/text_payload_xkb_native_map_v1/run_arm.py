from __future__ import annotations
import argparse, hashlib, json, os, re, subprocess
from pathlib import Path
from Xlib import display

def sha(data: bytes) -> str: return hashlib.sha256(data).hexdigest()
def cmd(args, **kw):
    p=subprocess.run(args, text=True, capture_output=True, **kw)
    return {'args':args,'returncode':p.returncode,'stdout':p.stdout,'stderr':p.stderr}
def dump_live() -> dict:
    d=display.Display(); info=d.display.info
    mapping=[list(r) for r in d.get_keyboard_mapping(info.min_keycode, info.max_keycode-info.min_keycode+1)]
    mods=d.get_modifier_mapping()
    try: modrows=[list(r) for r in mods]
    except TypeError:
        kpm=getattr(mods,'keycodes_per_modifier',0); flat=list(getattr(mods,'keycodes',[])); modrows=[flat[i*kpm:(i+1)*kpm] for i in range(8)]
    obj={'min_keycode':info.min_keycode,'max_keycode':info.max_keycode,'mapping':mapping,'modifier_mapping':modrows}
    raw=json.dumps(obj,separators=(',',':'),sort_keys=True).encode(); obj['sha256']=sha(raw); d.close(); return obj
def parse_codes(text: str) -> dict[str,int]: return {m.group(1):int(m.group(2)) for m in re.finditer(r'<([^>]+)>\s*=\s*(\d+)\s*;',text)}
def parse_syms(text: str, name: str) -> list[str]:
    m=re.search(r'key\s+<'+re.escape(name)+r'>\s*\{(.*?)\};',text,re.S)
    if not m: return []
    b=m.group(1); s=re.search(r'symbols\[Group1\]\s*=\s*\[(.*?)\]',b,re.S) or re.search(r'\[(.*?)\]',b,re.S)
    return [x.strip() for x in s.group(1).split(',')] if s else []
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--out',type=Path,required=True); ap.add_argument('--plan',type=Path,required=True); a=ap.parse_args()
    a.out.mkdir(parents=True,exist_ok=False); plan=json.loads(a.plan.read_text())
    if not os.environ.get('DISPLAY') or not os.environ.get('XAUTHORITY'): raise RuntimeError('fresh authenticated xvfb-run required')
    ext=cmd(['xdpyinfo','-queryExtensions']); xkeyboard='XKEYBOARD' in ext['stdout'].upper()
    bq=cmd(['setxkbmap','-query']); baseline=dump_live(); bd=cmd(['xkbcomp','-xkb',os.environ['DISPLAY'],'-'])
    (a.out/'baseline.server.xkb').write_text(bd['stdout']); (a.out/'baseline.query.txt').write_text(bq['stdout'])
    pr=cmd(['setxkbmap','-layout',plan['layout'],'-print']); (a.out/'de.print.xkb').write_text(pr['stdout'])
    rr=cmd(['xkbcomp','-xkb','-w','0',str(a.out/'de.print.xkb'),str(a.out/'de.resolved.xkb')]); resolved=(a.out/'de.resolved.xkb').read_bytes(); resolved_text=resolved.decode(); resolved_hash=sha(resolved)
    codes=parse_codes(resolved_text); ad01_syms=parse_syms(resolved_text,'AD01'); ralt_syms=parse_syms(resolved_text,'RALT')
    apply=cmd(['xkbcomp','-w','0',str(a.out/'de.resolved.xkb'),os.environ['DISPLAY']]);
    aq=cmd(['setxkbmap','-query']); after=dump_live(); ad=cmd(['xkbcomp','-xkb',os.environ['DISPLAY'],'-'])
    (a.out/'after.server.xkb').write_text(ad['stdout']); (a.out/'after.query.txt').write_text(aq['stdout'])
    ad01_code=codes.get('AD01'); row=None
    if ad01_code is not None and after['min_keycode']<=ad01_code<=after['max_keycode']: row=after['mapping'][ad01_code-after['min_keycode']]
    native_at=bool(row and len(row)>2 and row[2]==64)
    integrity=(xkeyboard and resolved_hash==plan['resolved_sha256'] and rr['returncode']==0 and ad01_syms[:4]==['q','Q','at','Greek_OMEGA'] and ralt_syms and ralt_syms[0]=='ISO_Level3_Shift')
    server_changed=sha(bd['stdout'].encode())!=sha(ad['stdout'].encode()); live_changed=baseline['sha256']!=after['sha256']
    if not integrity or apply['returncode']!=0: decision='FAIL_INTEGRITY'
    elif server_changed and live_changed and native_at: decision='PASS_NATIVE_XKB_MAP_ROUNDTRIP_SCOPED'
    else: decision='SETUP_BLOCKED_NATIVE_XKB_APPLY'
    result={'schema':'agent-interface/xkb-native-map-arm-v1','decision':decision,'display':os.environ['DISPLAY'],'xkeyboard_present':xkeyboard,
      'resolved_sha256':resolved_hash,'resolved_expected':plan['resolved_sha256'],'ad01_code':ad01_code,'resolved_ad01_symbols':ad01_syms,'resolved_ralt_symbols':ralt_syms,
      'baseline_live_sha256':baseline['sha256'],'after_live_sha256':after['sha256'],'live_core_map_changed':live_changed,'server_dump_changed':server_changed,
      'baseline_server_sha256':sha(bd['stdout'].encode()),'after_server_sha256':sha(ad['stdout'].encode()),'baseline_query':bq['stdout'],'after_query':aq['stdout'],
      'apply':apply,'resolve_compile':rr,'live_ad01_row':row,'live_ad01_level3_at':native_at,'baseline_modifier_mapping':baseline['modifier_mapping'],'after_modifier_mapping':after['modifier_mapping'],
      'input_operations':0,'integrity':integrity}
    (a.out/'result.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n'); print(json.dumps({'decision':decision,'server_changed':server_changed,'live_changed':live_changed,'native_at':native_at}))
    return 0 if decision!='FAIL_INTEGRITY' else 2
if __name__=='__main__': raise SystemExit(main())
