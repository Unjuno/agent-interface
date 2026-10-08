from common import load_fixture,evaluate
r=evaluate(load_fixture())
assert r['decision']=='PASS_P0_CAUSAL_TRACE_GAP_LOCALIZED_SCOPED'
assert r['semantic_node_count']==6
assert r['runtime_live_gates_unproven'] and not r['live_useful_control_proven']
print('MECHANICS_PASS')
