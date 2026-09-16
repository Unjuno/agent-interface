from __future__ import annotations
import argparse,hashlib,json,re
from pathlib import Path

def sha(b:bytes)->str:return hashlib.sha256(b).hexdigest()
def parse_syms(text,name):
    m=re.search(r'key\s+<'+re.escape(name)+r'>\s*\{(.*?)\};',text,re.S)
    if not m:return []
    s=re.search(r'symbols\[Group1\]\s*=\s*\[(.*?)\]',m.group(1),re.S) or re.search(r'\[(.*?)\]',m.group(1),re.S)
    return [x.strip() for x in s.group(1).split(',')] if s else []
def audit(root:Path, plan:dict):
    errs=[]; rows=[]
    for i in range(plan['repetitions']):
        d=root/f'arm-{i:02d}'; r=json.loads((d/'result.json').read_text()); resolved=(d/'de.resolved.xkb').read_bytes(); b=(d/'baseline.server.xkb').read_bytes(); a=(d/'after.server.xkb').read_bytes()
        if sha(resolved)!=plan['resolved_sha256'] or r['resolved_sha256']!=plan['resolved_sha256']: errs.append(f'{i}:resolved_hash')
        txt=resolved.decode();
        if parse_syms(txt,'AD01')[:4]!=['q','Q','at','Greek_OMEGA']: errs.append(f'{i}:resolved_ad01')
        if not parse_syms(txt,'RALT') or parse_syms(txt,'RALT')[0]!='ISO_Level3_Shift': errs.append(f'{i}:resolved_ralt')
        if r['input_operations']!=0: errs.append(f'{i}:input')
        if r['baseline_server_sha256']!=sha(b) or r['after_server_sha256']!=sha(a): errs.append(f'{i}:server_hash')
        changed=sha(b)!=sha(a)
        if r['server_dump_changed']!=changed: errs.append(f'{i}:server_changed_receipt')
        blocked=(r['xkeyboard_present'] and r['integrity'] and r['apply']['returncode']==0 and (not r['server_dump_changed'] or not r['live_core_map_changed'] or not r['live_ad01_level3_at']))
        passed=(r['xkeyboard_present'] and r['integrity'] and r['apply']['returncode']==0 and r['server_dump_changed'] and r['live_core_map_changed'] and r['live_ad01_level3_at'])
        expected='PASS_NATIVE_XKB_MAP_ROUNDTRIP_SCOPED' if passed else ('SETUP_BLOCKED_NATIVE_XKB_APPLY' if blocked else 'FAIL_INTEGRITY')
        if r['decision']!=expected: errs.append(f'{i}:decision')
        rows.append(expected)
    summary=json.loads((root/'summary.json').read_text()); expect='PASS_NATIVE_XKB_MAP_ROUNDTRIP_SCOPED' if all(x=='PASS_NATIVE_XKB_MAP_ROUNDTRIP_SCOPED' for x in rows) else ('SETUP_BLOCKED_NATIVE_XKB_APPLY' if all(x=='SETUP_BLOCKED_NATIVE_XKB_APPLY' for x in rows) else 'FAIL_INTEGRITY')
    if summary['decision']!=expect or summary['input_operations']!=0: errs.append('summary')
    return {'status':'PASS_INDEPENDENT_AUDIT' if not errs else 'FAIL_INDEPENDENT_AUDIT','decision':expect,'errors':errs,'arms':len(rows)}
def main():
    ap=argparse.ArgumentParser();ap.add_argument('root',type=Path);ap.add_argument('--plan',type=Path,required=True);a=ap.parse_args(); o=audit(a.root,json.loads(a.plan.read_text())); print(json.dumps(o)); return 0 if o['status'].startswith('PASS') else 2
if __name__=='__main__':raise SystemExit(main())
