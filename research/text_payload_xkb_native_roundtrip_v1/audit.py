from __future__ import annotations
import hashlib,json,re,sys
from pathlib import Path
EXPECTED_DE_SHA='3d3133ea34205324545de76b99d9f65e450d45451a705443336f71a5ac6a7ffd'
DIRECT={'at','bracketleft','bracketright','backslash','braceleft','braceright','bar','asciitilde'}

def sha(p: Path): return hashlib.sha256(p.read_bytes()).hexdigest()
def tokens(text: str):
    vals=set()
    for m in re.finditer(r'symbols\[Group1\]\s*=\s*\[(.*?)\]',text,re.S):
        parts=[x.strip() for x in m.group(1).split(',')]
        vals.update(x for x in parts[2:4] if x)
    return vals

def audit(root: Path):
    rows=json.loads((root/'results.json').read_text()); errors=[]
    if len(rows)!=3: errors.append(f'case_count:{len(rows)}')
    baseline_shas=set(); after_shas=set()
    for i,r in enumerate(rows):
        case=root/f'case-{i:02d}'
        for name in ('baseline.server.xkb','after.server.xkb','de.resolved.xkb','report.json'):
            if not (case/name).is_file(): errors.append(f'{i}:missing:{name}')
        if r.get('process_returncode')!=0: errors.append(f'{i}:process')
        if not r.get('xkeyboard_present'): errors.append(f'{i}:xkeyboard')
        if r.get('de_resolved_sha256')!=EXPECTED_DE_SHA or sha(case/'de.resolved.xkb')!=EXPECTED_DE_SHA: errors.append(f'{i}:de_sha')
        expected=tokens((case/'de.resolved.xkb').read_text())
        if not DIRECT.issubset(expected): errors.append(f'{i}:resolved_direct_missing:{sorted(DIRECT-expected)}')
        if r.get('apply_returncode')!=0: errors.append(f'{i}:apply_rc')
        baseline_shas.add(r.get('baseline_server_sha256'));after_shas.add(r.get('after_server_sha256'))
        after_tokens=tokens((case/'after.server.xkb').read_text())
        direct_after=DIRECT.issubset(after_tokens)
        observable_change=bool(r.get('server_changed') and r.get('core_map_changed') and r.get('modifier_changed'))
        r['_audit_direct_after']=direct_after;r['_audit_observable_change']=observable_change
    if len(baseline_shas)!=1: errors.append('baseline_not_stable')
    direct_all=all(r.get('_audit_direct_after') for r in rows)
    change_all=all(r.get('_audit_observable_change') for r in rows)
    if not errors and direct_all and change_all:
        decision='PASS_NATIVE_XKB_ROUNDTRIP_PREREQ'
    elif not errors:
        decision='SETUP_BLOCKED_NATIVE_XKB_APPLY'
    else:
        decision='FAIL_INTEGRITY'
    out={'status':'PASS_AUDIT' if not errors else 'FAIL_AUDIT','decision':decision,'errors':errors,
         'cases':len(rows),'direct_after_count':sum(bool(r.get('_audit_direct_after')) for r in rows),
         'observable_change_count':sum(bool(r.get('_audit_observable_change')) for r in rows)}
    (root/'audit.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,indent=2));return 0 if not errors else 1
if __name__=='__main__': raise SystemExit(audit(Path(sys.argv[1])))
