from check_retained_result import check

out = check()
assert out['decision'] == 'PASS_RETAINED_RESULT_PROVENANCE_SCOPED'
assert out['fresh_allocation'] is False
print('PASS retained-result provenance gate')
