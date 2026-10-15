#!/usr/bin/env python3
import ctypes, ctypes.util, hashlib, json, os, platform, subprocess, sys
from pathlib import Path
root=Path(__file__).parent
items=[]
for p in sorted((root/'inputs').glob('*.deb')):
    fields=subprocess.run(['dpkg-deb','-f',str(p),'Package','Version','Architecture'],capture_output=True,text=True,check=True).stdout.splitlines()
    items.append({'file':p.name,'package':fields[0],'version':fields[1],'architecture':fields[2],'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
(root/'inputs'/'PACKAGE_MANIFEST.json').write_text(json.dumps({'schema':'x11-package-manifest-v1','packages':items},indent=2,sort_keys=True)+'\n')
(root/'inputs'/'SHA256SUMS').write_text(''.join(x['sha256']+'  '+x['file']+'\n' for x in items))
base=Path('/home/user/x11-xtest-device-cross-client-a01-20261005')
libs={}
for logical,soname,pkg in [('X11','libX11.so.6','libx11-6'),('Xi','libXi.so.6','libxi6'),('Xtst','libXtst.so.6','libxtst6')]:
    found=ctypes.util.find_library(logical); lib=ctypes.CDLL(found or soname)
    sym=getattr(lib,'XTestFakeDeviceKeyEvent' if logical=='Xtst' else 'XOpenDisplay')
    path=Path('/lib/x86_64-linux-gnu')/soname
    libs[soname]={'resolved':found,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'package':subprocess.run(['dpkg-query','-W','-f=${Version}',pkg],capture_output=True,text=True,check=True).stdout,'required_symbol_present':bool(sym)}
for f in ['Xvfb','xkbcomp']:
    p=base/'deps/usr/bin'/f
    libs[f]={'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
mem={}
for line in Path('/proc/meminfo').read_text().splitlines()[:3]:
    k,v=line.split(':',1); mem[k]=v.strip()
env={'schema':'x11-xtest-device-cross-client-environment-a01-v1','timestamp_utc':subprocess.run(['date','-u','+%Y-%m-%dT%H:%M:%SZ'],capture_output=True,text=True,check=True).stdout.strip(),'os_release':Path('/etc/os-release').read_text(),'uname':platform.uname()._asdict(),'python':sys.version,'python_executable':sys.executable,'logical_cpu_count':os.cpu_count(),'memory_first_three_kib':mem,'resource_caps':'No CPU/memory limit applied or verified; one short Xvfb/candidate process only.','network':'Candidate source makes no network calls; Xvfb uses -nolisten tcp; UNIX socket is private-mount-namespace tmpfs.','libraries':libs,'packages':items,'setup_a05_result':(root/'setup'/'a05'/'result.txt').read_text(),'setup_a05_connectivity':(root/'setup'/'a05'/'connectivity.txt').read_text(),'shared_socket_dir_after_setup':(root/'setup'/'a05'/'shared-socket-dir-after.txt').read_text()}
(root/'ENVIRONMENT.json').write_text(json.dumps(env,indent=2,sort_keys=True)+'\n')
print(json.dumps({'package_count':len(items),'libraries':libs,'setup':env['setup_a05_result']},sort_keys=True))
