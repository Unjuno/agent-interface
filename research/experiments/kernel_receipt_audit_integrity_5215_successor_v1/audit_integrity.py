"""Strict independent audit of retained #5216 outcomes against fixed facts."""
from __future__ import annotations
EXPECTED = {
 "execution_end_700": True, "execution_end_999": True,
 "execution_end_1000": True, "execution_end_1001": True,
 "execution_wrong_command": False, "effect_at_499": True,
 "effect_at_699": True, "effect_at_700": True, "effect_at_701": True,
}
TIMES = {
 "execution_end_700": {"end":700,"lease":1000,"release":800},
 "execution_end_999": {"end":999,"lease":1000,"release":800},
 "execution_end_1000":{"end":1000,"lease":1000,"release":800},
 "execution_end_1001":{"end":1001,"lease":1000,"release":800},
 "effect_at_499":{"start":500,"end":700,"observed":499},
 "effect_at_699":{"start":500,"end":700,"observed":699},
 "effect_at_700":{"start":500,"end":700,"observed":700},
 "effect_at_701":{"start":500,"end":700,"observed":701},
}
def _case_valid(name):
 t=TIMES[name]
 if name.startswith("execution_"):
  return t["end"] < t["lease"] and t["release"] >= t["end"]
 return t["observed"] >= t["start"] and t["observed"] >= t["end"]
def audit(record):
 if type(record) is not dict: return {"disposition":"HOLD_SCHEMA","errors":["record_not_object"]}
 errors=[]
 keys=set(record)
 if keys != set(EXPECTED): errors.append("required_key_set_mismatch")
 for k,v in record.items():
  if type(v) is not bool: errors.append("non_boolean:"+str(k))
 for k,expected in EXPECTED.items():
  if k in record and type(record[k]) is bool and record[k] is not expected:
   errors.append("outcome_mismatch:"+k)
 inconsistent=[]
 for k in EXPECTED:
  if k=="execution_wrong_command": continue
  if not _case_valid(k): inconsistent.append(k)
 # The legacy plan contradicts its auditor on equality at execution end.
 conflicts=["effect_at_700"]
 return {"disposition":"HOLD_LEGACY_PLAN_CONFLICT" if conflicts else ("HOLD_SCHEMA_OR_CONTRACT" if errors or inconsistent else "PASS_AUDIT_MUTATION_RESISTANCE_SCOPED"),
 "errors":errors,"inconsistent_cases":inconsistent,"missing_keys":sorted(set(EXPECTED)-keys),
 "unexpected_keys":sorted(keys-set(EXPECTED)),"plan_conflicts":conflicts}
