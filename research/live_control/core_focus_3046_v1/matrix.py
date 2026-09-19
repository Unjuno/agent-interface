import json, os, subprocess, tempfile, time
from pathlib import Path

def run(argv, env, timeout=4):
    try:
        q=subprocess.run(argv,env=env,text=True,capture_output=True,timeout=timeout)
        return {'rc':q.returncode,'out':q.stdout.strip(),'err':q.stderr.strip()}
    except subprocess.TimeoutExpired as e:
        return {'rc':124,'out':str(e.stdout or ''),'err':str(e.stderr or 'timeout')}
def one(display, configured):
    root=Path(tempfile.mkdtemp(prefix='lo3046-')); auth=root/'Xauthority'; auth.touch(mode=0o600)
    env=os.environ.copy(); env.update(DISPLAY=display,XAUTHORITY=str(auth))
    if configured:
        cfg=root/'openbox'; cfg.mkdir()
        (cfg/'rc.xml').write_text('''<?xml version="1.0"?><openbox_config><focus><focusNew>yes</focusNew><focusLast>yes</focusLast><followMouse>no</followMouse><focusDelay>0</focusDelay><raiseOnFocus>yes</raiseOnFocus></focus><desktops><number>1</number></desktops></openbox_config>''')
        env['XDG_CONFIG_HOME']=str(root)
    procs=[]
    try:
        xv=subprocess.Popen(['Xvfb',display,'-screen','0','1600x1000x24','-auth',str(auth)],env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL); procs.append(xv); time.sleep(.5)
        wm_cmd=['fluxbox'] if os.environ.get('LO3046_WM') == 'fluxbox' else ['openbox','--sm-disable']
        wm=subprocess.Popen(wm_cmd,env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL); procs.append(wm); time.sleep(.8)
        lo=subprocess.Popen(['libreoffice','--norestore','--nodefault','--nolockcheck','--calc'],env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL); procs.append(lo); time.sleep(2.5)
        wins=run(['xdotool','search','--onlyvisible','--name','.*'],env)
        ids=[x for x in wins['out'].splitlines() if x]
        rows=[]
        for wid in ids:
            rows.append({'window':wid,'name':run(['xdotool','getwindowname',wid],env),'class':run(['xprop','-id',wid,'WM_CLASS'],env),'geom':run(['xdotool','getwindowgeometry',wid],env)})
        rootprops={p:run(['xprop','-root',p],env) for p in ['_NET_ACTIVE_WINDOW','_NET_SUPPORTED','_NET_SUPPORTING_WM_CHECK','_NET_NUMBER_OF_DESKTOPS']}
        active=run(['xdotool','getactivewindow'],env)
        core_before=run(['xdotool','getwindowfocus'],env)
        target=next((r['window'] for r in rows if r['name']['out']!='Openbox'),None)
        act=run(['xdotool','windowactivate','--sync',target],env) if target else None
        after=run(['xdotool','getactivewindow'],env)
        core_after=run(['xdotool','getwindowfocus'],env)
        return {'configured':configured,'windows':rows,'rootprops':rootprops,'active_before':active,'core_before':core_before,'target':target,'activate':act,'active_after':after,'core_after':core_after}
    finally:
        for p in reversed(procs):
            if p.poll() is None: p.terminate()
results=[one(':143',False),one(':144',True)]
valid=any(r['rootprops']['_NET_ACTIVE_WINDOW']['out'] and 'not found' not in r['rootprops']['_NET_ACTIVE_WINDOW']['out'] and '0x0' not in r['rootprops']['_NET_ACTIVE_WINDOW']['out'] and r['active_after']['rc']==0 for r in results)
core=any(r['core_after']['rc']==0 for r in results)
print(json.dumps({'decision':'PASS_EWMH_MATRIX' if valid else ('PASS_CORE_FOCUS_ONLY' if core else 'HOLD_NO_ACTIVE_WINDOW'),'results':results,'model_calls':0,'network_calls':0},sort_keys=True))
