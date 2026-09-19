from pathlib import Path
import json,subprocess,os,hashlib
r=Path('/home/taka/agent-interface-bench-feasibility'); dest=Path('/mnt/c/Users/junny/Documents/New project/agent-interface/research/benchmark_discovery')
assets=[]
for p in sorted((r/'packages').glob('*.deb')):
 package=subprocess.check_output(['dpkg-deb','-f',str(p),'Package'],text=True).strip();version=subprocess.check_output(['dpkg-deb','-f',str(p),'Version'],text=True).strip()
 s=subprocess.check_output(['apt-cache','show',package+'='+version],text=True)
 d=dict(l.split(': ',1) for l in s.splitlines() if ': ' in l and not l.startswith(' ')); h=hashlib.sha256(p.read_bytes()).hexdigest();assert h==d['SHA256']
 assets.append({'path':p.relative_to(r).as_posix(),'package':package,'version':version,'url':'http://archive.ubuntu.com/ubuntu/'+d['Filename'],'sha256':h,'bytes':p.stat().st_size})
for file,meta in [('Mindustry-v160.2-complete.jar','mindustry-download.json'),('luanti-5.17.0.deb','luanti-download.json')]:
 p=r/file;d=json.loads((r/meta).read_text());assets.append({'path':file,'url':d['url'],'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size})
(dest/'assets.json').write_text(json.dumps({'scope':'Actual user-local downloaded artifacts; existing system dependencies not included','assets':assets},indent=2)+'\n')
env={'cpu_count':os.cpu_count(),'cpu_model':next(l.split(':',1)[1].strip() for l in Path('/proc/cpuinfo').read_text().splitlines() if l.startswith('model name')),'memory':Path('/proc/meminfo').read_text().splitlines()[:3],'system_packages':subprocess.check_output(['dpkg-query','-W','xvfb','openbox','libgl1-mesa-dri','libglx-mesa0','python3-pil','python3-xlib','python3-numpy','python3-openpyxl'],text=True),'collected':'post-study environment inventory; not synchronized resource telemetry'}
(dest/'environment.json').write_text(json.dumps(env,indent=2)+'\n');print(len(assets),'assets',sum(a['bytes'] for a in assets))
