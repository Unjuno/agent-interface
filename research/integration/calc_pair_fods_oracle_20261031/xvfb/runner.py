import subprocess,time,os,json
from pathlib import Path
log=Path('/out/xvfb.log').open('wb');x=subprocess.Popen(['Xvfb',':152','-screen','0','1280x800x24','-nolisten','tcp','-ac'],stdout=log,stderr=subprocess.STDOUT)
try:
 for _ in range(100):
  if Path('/tmp/.X11-unix/X152').exists():break
  if x.poll() is not None:raise RuntimeError('Xvfb exited')
  time.sleep(.05)
 else:raise RuntimeError('Xvfb not ready')
 env=dict(os.environ,DISPLAY=':152',SAL_USE_VCLPLUGIN='gen',HOME='/tmp')
 r=subprocess.run(['libreoffice','-env:UserInstallation=file:///tmp/pair-profile','--headless','--convert-to','fods','--outdir','/out','/in/input.fods'],env=env,capture_output=True,timeout=25)
 Path('/out/lo.stdout').write_bytes(r.stdout);Path('/out/lo.stderr').write_bytes(r.stderr)
 out=Path('/out/input.fods');Path('/out/receipt.json').write_text(json.dumps({'lo_exit':r.returncode,'output_exists':out.exists()})+'\n')
 raise SystemExit(0 if r.returncode==0 and out.exists() else 1)
finally:
 x.terminate()
 try:x.wait(timeout=3)
 except subprocess.TimeoutExpired:x.kill();x.wait(timeout=3)
 log.close()
