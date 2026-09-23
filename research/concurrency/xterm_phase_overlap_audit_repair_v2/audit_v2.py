import hashlib,json,pathlib,statistics,sys
root=pathlib.Path(__file__).parent
PINS={
 'PREDECESSOR_RAW_CASES.json':'6426b6425764adc585585eff915faea504d1ddabac38ae34720660e277ce37f8',
 'PREDECESSOR_RESULT.json':'07c44477c1e1a4ebf032ebd6443bb2bc7d8b0fab8e5a1324b7500780182946e0',
 'PREDECESSOR_AUDIT.json':'2fa51e9e8f4c8830a1ab101d37922f1a3bd7272d3932ff4667402c562006ed75',
 'PREDECESSOR_SCHEDULE.json':'a87aee9a7eb3194b950c41f85a210683c4b7321767357b125ec595544fb50cd8',
}
def h(p): return hashlib.sha256((root/p).read_bytes()).hexdigest()
raw=json.loads((root/'PREDECESSOR_RAW_CASES.json').read_text())
result=json.loads((root/'PREDECESSOR_RESULT.json').read_text())
old=json.loads((root/'PREDECESSOR_AUDIT.json').read_text())
schedule=json.loads((root/'PREDECESSOR_SCHEDULE.json').read_text())['cases']
errors=[]
for p,e in PINS.items():
 if h(p)!=e: errors.append(f'integrity:{p}:{h(p)}')
expected_old=[
 'serial_order:serial_independent-02','serial_order:serial_independent-04','serial_order:serial_shared-03','serial_order:serial_independent-01',
 'serial_order:serial_independent-05','serial_order:serial_shared-00','serial_order:serial_shared-05','serial_order:serial_independent-03',
 'serial_order:serial_shared-02','serial_order:serial_independent-00','serial_order:serial_shared-04','serial_order:serial_shared-01']
if old.get('decision')!='FAIL_REAL_XTERM_PHASE_OVERLAP' or old.get('pass') is not False or old.get('errors')!=expected_old: errors.append('predecessor_fail_signature')
if len(raw)!=24: errors.append(f'raw_count:{len(raw)}')
if [(r.get('case_id'),r.get('arm')) for r in raw] != [(r['case_id'],r['arm']) for r in schedule]: errors.append('schedule_order')
by={a:[] for a in ['serial_independent','overlap_independent','serial_shared','overlap_shared_negative']}
def events(r,kind,s): return [e for e in r.get('events',[]) if e.get('kind')==kind and e.get('surface')==s]
def first_t(r,kind,s):
 xs=events(r,kind,s); return min((e['t_ns'] for e in xs),default=None)
def terminal_t(r,s):
 return min((e['t_ns'] for e in r.get('events',[]) if e.get('surface')==s and e.get('kind') in ('done','done_already')),default=None)
for r in raw:
 a=r.get('arm')
 if a not in by: errors.append(f'arm:{a}'); continue
 by[a].append(r)
 if 'wall_ms' not in r: errors.append(f"case_failure:{r.get('case_id')}"); continue
 if r.get('keys_down')!=[]: errors.append(f"keys:{r['case_id']}")
 if any(tuple(v or ())!=('xterm','XTerm') for v in r.get('wm_class',{}).values()): errors.append(f"wm_class:{r['case_id']}")
 for s in ('A','B'):
  st=first_t(r,'started',s); dn=terminal_t(r,s)
  if st is None or dn is None or not st<dn: errors.append(f"receipt_order:{r['case_id']}:{s}")
 b_begin=first_t(r,'input_begin','B'); b_started=first_t(r,'started','B'); a_done=terminal_t(r,'A')
 if a.startswith('overlap_'):
  if None in (b_started,a_done) or not b_started<a_done: errors.append(f"overlap_order:{r['case_id']}")
 else:
  if None in (b_begin,a_done) or not a_done<b_begin: errors.append(f"serial_order:{r['case_id']}")
for a,rows in by.items():
 if len(rows)!=6: errors.append(f'n:{a}:{len(rows)}')
for a in ('serial_independent','overlap_independent','serial_shared'):
 for r in by[a]:
  if r.get('final_titles')!={'A':'A_DONE','B':'B_DONE'}: errors.append(f"final:{r['case_id']}")
for r in by['overlap_shared_negative']:
 if r.get('final_titles')!={'A':'B_DONE','B':'B_DONE'}: errors.append(f"negative:{r['case_id']}")
for a in ('serial_independent','overlap_independent'):
 for r in by[a]:
  for s in ('A','B'):
   st=first_t(r,'started',s); dn=terminal_t(r,s)
   if st is not None and dn is not None:
    ms=(dn-st)/1e6
    if not (120<=ms<=250): errors.append(f"tail:{r['case_id']}:{s}:{ms}")
sm=statistics.median(r['wall_ms'] for r in by['serial_independent']) if len(by['serial_independent'])==6 else None
om=statistics.median(r['wall_ms'] for r in by['overlap_independent']) if len(by['overlap_independent'])==6 else None
ratio=om/sm if sm else None; reduction=sm-om if sm is not None and om is not None else None
if ratio is None or ratio>0.65: errors.append(f'ratio:{ratio}')
if reduction is None or reduction<100: errors.append(f'reduction:{reduction}')
if (result.get('formal_invocations'),result.get('reruns'),result.get('replacements'),result.get('tuning_after_freeze'))!=(1,0,0,0): errors.append('predecessor_budget')
rm=result.get('metrics',{})
if sm is not None and abs(rm.get('serial_independent_median_wall_ms',-1)-sm)>1e-9: errors.append('serial_metric')
if om is not None and abs(rm.get('overlap_independent_median_wall_ms',-1)-om)>1e-9: errors.append('overlap_metric')
out={'decision':'PASS_REAL_XTERM_PHASE_OVERLAP_AUDIT_REPAIR_SCOPED' if not errors else 'FAIL_REAL_XTERM_PHASE_OVERLAP_AUDIT_REPAIR',
     'pass':not errors,'errors':errors,'audit_invocations':1,'reruns':0,'tuning':0,
     'predecessor_decision':old.get('decision'),'predecessor_errors_retained':old.get('errors'),
     'arm_counts':{a:len(v) for a,v in sorted(by.items())},'serial_median_ms':sm,'overlap_median_ms':om,'median_reduction_ms':reduction,'overlap_serial_ratio':ratio,
     'predecessor_sha256':PINS}
(root/'AUDIT_V2.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
print(json.dumps(out,sort_keys=True)); sys.exit(0 if not errors else 1)
