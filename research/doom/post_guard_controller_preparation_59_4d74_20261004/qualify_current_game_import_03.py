from pathlib import Path
import sys,json,hashlib,importlib,shutil,traceback
root=Path('/study/current-game-source-04')
sys.path.insert(0,str(root))
for name in ['real_apps_v1','observation_tiles','observation_gating','live_control','doom']:
 sys.path.insert(0,str(root/'research'/name))
r={'scope':'import qualification only; no Session/DoomGame/model/input instantiated','imports':{},'executables':{n:shutil.which(n) for n in ['Xvfb','openbox','wmctrl','xdotool']}}
for name in ['gui_suite','session_map01_v12','map01_overlap_controller_v39']:
 try:
  m=importlib.import_module(name);r['imports'][name]={'ok':True,'file':m.__file__}
 except Exception:r['imports'][name]={'ok':False,'traceback':traceback.format_exc()}
import vizdoom
wad=Path(vizdoom.__file__).parent/'freedoom2.wad'
r['wad']={'path':str(wad),'sha256':hashlib.sha256(wad.read_bytes()).hexdigest()}
Path('/out/RESULT.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r));sys.exit(0 if all(x['ok'] for x in r['imports'].values()) else 1)
