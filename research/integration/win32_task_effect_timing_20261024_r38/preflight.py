import json, hashlib, subprocess, sys, ctypes, os
from pathlib import Path
P=Path(__file__).resolve().parent
ROOT=P.parents[2]
C=json.loads((P/'conditions.json').read_text(encoding='utf-8'))
RUN=P/'run'/'phase2_task'
checks=[]
def check(name, passed, detail=None): checks.append({'name':name,'passed':bool(passed),'detail':detail})
check('native_windows', os.name=='nt' and sys.platform=='win32', {'platform':sys.platform,'python':sys.version})
head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
check('exact_source_commit',head==C['source_commit'],{'expected':C['source_commit'],'actual':head})
tracked_dirty=bool(subprocess.run(['git','diff','--quiet','HEAD','--'],cwd=ROOT).returncode or subprocess.run(['git','diff','--cached','--quiet'],cwd=ROOT).returncode)
check('tracked_tree_clean',not tracked_dirty)
for name,want in C['frozen_files'].items():
 got=hashlib.sha256((P/name).read_bytes()).hexdigest()
 check('packet_hash:'+name,got==want,{'expected':want,'actual':got})
for name,want in C['runtime_hashes'].items():
 got=hashlib.sha256((ROOT/name).read_bytes()).hexdigest()
 check('runtime_hash:'+name,got==want,{'expected':want,'actual':got})
check('fresh_run_directory',RUN.exists() and not any(RUN.iterdir()),{'entries':[p.name for p in RUN.iterdir()] if RUN.exists() else None})
try:
 import mcp
 from PIL import Image
 check('mcp_and_image_dependencies',True,{'mcp':getattr(mcp,'__file__',None),'pillow':Image.__module__})
except Exception as e: check('mcp_and_image_dependencies',False,repr(e))
class_name='AgentInterfaceWin32FixtureV1'
existing=[]
if os.name=='nt':
 user32=ctypes.WinDLL('user32',use_last_error=True)
 WNDENUMPROC=ctypes.WINFUNCTYPE(ctypes.c_bool,ctypes.c_void_p,ctypes.c_void_p)
 user32.EnumWindows.argtypes=[WNDENUMPROC,ctypes.c_void_p]
 def visit(hwnd,lparam):
  buf=ctypes.create_unicode_buffer(256)
  user32.GetClassNameW(hwnd,buf,len(buf))
  if buf.value==class_name: existing.append(int(hwnd))
  return True
 user32.EnumWindows(WNDENUMPROC(visit),None)
check('no_existing_fixture_window',not existing,existing)
result={'schema':'win32-task-effect-timing-r38-preflight-v1','attempt_id':C['attempt_id'],'checks':checks,'passed':sum(x['passed'] for x in checks),'total':len(checks),'status':'PASS' if all(x['passed'] for x in checks) else 'FAIL_OR_UNKNOWN'}
(P/'preflight.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result,indent=2))
if not all(x['passed'] for x in checks): raise SystemExit(2)

