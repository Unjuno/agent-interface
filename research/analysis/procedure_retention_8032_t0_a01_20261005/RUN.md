# Run record

Frozen source base: `e724d6d795da2852c043cb53cfd92d5a9222a091`. Platform: Windows 11 host CPython 3.12.10, stdlib only; no dependencies installed. Final suite commands from this directory:

```text
python -m unittest -v
python -O -m unittest -v
```

Result: 18/18 PASS in both modes. `python -m json.tool study_plan.json` and the equivalent command for `synthetic_cases.json` parsed 2/2. `git diff --check` passed.

Independent raw-only command:

```text
python -c 'import json,pathlib,audit; p=json.loads(pathlib.Path("study_plan.json").read_text()); c=json.loads(pathlib.Path("synthetic_cases.json").read_text()); r=[audit.score_attempt(x["expected_steps"],x["expected_state"],x["attempt"]) for x in c["retention_cases"]]; assert audit.audit_plan(p)=={"valid":True,"errors":[]}; assert r==[x["expected_score"] for x in c["retention_cases"]]; print(json.dumps({"plan_valid":True,"retention_rows":len(r),"retention_statuses":[x["status"] for x in r],"power_approx_recruits_d05":audit.sample_size(.5),"power_approx_recruits_d035":audit.sample_size(.35)},sort_keys=True))'
```

Output:

```json
{"plan_valid": true, "power_approx_recruits_d035": 216, "power_approx_recruits_d05": 106, "retention_rows": 6, "retention_statuses": ["complete", "incomplete", "incomplete", "critical_error", "missing", "complete"]}
```

The final WSLc attempt terminated at client `E_FAIL` before tests began; per the no-silent-retry rule it was not rerun. Host-only evidence is not relabeled as WSLc.
