from __future__ import annotations
import hashlib, json, os, subprocess, sys
from pathlib import Path
from Xlib import display

EXPECTED_DE_SHA='3d3133ea34205324545de76b99d9f65e450d45451a705443336f71a5ac6a7ffd'
DIRECT={'at','bracketleft','bracketright','backslash','braceleft','braceright','bar','asciitilde'}

def sha(b: bytes) -> str: return hashlib.sha256(b).hexdigest()
def run(cmd, env, *, input_text=None):
    p=subprocess.run(cmd,env=env,input=input_text,text=True,capture_output=True)
    return {'cmd':cmd,'returncode':p.returncode,'stdout':p.stdout,'stderr':p.stderr}
def mapping(d):
    info=d.display.info
    return [list(r) for r in d.get_keyboard_mapping(info.min_keycode,info.max_keycode-info.min_keycode+1)]
def modifiers(d): return [list(x) for x in d.get_modifier_mapping()]
def fp(obj): return hashlib.sha256(json.dumps(obj,separators=(',',':')).encode()).hexdigest()

def main(out: Path):
    out.mkdir(parents=True,exist_ok=False)
    env=os.environ.copy(); disp=env['DISPLAY']; auth=env.get('XAUTHORITY','')
    d=display.Display(disp)
    ext=bool(d.query_extension('XKEYBOARD').present)
    before_map=mapping(d); before_mod=modifiers(d)
    baseline=run(['xkbcomp','-xkb',disp,'-'],env)
    (out/'baseline.server.xkb').write_text(baseline['stdout'])
    source=run(['setxkbmap','-layout','de','-print'],env)
    (out/'de.src.xkb').write_text(source['stdout'])
    resolved=run(['xkbcomp','-xkb','-w','0','-','-'],env,input_text=source['stdout'])
    (out/'de.resolved.xkb').write_text(resolved['stdout'])
    de_sha=sha(resolved['stdout'].encode())
    apply=run(['setxkbmap','-layout','de'],env)
    after=run(['xkbcomp','-xkb',disp,'-'],env)
    (out/'after.server.xkb').write_text(after['stdout'])
    after_map=mapping(d); after_mod=modifiers(d); d.close()
    report={
      'schema':'agent-interface/xkb-native-roundtrip-v1',
      'xkeyboard_present':ext,
      'baseline_dump_returncode':baseline['returncode'],
      'resolved_source_returncode':source['returncode'],
      'resolved_compile_returncode':resolved['returncode'],
      'apply_returncode':apply['returncode'],
      'apply_stdout':apply['stdout'],'apply_stderr':apply['stderr'],
      'after_dump_returncode':after['returncode'],
      'de_resolved_sha256':de_sha,
      'expected_de_sha256':EXPECTED_DE_SHA,
      'baseline_server_sha256':sha(baseline['stdout'].encode()),
      'after_server_sha256':sha(after['stdout'].encode()),
      'core_map_before_sha256':fp(before_map),'core_map_after_sha256':fp(after_map),
      'modifier_before_sha256':fp(before_mod),'modifier_after_sha256':fp(after_mod),
      'server_changed':baseline['stdout']!=after['stdout'],
      'core_map_changed':before_map!=after_map,
      'modifier_changed':before_mod!=after_mod,
      'baseline_map':before_map,'after_map':after_map,
      'baseline_modifiers':before_mod,'after_modifiers':after_mod,
    }
    (out/'report.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    print(json.dumps({k:report[k] for k in ['xkeyboard_present','apply_returncode','de_resolved_sha256','server_changed','core_map_changed','modifier_changed']},indent=2))

if __name__=='__main__': main(Path(sys.argv[1]))
