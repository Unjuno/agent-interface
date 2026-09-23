import json,hashlib,pathlib
p=pathlib.Path('/tmp/ai_exp1004'); r=json.loads((p/'RESULT.json').read_text()); e=[]
if r['decision']!='PASS_USEFUL_EFFECT_CLOCK_PROVENANCE_GATE_SCOPED':e.append('decision')
if r['candidate_oracle_mismatches']!=0:e.append('oracle')
if r['cross_clock_clock_bound_promotions']!=0:e.append('cross_clock_promotion')
if r['cross_clock_numeric_only_bound_promotions']<=0:e.append('no_discriminator')
if r['same_clock_parent_mismatches']!=0:e.append('parent_mismatch')
if r['parent_degeneration_pass']!=r['parent_degeneration_total']:e.append('parent_degeneration')
if r['fixed_pass']!=r['fixed_total']:e.append('fixed')
if r['malformed_controls_pass']!=3:e.append('malformed')
if r['authority_grants'] or r['task_input_calls'] or r['occupancy_mutations']:e.append('side_effect')
s=(p/'candidate.py').read_text(); body=s[s.index('def clock_bound'):]
# Bound clock check must appear before effect.t comparison in the bound path.
if body.index('clock_domain')>body.index('effect.t_ns < a.down_lo'):e.append('clock_gate_order')
if 'oracle' in s:e.append('candidate_oracle_import')
sh={f:hashlib.sha256((p/f).read_bytes()).hexdigest() for f in ['candidate.py','oracle.py','run.py','audit.py']}
out={'passed':not e,'errors':e,'result_sha256':hashlib.sha256((p/'RESULT.json').read_bytes()).hexdigest(),'source_sha256':sh}
(p/'AUDIT.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,sort_keys=True))
