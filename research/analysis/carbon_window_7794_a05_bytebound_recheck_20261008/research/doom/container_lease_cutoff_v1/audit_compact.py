import json,pathlib,sys
root=pathlib.Path(sys.argv[1])
r=json.loads((root/"results/result.json").read_text())
assert r["segmentation"]["sessions"]==12
assert r["lease_cutoff"]["sessions"]==9
assert r["matched_250"]["pairs"]==3 and r["matched_250"]["all_three_lease_upper_lower"] is True
assert r["segmentation"]["missed_scorer_periods_total"]==0 and r["lease_cutoff"]["missed_scorer_periods_total"]==0
assert r["segmentation"]["scorer_leaks_total"]==0 and r["lease_cutoff"]["scorer_leaks_total"]==0
assert r["outcomes"]["gameplay_efficacy_claim"] is False
for x in r["lease_cutoff"]["deadline_to_verified_empty_median_ms"].values(): assert 0 <= x < 1
print("PASS compact retained audit")
