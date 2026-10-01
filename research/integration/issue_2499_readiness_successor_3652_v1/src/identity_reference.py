import json,os,subprocess,tempfile,time,signal
from pathlib import Path
def run(a,e): return subprocess.run(a,env=e,text=True,capture_output=True,timeout=20,check=False)
def prop(e,w): return run(["xprop","-id",w,"_NET_WM_PID","WM_CLASS","WM_NAME"],e).stdout
def main():
 r=Path(tempfile.mkdtemp(prefix='xauth-2699-v4-')); d=':158'; a=r/'Xauthority'; e=os.environ.copy(); e.update(DISPLAY=d,XAUTHORITY=str(a),HOME=str(r/'home'),XDG_CONFIG_HOME=str(r/'config'),XDG_CACHE_HOME=str(r/'cache'),XDG_RUNTIME_DIR=str(r/'runtime'),SAL_USE_VCLPLUGIN='gen',GDK_BACKEND='x11')
 for n in ('home','config','cache','runtime'): (r/n).mkdir(mode=0o700)
 a.touch(mode=0o600); run(['xauth','-f',str(a),'add',d,'.','0123456789abcdef0123456789abcdef'],e); x=subprocess.Popen(['Xvfb',d,'-screen','0','1600x1000x24','-auth',str(a)],env=e,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL); ps=[]; out={'display':d,'apps':{},'input_operations':0,'model_calls':0,'network_calls':0,'filters':{'inkscape':'WM_NAME contains Inkscape','calc':'WM_NAME contains LibreOffice Calc','chromium':'WM_CLASS contains Chromium'}}
 try:
  time.sleep(.7); cmds={'inkscape':['inkscape'],'calc':['libreoffice','--norestore','--nolockcheck',f'-env:UserInstallation=file://{r/"lo-profile"}','--calc'],'chromium':['chromium','--no-sandbox','--disable-gpu','--no-first-run','--no-default-browser-check','--user-data-dir='+str(r/'chrome'),'about:blank']}; needles={'inkscape':'WM_NAME(STRING) = "Inkscape ','calc':'LibreOffice Calc','chromium':'Chromium'}
  for n,c in cmds.items():
   p=subprocess.Popen(c,env=e,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL); ps.append(p); time.sleep(3); ws=run(['xdotool','search','--onlyvisible','--name','.*'],e).stdout.split(); allp=[{'window':w,'raw':prop(e,w)} for w in ws]; hits=[q for q in allp if needles[n].lower() in q['raw'].lower()]; out['apps'][n]={'all_candidates':allp,'selected':hits,'auxiliary':[q for q in allp if q not in hits],'disposition':'accepted' if len(hits)==1 else 'refused_ambiguous_or_missing'}
  ok=all(v['disposition']=='accepted' for v in out['apps'].values()); out['decision']='PASS_XAUTH_COOKIE_IDENTITY_FILTERED' if ok else 'FAIL_XAUTH_COOKIE_IDENTITY_FILTERED'; print(json.dumps(out,sort_keys=True)); raise SystemExit(0 if ok else 1)
 finally:
  for p in ps:
   if p.poll() is None:p.terminate()
  if x.poll() is None:x.terminate()
if __name__=='__main__': main()
