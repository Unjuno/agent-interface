#!/usr/bin/env python3
import argparse,json,sys
from pathlib import Path

def ok_probe(p):
    return all(p[k]['rc']==0 for k in ('props','role','state'))

def audit(root):
    root=Path(root); rows=[]; errors=[]
    cases=sorted([p for p in root.glob('case-*') if p.is_dir()])
    if len(cases)!=6: errors.append(f'case_count={len(cases)}')
    expected=['matched_no_transition','selection_transition','selection_transition','matched_no_transition','matched_no_transition','selection_transition']
    for i,p in enumerate(cases):
        rp=p/'result.json'
        if not rp.exists(): errors.append(f'{p.name}:missing_result'); continue
        r=json.loads(rp.read_text()); rows.append(r)
        if r.get('task')!='INKSCAPE-ATSPI-SELECTION-TRANSITION-PATH-LIFETIME-20260917-031': errors.append(f'{p.name}:task')
        if i < len(expected) and r.get('arm')!=expected[i]: errors.append(f'{p.name}:arm={r.get("arm")} expected={expected[i]}')
        if not r.get('finished'): errors.append(f'{p.name}:unfinished')
        if r.get('listener_registration_count')!=2: errors.append(f'{p.name}:listeners')
        if not r.get('session_getaddress_match'): errors.append(f'{p.name}:session_match')
        if r.get('app_env_has_at_spi_bus_address') is not False: errors.append(f'{p.name}:explicit_addr_present')
        if not r.get('final_keymap_empty'): errors.append(f'{p.name}:keymap')
        if r.get('path_equal')!={'A':True,'B':True}: errors.append(f'{p.name}:path_equal')
        phases=r.get('phases',[])
        if len(phases)!=3: errors.append(f'{p.name}:phase_count'); continue
        want=[[],[],[]] if r.get('arm')=='matched_no_transition' else [['A'],['B'],[]]
        for j,ph in enumerate(phases):
            if ph.get('visual_selected')!=want[j]: errors.append(f'{p.name}:phase{j+1}:visual={ph.get("visual_selected")}')
            for tg in ('A','B'):
                if not ok_probe(ph['probes'][tg]): errors.append(f'{p.name}:phase{j+1}:{tg}_probe')
    ctrls=[r for r in rows if r.get('arm')=='matched_no_transition']
    sels=[r for r in rows if r.get('arm')=='selection_transition']
    control_pass=len(ctrls)==3 and not any(e for e in errors if any(f'case-{i:02d}' in e for i in (0,3,4)))
    selection_pass=len(sels)==3 and not any(e for e in errors if any(f'case-{i:02d}' in e for i in (1,2,5)))
    if not errors and len(ctrls)==3 and len(sels)==3:
        decision='REJECT_SELECTION_TRANSITION_ALONE_AS_DEFUNCT_CAUSE_SCOPED'
    else:
        def path_failure(r):
            if r.get('path_equal')!={'A':True,'B':True}: return True
            for ph in r.get('phases',[]):
                for tg in ('A','B'):
                    if not ok_probe(ph['probes'][tg]): return True
            return False
        if control_pass and len(sels)==3 and all(path_failure(r) for r in sels): decision='SELECTION_TRANSITION_PATH_DEFUNCT_OBSERVED_SCOPED'
        else: decision='HOLD'
    return {'schema':'inkscape-atspi-selection-transition-path-lifetime-audit-v1','pass':not errors,'decision':decision,'cases':len(rows),'errors':errors}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('root');ap.add_argument('--out');a=ap.parse_args();res=audit(a.root);text=json.dumps(res,indent=2,sort_keys=True)+'\n';
    if a.out: Path(a.out).write_text(text)
    print(text,end=''); return 0 if res['pass'] else 1
if __name__=='__main__': raise SystemExit(main())
