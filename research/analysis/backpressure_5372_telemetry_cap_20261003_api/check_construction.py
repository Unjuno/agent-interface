"""Hand-worked controls only. Does not execute the formal five-tick corpus."""
from candidate import simulate
from audit import reference, check_row

for arm in ('report_only','report_cap','cap_only','rate_cap'):
    empty = simulate([0], 'honest', 0, 'unit', arm)
    assert empty['verified'] == 0 and empty['safety_serviced'] == 8
    assert empty == reference([0,0,0,0,0], 'honest', 0, 'unit', arm)

for arm, admission, peak in [('report_only',4,4),('report_cap',2,2),('cap_only',2,2),('rate_cap',2,2)]:
    result = simulate([2,2], 'zero', 0, 'stall', arm)
    assert result['admitted'] == admission and result['peak'] == peak
    assert result['verified'] == admission and not result['pending']
    assert result == reference([2,2,0,0,0], 'zero', 0, 'stall', arm)

assert simulate([2], 'high', 0, 'unit', 'report_cap')['admitted'] == 0
assert simulate([2], 'high', 0, 'unit', 'cap_only')['admitted'] == 2
assert simulate([2], 'high', 0, 'unit', 'rate_cap')['admitted'] == 1
print('PASS: empty, underreported overload, overreported refusal, rate and safety controls')
