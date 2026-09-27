from census import load,evaluate
r=evaluate(load())
assert r['decision']=='BLOCKED_DATA'
assert r['potential_program_opportunities']==21
assert r['oracle_qualified_positive_rows']==0
assert r['semantic_negative_rows']==0
assert len(r['raw_operation_families'])>=2
assert r['independent_episode_units']==6
assert r['checks']['raw_operation_diversity_present']
assert r['checks']['episode_final_oracles_present']
assert not r['checks']['decision_oracle']
print('MECHANICS_PASS')
