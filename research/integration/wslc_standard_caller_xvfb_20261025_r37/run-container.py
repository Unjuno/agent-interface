import json,os,signal,subprocess,sys,time,traceback
from pathlib import Path
OUT=Path('/out');REPORT=OUT/'container-setup.json'
def save(stage,**items):
 row={'stage':stage,'utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),**items};REPORT.write_text(json.dumps(row,sort_keys=True,indent=2),encoding='utf-8');print(json.dumps(row,sort_keys=True),flush=True)
def stop(p):
 if p is None or p.poll() is not None:return
 p.send_signal(signal.SIGTERM)
 try:p.wait(timeout=8)
 except subprocess.TimeoutExpired:p.kill();p.wait(timeout=3)
proc=None
try:
 for path in ('/tmp/stage/bin/python3.12','/tmp/stage/bin/Xvfb','/tmp/stage/bin/xauth','/tmp/stage/bin/xkbcomp','/xkb'):
  if not Path(path).exists():raise FileNotFoundError(path)
 OUT.mkdir(parents=True,exist_ok=True)
 auth='/tmp/Xauthority';cookie=os.urandom(16).hex();Path(auth).touch(mode=0o600)
 ld='/tmp/stage/lib'
 server_env=os.environ.copy();server_env.update({'LD_LIBRARY_PATH':ld})
 xr=subprocess.run(['/tmp/stage/bin/xauth','-f',auth,'add',':88','MIT-MAGIC-COOKIE-1',cookie],env=server_env,text=True,capture_output=True,timeout=10)
 (OUT/'xauth.stdout.txt').write_text(xr.stdout,encoding='utf-8');(OUT/'xauth.stderr.txt').write_text(xr.stderr,encoding='utf-8')
 if xr.returncode:raise RuntimeError(f'xauth exit={xr.returncode}: {xr.stderr}')
 Path('/tmp/.X11-unix').mkdir(mode=0o1777,exist_ok=True);os.chmod('/tmp/.X11-unix',0o1777)
 log=open(OUT/'xvfb.log','wb');argv=['/tmp/stage/bin/Xvfb',':88','-screen','0','1024x768x24','-nolisten','tcp','-ardelay','60000','-arinterval','1000','-auth',auth,'-xkbdir','/xkb','-fp','built-ins']
 proc=subprocess.Popen(argv,stdout=log,stderr=subprocess.STDOUT,env=server_env);(OUT/'xvfb-pid.txt').write_text(str(proc.pid),encoding='ascii')
 (OUT/'xvfb-argv.json').write_text(json.dumps({'argv':argv,'pid':proc.pid},indent=2),encoding='utf-8')
 deadline=time.monotonic()+15
 while time.monotonic()<deadline and not Path('/tmp/.X11-unix/X88').exists():
  if proc.poll() is not None:raise RuntimeError(f'Xvfb exited early: {proc.returncode}')
  time.sleep(.05)
 if not Path('/tmp/.X11-unix/X88').exists():raise TimeoutError('private local X socket not created')
 app_env=os.environ.copy();app_env.update({'LD_LIBRARY_PATH':ld,'PYTHONHOME':'/tmp/stage','DISPLAY':':88','XAUTHORITY':auth,'PYTHONPATH':'/deps:/repo'})
 pre="from Xlib import display; from runtime.guarded_x11_v1.process_identity import read_linux_x11_process_identity; d=display.Display(); s=d.screen(); w=s.root.create_window(1,1,16,16,0,0,1,0,0); w.map(); d.sync(); print('local_xres_identity='+read_linux_x11_process_identity(d,w.id)); d.close()"
 check=subprocess.run(['/tmp/stage/bin/python3.12','-B','-c',pre],env=app_env,text=True,capture_output=True,timeout=20)
 (OUT/'xvfb-process-identity-preflight.txt').write_text(check.stdout,encoding='utf-8');(OUT/'xvfb-process-identity-preflight.stderr.txt').write_text(check.stderr,encoding='utf-8')
 if check.returncode:raise RuntimeError(f'Xlib/XRes local identity preflight failed: {check.stderr}')
 (OUT/'preflight-status.txt').write_text('pass\n',encoding='ascii')
 app_env.update({'AGENT_INTERFACE_XVFB_PID':str(proc.pid),'AGENT_INTERFACE_MCP_XVFB_TEST':'1','AGENT_INTERFACE_MCP_XVFB_SERVER_PAUSE_MS':'3500','AGENT_INTERFACE_MCP_XVFB_CANCEL_ACK_WITHHOLD_S':'0','AGENT_INTERFACE_MCP_XVFB_TRACE_OWNER_PROCESS_METHODS':'1','AGENT_INTERFACE_MCP_XVFB_PRESTARTED_CANCEL_SUPERVISOR':'1','AGENT_INTERFACE_MCP_XVFB_BLOCKED_RELEASE_RESULT':'/out/result.json','PYTHONDONTWRITEBYTECODE':'1'})
 (OUT/'trial-started.txt').write_text('test body starts only after local XRes identity preflight passes\n',encoding='utf-8')
 with open(OUT/'runner.stdout.txt','w',encoding='utf-8') as so,open(OUT/'runner.stderr.txt','w',encoding='utf-8') as se:
  run=subprocess.run(['/tmp/stage/bin/python3.12','-B','-m','unittest','-v','runtime.cli_v1.test_mcp_xvfb_blocked_release_integration'],env=app_env,stdout=so,stderr=se,timeout=210)
 (OUT/'test-exit-code.txt').write_text(str(run.returncode)+'\n',encoding='ascii');save('test_finished',returncode=run.returncode,result_exists=(OUT/'result.json').is_file());rc=run.returncode
except Exception as exc:
 save('pretrial_or_runner_failure',type=type(exc).__name__,error=str(exc),traceback=traceback.format_exc());rc=74
finally:
 try:stop(proc)
 except Exception as exc:save('xvfb_cleanup_failure',type=type(exc).__name__,error=str(exc))
 (OUT/'xvfb-process-absent-after-run.txt').write_text(str(proc is None or proc.poll() is not None)+'\n',encoding='ascii')
sys.exit(rc)






