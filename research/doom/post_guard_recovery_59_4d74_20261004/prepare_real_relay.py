from pathlib import Path
r=Path(__file__).resolve().parent
s=(r/'run_relay_construction_02.py').read_text().replace("relay-construction-02'","real-relay-construction-01'").replace("construction02'","real-construction01'")
s=s.replace("'run_relay_construction_02.py'","'run_real_relay_construction.py'").replace("'relay_container_check.py'","'real_relay_container_check.py'").replace("/study/relay_container_check.py","/study/real_relay_container_check.py")
s=s.replace("hostargs=[sys.executable,'-X','utf8',str(root/'fake_pending_server.py')]",'''cli=root.parent.parent.parent.parent.parent / 'unused'
cli=Path('C:/Users/junny/AppData/Local/OpenAI/Codex/bin/8aaf1547b825b104/codex.exe')
workspace=root/'real-empty-workspace';workspace.mkdir(exist_ok=False)
args[args.index('--mount'):args.index('--mount')]=['--env','HOST_WORKSPACE='+str(workspace)]
hostargs=[str(cli),'app-server','--stdio','--disable','plugins','--disable','remote_plugin','--disable','shell_tool','--disable','shell_snapshot','-c','project_doc_max_bytes=0']
pins['CLI_SHA256']=hashlib.sha256(cli.read_bytes()).hexdigest()''')
s=s.replace("one bounded setup construction, explicit fake peer, no provider/game/input","one actual provider transport construction, at most 2 requested turns, no game/input; interruption usage may remain unknown")
s=s.replace("['pending interrupt','completed after interrupt','fresh continuation']","['real pending interrupt','real fresh continuation']")
s=s.replace("'max_seconds':40","'max_seconds':60").replace('>40:', '>60:')
s=s.replace("'provider_calls':0,","'provider_calls':'derive requested turn/start count from retained requests',")
(r/'run_real_relay_construction.py').write_text(s)
