#!/usr/bin/env python3
import hashlib, json, os, sys
from pathlib import Path
asset=Path(sys.argv[1])
packet=Path(sys.argv[2])
groups={'repo':asset/'repo','deps':asset/'deps','stage':asset/'stage','xkb':asset/'xkb','runner':packet/'runner'}
def manifest(name, root):
    files=[]
    for p in sorted(root.rglob('*')):
        rel=p.relative_to(root).as_posix()
        if p.is_symlink():
            target=os.readlink(p)
            files.append({'path':rel,'kind':'symlink','target':target,'sha256':hashlib.sha256(target.encode()).hexdigest()})
        elif p.is_file():
            b=p.read_bytes()
            files.append({'path':rel,'kind':'file','bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()})
    out={'schema':'agent-interface/wslc-s29-input-manifest-v1','group':name,'files':len(files),'bytes':sum(x.get('bytes',0) for x in files),'entries':files}
    (packet/'inputs'/f'{name.upper()}-MANIFEST.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    return {'files':out['files'],'bytes':out['bytes'],'manifest_sha256':hashlib.sha256((packet/'inputs'/f'{name.upper()}-MANIFEST.json').read_bytes()).hexdigest()}
summary={n:manifest(n,p) for n,p in groups.items()}
summary['stage_python_version']='3.12.3'
summary['deps_versions']={'mcp':'1.30.0','Pillow':'13.0.0','python-xlib':'system python-xlib','six':'system python-six'}
summary['xkb_source']='Ubuntu 24.04.3 /usr/share/X11/xkb'
(packet/'inputs'/'INPUTS-SUMMARY.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n')
print(json.dumps(summary,sort_keys=True))