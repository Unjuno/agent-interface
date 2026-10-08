#!/usr/bin/env python3
import json, sys
from pathlib import Path
import numpy as np
SEEDS=[9101701,9101702,9101703,9101704]

def main(root,out):
 rows=[]
 for s in SEEDS: rows.append(json.loads((Path(root)/str(s)/'CASE.json').read_text()))
 correctness=[]; cost=[]; baseline_counts=[]; cand_counts=[]; mean_red=[]; p50_red=[]; faster=0; p95_reg=[]
 for r in rows:
  s=r['seed']; full_o=r['ordinary']['FULL_DEPTH']; full_s=r['stress']['FULL_DEPTH']; c_o=r['ordinary']['CONSECUTIVE_CONFIRM']; c_s=r['stress']['CONSECUTIVE_CONFIRM']; d_s=r['stress']['DIRECT_TTC']
  if full_o['accuracy']<.98 or full_s['accuracy']<.94: correctness.append(f'{s}:full_competence')
  for sn,m,amin,agree in [('ordinary',c_o,.98,.99),('stress',c_s,.94,.98)]:
   full=r[sn]['FULL_DEPTH']
   if m['accuracy']<amin: correctness.append(f'{s}:{sn}:candidate_accuracy')
   if m['agreement_with_full']<agree: correctness.append(f'{s}:{sn}:agreement')
   if m['teacher_yield_to_exec_rate']-full['teacher_yield_to_exec_rate']>.0025+1e-12: correctness.append(f'{s}:{sn}:yield_exec_delta')
   if m['premature_yield']!=0: correctness.append(f'{s}:{sn}:premature_yield')
  if c_o['premature_exec']!=0: correctness.append(f'{s}:ordinary:premature_exec')
  if c_s['premature_exec_rate']>.001+1e-12: correctness.append(f'{s}:stress:premature_exec_gate')
  baseline_counts.append(d_s['premature_exec']); cand_counts.append(c_s['premature_exec'])
  if c_s['premature_exec']>d_s['premature_exec']: correctness.append(f'{s}:stress:safety_regression_vs_direct')
  if c_o['mean_normalized_compute']>.75: cost.append(f'{s}:ordinary:compute')
  if c_s['mean_normalized_compute']>.85: cost.append(f'{s}:stress:compute')
  if sum(x>0 for x in c_o['exit_counts'])<3: cost.append(f'{s}:exit_diversity')
  tf=r['timing_ms']['FULL_DEPTH']; tc=r['timing_ms']['CONSECUTIVE_CONFIRM']
  mr=1-tc['mean']/tf['mean']; pr=1-tc['p50']/tf['p50']; rr=tc['p95']/tf['p95']-1
  mean_red.append(mr); p50_red.append(pr); p95_reg.append(rr)
  if tc['mean']<tf['mean']: faster+=1
  if rr>.10: cost.append(f'{s}:p95_regression')
 full_comp=not any('full_competence' in x for x in correctness)
 candidate_correct=not any('full_competence' not in x for x in correctness)
 no_disc=(sum(baseline_counts)==0 and sum(cand_counts)==0)
 safety_improved=(all(c<=b for c,b in zip(cand_counts,baseline_counts)) and sum(cand_counts)<sum(baseline_counts))
 speed=(float(np.median(mean_red))>=.15 and float(np.median(p50_red))>=.15 and faster>=3)
 if not full_comp: decision='HOLD_COMPETENCE_NOT_CLOSED'
 elif not candidate_correct: decision='REJECT_CONSECUTIVE_CONFIRM_SAFETY'
 elif no_disc: decision='HOLD_NO_SAFETY_DISCRIMINATOR'
 elif not safety_improved: decision='REJECT_CONSECUTIVE_CONFIRM_SAFETY'
 elif cost or not speed: decision='HOLD_CONFIRMATION_COST'
 else: decision='PASS_CONSECUTIVE_TTC_CONFIRM_SCOPED'
 result={'task':'LOCAL-SYSTEM1-TTC-CONSECUTIVE-CONFIRM-20260917-001','decision':decision,'formal_cases':4,'formal_reruns':0,'baseline_stress_premature_counts':baseline_counts,'candidate_stress_premature_counts':cand_counts,'aggregate_baseline_stress_premature':sum(baseline_counts),'aggregate_candidate_stress_premature':sum(cand_counts),'median_mean_latency_reduction':float(np.median(mean_red)),'median_p50_latency_reduction':float(np.median(p50_red)),'candidate_mean_faster_pairs':faster,'p95_regressions':p95_reg,'correctness_violations':correctness,'cost_violations':cost,'rows':rows}
 Path(out).write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
 print(json.dumps({k:result[k] for k in ['decision','aggregate_baseline_stress_premature','aggregate_candidate_stress_premature','median_mean_latency_reduction','median_p50_latency_reduction']},sort_keys=True))
if __name__=='__main__': main(sys.argv[1],sys.argv[2])
