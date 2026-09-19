import json,subprocess,sys
r=json.loads(subprocess.check_output([sys.executable,"experiment.py"],text=True))
assert r["rows"]==256 and r["accepted"]==16 and r["mismatches"]==0 and r["authority_true_admitted"]==0
print("INDEPENDENT_AUDIT_PASS",r["sha256"])
