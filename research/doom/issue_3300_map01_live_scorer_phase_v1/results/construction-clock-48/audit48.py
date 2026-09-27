from __future__ import annotations
import json,statistics,sys
from pathlib import Path

rows=json.loads(Path(sys.argv[1]).read_text()); errors=[]; reports=[]
for r in rows:
    entries=r.get('tic_entry_records',[]); events=r.get('scorer_getters',[]); reads=r.get('passive_reads',[])
    counters=[x['counter'] for x in entries]; viz=[x['viz_time'] for x in entries]
    api=[x['tic'] for x in reads]; freq=r.get('counter_frequency_hz',0)
    phases=[]
    for ix,e in enumerate(events):
        prev=[x for x in entries if x['counter']<=e['counter_lower']]
        nxt=[x for x in entries if x['counter']>=e['counter_upper']]
        if not prev or not nxt:
            errors.append({'index':r.get('index'),'getter':ix,'check':'getter_phase_not_bracketed'})
            continue
        p,n=prev[-1],nxt[0]; period=n['counter']-p['counter']
        lo=e['counter_lower']-p['counter']; hi=e['counter_upper']-p['counter']
        if period<=0 or lo<0 or hi>period:
            errors.append({'index':r.get('index'),'getter':ix,'check':'invalid_phase_interval'})
            continue
        phases.append({'getter_index':ix,'name':e['name'],'value':e.get('result'),
          'engine_viz_time_before':p['viz_time'],'engine_viz_time_after':n['viz_time'],
          'period_counter_ticks':period,'phase_lower_ticks':lo,'phase_upper_ticks':hi,
          'phase_lower_ns':lo*1e9/freq,'phase_upper_ns':hi*1e9/freq,
          'phase_width_ns':(hi-lo)*1e9/freq,'phase_fraction_lower':lo/period,'phase_fraction_upper':hi/period,
          'getter_counter_bracket_ticks':e['counter_upper']-e['counter_lower']})
    continuous=len(viz)>=2 and all(b-a==1 for a,b in zip(viz,viz[1:]))
    periods=[b-a for a,b in zip(counters,counters[1:])]
    spans=[p['phase_width_ns'] for p in phases]
    expected_names=['get_episode_time','is_episode_finished','is_player_dead','get_game_variable','get_game_variable','get_ticrate','is_episode_timeout_reached','get_episode_time']
    checks={
      'setup':r.get('setup_status')=='ok','scorer_returned':r.get('scorer_status')=='returned',
      'cleanup':r.get('cleanup',{}).get('game_closed') is True,'counter_frequency_constant':freq>0 and all(x['counter_frequency_hz']==freq for x in entries),
      'first_instruction_disassembly_gate':bool(r.get('entry_disassembly',{}).get('object_relocation_to_body')) and 'mrs' in r.get('entry_disassembly',{}).get('object',[''])[0] and 'mrs' in r.get('entry_disassembly',{}).get('linked_binary',[''])[0],
      'contiguous_viz_time':continuous,'passive_api_stale':len(api)>=100 and set(api)=={1},
      'exact_scorer_getter_sequence':[e['name'] for e in events]==expected_names,
      'all_getters_phase_bracketed':len(phases)==len(events)==8,
    }
    for k,v in checks.items():
      if not v: errors.append({'index':r.get('index'),'check':k})
    # Cross-clock calibration is diagnostic only; phase reconstruction stays in CNTVCT units.
    mono_delta=entries[-1]['monotonic_ns_after_entry']-entries[0]['monotonic_ns_after_entry'] if len(entries)>1 else 0
    counter_delta=counters[-1]-counters[0] if len(entries)>1 else 0
    calibrated=counter_delta*1e9/mono_delta if mono_delta>0 else None
    reports.append({'index':r.get('index'),'counter_frequency_hz':freq,'counter_ticks_per_ns':freq/1e9,
      'counter_quantum_ns':1e9/freq if freq else None,'engine_entry_count':len(entries),
      'engine_viz_time_range':[min(viz),max(viz)] if viz else None,'engine_viz_time_contiguous':continuous,
      'engine_median_period_ticks':int(statistics.median(periods)) if periods else None,
      'engine_median_period_ns':statistics.median(periods)*1e9/freq if periods and freq else None,
      'engine_median_rate_hz':freq/statistics.median(periods) if periods and freq else None,
      'monotonic_diagnostic_span_ns':mono_delta,'counter_calibrated_hz_over_monotonic_span':calibrated,
      'counter_calibration_error_ppm':(calibrated/freq-1)*1e6 if calibrated and freq else None,
      'passive_read_count':len(reads),'passive_api_tics':sorted(set(api)),
      'scorer_getter_count':len(events),'scorer_phase_interval_count':len(phases),
      'getter_phase_width_ns_min':min(spans) if spans else None,'getter_phase_width_ns_max':max(spans) if spans else None,
      'phase_intervals':phases,'checks':checks,'cleanup':r.get('cleanup')})
out={'schema':'issue3453-construction-clock48-independent-audit-v1','input':str(sys.argv[1]),'rows':len(rows),'errors':errors,
 'decision':'PASS_CONSTRUCTION_ONLY_CNTVCT_PHASE_INTERVALS' if rows and not errors else 'FAIL_AUDIT','formal_allocation':False,'reports':reports,
 'limitations':['Counter quantum is 1e9/CNTFRQ; this VM exposes 24 MHz (41.67 ns/tick), so ±1 ns schedule neighbors cannot be distinguished.',
 'Getter brackets cover Python/C API dispatch and getter execution; their measured widths are reported, not collapsed to point estimates.',
 'Every tic performs CNTVCT sample, clock_gettime diagnostic, and ring-buffer writes; perturbation versus uninstrumented source remains unbounded.',
 'Three construction sessions do not constitute or authorize the single frozen 120-row formal allocation.']}
print(json.dumps(out,indent=2,sort_keys=True)); raise SystemExit(bool(errors))
