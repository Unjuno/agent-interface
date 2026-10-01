import json,subprocess,sys
r=json.loads(subprocess.check_output([sys.executable,"experiment.py"],text=True))
assert r["rows"]==64 and r["valid"]==64 and r["terminal_release_failures"]==0
print("INDEPENDENT_AUDIT_PASS",r["sha256"])
