"""Explicit WSLc entry adapter. Original frozen controller remains unchanged.
Requires owned output mount, host cwd, transport command and qualified assets.
No model/game starts occur on import; main is the separately authorized entry.
"""
from pathlib import Path, PureWindowsPath
import os,sys,json,hashlib
SOURCE=Path(os.environ.get('GAME_SOURCE','/study/current-game-source-05')).resolve()
sys.path.insert(0,str(SOURCE))
for name in ['real_apps_v1','observation_tiles','observation_gating','live_control','doom']:
 sys.path.insert(0,str(SOURCE/'research'/name))
import map01_overlap_controller_v39 as controller

def host_path(path):
 p=Path(path).resolve()
 if p==controller.REPO.resolve():
  return os.environ['HOST_EMPTY_CWD']
 owned=Path(os.environ['GUEST_OUTPUT_ROOT']).resolve()
 relative=p.relative_to(owned)
 if not p.is_file():raise FileNotFoundError(p)
 digest=hashlib.sha256(p.read_bytes()).hexdigest()
 host=str(PureWindowsPath(os.environ['HOST_OUTPUT_ROOT']).joinpath(*relative.parts))
 receipt={'guest_path':str(p),'relative_path':relative.as_posix(),'host_path':host,'sha256':digest,'bytes':p.stat().st_size,'scope':'guest-side path custody; host must independently verify before forwarding'}
 with (owned/'image-path-receipts.jsonl').open('a') as f:f.write(json.dumps(receipt)+'\n')
 return host

def install():
 command=json.loads(os.environ['RELAY_COMMAND_JSON'])
 if not isinstance(command,list) or not command or not all(isinstance(x,str) for x in command):raise ValueError('invalid relay command')
 controller.win=host_path
 controller.app_server_command=lambda:list(command)
 controller.WAD=Path(os.environ['QUALIFIED_WAD_PATH']).resolve()
 if hashlib.sha256(controller.WAD.read_bytes()).hexdigest()!='a8772e088847032510d97ba2312406a6998f21cbab44d4ff10696faa9c0ecd4b':raise ValueError('WAD hash mismatch')
 assets=Path(os.environ['QUALIFIED_CONTROLLER_ASSETS']).resolve()
 if assets!=controller.HERE.resolve():raise ValueError('assets must be staged beside frozen controller')
 return controller

if __name__=='__main__':install().main()
