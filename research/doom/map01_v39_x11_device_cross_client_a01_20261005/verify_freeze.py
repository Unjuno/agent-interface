#!/usr/bin/env python3
"""Verify every frozen source/input hash and the empty formal output path."""
import hashlib,json
from pathlib import Path
root=Path(__file__).resolve().parent
freeze=json.loads((root/'FREEZE.json').read_text(encoding='utf-8'))
linuxbase=Path('/home/user/x11-xtest-device-cross-client-a01-20261005')
paths={'Xvfb':linuxbase/'deps/usr/bin/Xvfb','xkbcomp':linuxbase/'deps/usr/bin/xkbcomp',
       'libXtst.so.6':Path('/lib/x86_64-linux-gnu/libXtst.so.6'),
       'libXi.so.6':Path('/lib/x86_64-linux-gnu/libXi.so.6'),
       'libX11.so.6':Path('/lib/x86_64-linux-gnu/libX11.so.6')}
checks=[]
def check(name,ok,detail=''):
    checks.append({'name':name,'ok':bool(ok),'detail':detail})
for name,expected in freeze['frozen_sources'].items():
    p=paths.get(name,(root/'inputs'/name if name in ('PACKAGE_MANIFEST.json','SHA256SUMS') else root/name))
    exists=p.is_file()
    actual=hashlib.sha256(p.read_bytes()).hexdigest().upper() if exists else None
    check('sha256:'+name,exists and actual==expected.upper(),actual or 'missing')
manifest=json.loads((root/'inputs'/'PACKAGE_MANIFEST.json').read_text(encoding='utf-8'))
for row in manifest['packages']:
    p=root/'inputs'/row['file']; actual=hashlib.sha256(p.read_bytes()).hexdigest()
    check('package:'+row['package'],actual==row['sha256'],actual)
setup=(root/'setup'/'a05'/'result.txt').read_text(encoding='utf-8')
check('no-input-setup-pass','setup=PASS_NO_INPUT' in setup)
check('formal-output-path-empty',not (linuxbase/'results'/'a01'/'invocation.marker').exists() and not (root/'results'/'a01'/'raw.json').exists())
result={'schema':'x11-freeze-verification-a01-v1','checks':checks,'passed':sum(x['ok'] for x in checks),'total':len(checks),'status':'PASS' if all(x['ok'] for x in checks) else 'FAIL'}
out=root/'precheck'/'freeze_verification_a02.json'; out.parent.mkdir(exist_ok=True); out.write_text(json.dumps(result,sort_keys=True,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'status':result['status'],'passed':result['passed'],'total':result['total']},sort_keys=True))
raise SystemExit(0 if result['status']=='PASS' else 1)
