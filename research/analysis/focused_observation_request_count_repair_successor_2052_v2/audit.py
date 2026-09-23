import json,subprocess,sys
r=json.loads(subprocess.check_output([sys.executable,"experiment.py"],text=True))
assert (r["rows"],r["accepted"],r["expected_accepted"],r["mismatches"],r["authority_positive_admissions"])==(256,8,8,0,0)
print("INDEPENDENT_AUDIT_PASS",r["sha256"])