"""Validate evaluator-only host report persistence; seed 2002 is construction only."""
import base64, hashlib, json, secrets, subprocess, time
from pathlib import Path
from inspection import inspect_to_file
HERE=Path(__file__).resolve().parent
OUT=HERE/'construction/smoke-07'; OUT.mkdir(parents=True,exist_ok=False)
NET='arena-isolation-v2-smoke'; EV='arena-isolation-v2-smoke-eval'; CTL='arena-isolation-v2-smoke-controller'
COOKIE=secrets.token_hex(16)
def call(args,check=True,timeout=30):
    p=subprocess.run(args,capture_output=True,text=True,timeout=timeout)
    if check and p.returncode: raise RuntimeError(f'{args}: {p.stdout}\n{p.stderr}')
    return p
for n in (EV,CTL): call(['docker','rm','-f',n],check=False)
call(['docker','network','rm',NET],check=False)
call(['docker','network','create','--internal',NET])
try:
    call(['docker','run','-d','--name',EV,'--platform','linux/amd64','--network',NET,'-e','ARENA_SEED=2002','-e',f'X11_COOKIE={COOKIE}','-e','ARENA_AUTOCLOSE=30','--read-only','--cap-drop=ALL','--security-opt=no-new-privileges','--tmpfs','/tmp:rw,noexec,nosuid,size=8m','-v',f'{OUT}:/evidence:rw','agent-arena-isolation-evaluator-v2:20260927'])
    ready=False
    for _ in range(100):
        p=call(['docker','exec','-e','XAUTHORITY=/tmp/Xauthority',EV,'xwininfo','-display',':0','-root','-tree'],check=False)
        if 'Procedural Control Arena v0' in p.stdout: ready=True; break
        time.sleep(.1)
    if not ready: raise RuntimeError('STOP: no evaluator window')
    display=f'{EV}:0'
    call(['docker','run','-d','--name',CTL,'--platform','linux/amd64','--network',NET,'-e',f'DISPLAY={display}','-e',f'X11_COOKIE={COOKIE}','--read-only','--cap-drop=ALL','--security-opt=no-new-privileges','--user=10000:10000','--tmpfs','/tmp:rw,noexec,nosuid,size=8m','agent-arena-isolation-controller-v2:20260927'])
    ctl_exit=int(call(['docker','wait',CTL]).stdout.strip())
    logs=call(['docker','logs',CTL],check=False)
    (OUT/'controller.stderr.log').write_text(logs.stderr,encoding='utf-8')
    lines=logs.stdout.splitlines()
    pl=next(x for x in lines if x.startswith('{'))
    xl=next(x for x in lines if x.startswith('XWD_BASE64:'))
    probe=json.loads(pl)
    (OUT/'controller-probe.json').write_text(json.dumps(probe,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    (OUT/'screen.xwd').write_bytes(base64.b64decode(xl.partition(':')[2],validate=True))
    controller_doc,_=inspect_to_file(CTL,OUT/'controller-inspect.json')
    for _ in range(100):
        if (OUT/'report.json').is_file() and (OUT/'report.json').stat().st_size: break
        time.sleep(.05)
    if not (OUT/'report.json').is_file(): raise RuntimeError('STOP: host evidence bind did not retain report')
    evaluator_doc,_=inspect_to_file(EV,OUT/'evaluator-inspect-before.json')
    argv=call(['docker','exec','-e','XAUTHORITY=/tmp/Xauthority',EV,'python','-c',"import pathlib;print(pathlib.Path('/proc/1/cmdline').read_bytes().replace(b'\\0',b' ').decode())"])
    (OUT/'evaluator-proc-1-cmdline.txt').write_text(argv.stdout,encoding='utf-8')
    (OUT/'network-inspect.json').write_text(call(['docker','network','inspect',NET]).stdout,encoding='utf-8')
    evlogs=call(['docker','logs',EV],check=False)
    (OUT/'evaluator.stdout.log').write_text(evlogs.stdout,encoding='utf-8')
    (OUT/'evaluator.stderr.log').write_text(evlogs.stderr,encoding='utf-8')
    report=json.loads((OUT/'report.json').read_text(encoding='utf-8'))
    network_doc=json.loads((OUT/'network-inspect.json').read_text(encoding='utf-8'))[0]
    ev_mounts=evaluator_doc.get('Mounts',[])
    ev_host=evaluator_doc.get('HostConfig',{})
    ctl_host=controller_doc.get('HostConfig',{})
    ev_cookie=next((v.partition('=')[2] for v in evaluator_doc['Config']['Env'] if v.startswith('X11_COOKIE_SHA256=')),None)
    ctl_cookie=next((v.partition('=')[2] for v in controller_doc['Config']['Env'] if v.startswith('X11_COOKIE_SHA256=')),None)
    result={'controller_exit':ctl_exit,'controller_probe':probe,'report':report,'evaluator_argv':argv.stdout.strip(),'evaluator_image_id':evaluator_doc['Image'],'controller_image_id':controller_doc['Image'],
            'network_internal':network_doc['Internal'],'evaluator_mounts':ev_mounts,'controller_mounts':controller_doc.get('Mounts',[]),'x11_cookie_sha256_match':bool(ev_cookie and ev_cookie==ctl_cookie)}
    (OUT/'CONSTRUCTION_SMOKE.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    assert ctl_exit==0 and report['episode']['seed']==2002 and report['failure_reason']=='deadline_miss'
    assert report['episode']['stages'][0]['kind']=='target'
    assert any(e['event']=='key_down' and e['detail'].get('key')=='w' for e in report['events'])
    assert any(e['event']=='key_up' and e['detail'].get('key')=='w' for e in report['events'])
    assert hashlib.sha256((OUT/'screen.xwd').read_bytes()).hexdigest()==probe['capture_sha256']
    assert probe['path_access']['/evidence/report.json'] is False
    assert '2002' not in json.dumps(probe['proc_cmdlines'])
    assert network_doc['Internal'] is True
    assert len(ev_mounts)==1 and ev_mounts[0]['Type']=='bind' and ev_mounts[0]['Destination']=='/evidence' and ev_mounts[0]['RW'] is True
    assert str(ev_mounts[0]['Source']).replace('\\','/').split('/')[-1]=='smoke-07'
    assert controller_doc.get('Mounts',[])==[] and controller_doc['Config']['User']=='10000:10000'
    assert ctl_host['ReadonlyRootfs'] is True and ctl_host['CapDrop']==['ALL'] and ctl_host['Privileged'] is False
    assert ctl_host.get('PidMode') in ('',None) and set(ctl_host.get('Tmpfs',{}))=={'/tmp'}
    assert ev_host['ReadonlyRootfs'] is True and ev_host['CapDrop']==['ALL'] and ev_host['SecurityOpt']==['no-new-privileges'] and set(ev_host.get('Tmpfs',{}))=={'/tmp'}
    assert ev_cookie and ev_cookie==ctl_cookie and not any(x.startswith('X11_COOKIE=') for x in evaluator_doc['Config']['Env']+controller_doc['Config']['Env'])
    for n in (EV,CTL):
        inspect_to_file(n,OUT/f'{n}-inspect-after.json')
    call(['docker','stop',EV],check=False)
    (OUT/'network-inspect-final.json').write_text(call(['docker','network','inspect',NET]).stdout,encoding='utf-8')
    raw={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in OUT.iterdir() if p.is_file() and p.name!='RAW_MANIFEST.json'}
    (OUT/'RAW_MANIFEST.json').write_text(json.dumps({'schema':'arena-isolation-v2-smoke-manifest-v1','files':raw},indent=2,sort_keys=True)+'\n',encoding='utf-8')
    print(json.dumps({'construction':'PASS','seed':2002,'report_retained':True,'xwd_bytes':(OUT/'screen.xwd').stat().st_size,'xwd_sha256':probe['capture_sha256']}))
finally:
    for n in (EV,CTL): call(['docker','rm','-f',n],check=False)
    call(['docker','network','rm',NET],check=False)
