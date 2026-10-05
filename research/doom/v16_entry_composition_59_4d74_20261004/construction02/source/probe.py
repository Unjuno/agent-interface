import sys,json,hashlib,os
from pathlib import Path
from types import SimpleNamespace
sys.path.insert(0,'/source')
import portable_controller_entry_04 as entry
c=entry.previous.controller
old=c.session_command
try:
 entry.install()
 args=SimpleNamespace(seed=40110,load_fixture_manifest=Path('/out/fixture.json'))
 argv=c.session_command(args,Path('/out/runtime'))
 assert argv[1]=='/source/research/doom/session_map01_v16.py'
 assert c.app_server_command()==['python3','/source/controller_file_stdio_proxy.py','/out']
 import session_map01_v16
 rows={name:{'path':m.__file__,'sha256':hashlib.sha256(Path(m.__file__).read_bytes()).hexdigest()} for name,m in list(sys.modules.items()) if getattr(m,'__file__',None) and str(m.__file__).startswith('/source/')}
 result={'status':'PASS_COMPOSED_ENTRY_SELECTION_ONLY','session_argv':argv,'relay_argv':c.app_server_command(),'modules':rows,'game_instances':0,'provider_calls':0,'input_calls':0}
finally:c.session_command=old
result['session_command_restored']=c.session_command is old
Path('/out/RESULT.json').write_text(json.dumps(result,indent=2));print(json.dumps({'status':result['status'],'modules':len(rows),'restored':result['session_command_restored']}))
