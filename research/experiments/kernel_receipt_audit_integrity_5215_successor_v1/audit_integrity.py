"""Independent consistency audit for the immutable #5216 boolean record."""
from __future__ import annotations
EXPECTED_KEYS={"execution_end_700","execution_end_999","execution_end_1000","execution_end_1001","execution_wrong_command","effect_at_499","effect_at_699","effect_at_700","effect_at_701"}
FACTS={
 "execution_end_700":{"end":700,"lease":1000,"release":800},
 "execution_end_999":{"end":999,"lease":1000,"release":800},
 "execution_end_1000":{"end":1000,"lease":1000,"release":800},
 "execution_end_1001":{"end":1001,"lease":1000,"release":800},
 "effect_at_499":{"start":500,"end":700,"observed":499},
 "effect_at_699":{"start":500,"end":700,"observed":699},
 "effect_at_700":{"start":500,"end":700,"observed":700},
 "effect_at_701":{"start":500,"end":700,"observed":701},
}
PLAN_CONFLICTS=("effect_at_700",)
def expected_outcome(name):
 f=FACTS[name]
 if name.startswith("execution_"):
  return f["end"] < f["lease"] and f["release"] >= f["end"]
 return f["observed"] >= f["start"] and f["observed"] >= f["end"]
def audit(record):
 if type(record) is not dict:return {"disposition":"HOLD_SCHEMA","errors":["record_not_object"],"case_mismatches":[]}
 errors=[]
 if set(record)!=EXPECTED_KEYS:errors.append("required_key_set_mismatch")
 for k,v in record.items():
  if type(v) is not bool:errors.append("non_boolean:"+str(k))
 mismatches=[]
 for k in sorted(EXPECTED_KEYS-{"execution_wrong_command"}):
  if k in record and type(record[k]) is bool and record[k] is not expected_outcome(k):mismatches.append(k)
 if "execution_wrong_command" in record and type(record["execution_wrong_command"]) is bool and record["execution_wrong_command"] is not False:mismatches.append("execution_wrong_command")
 if mismatches:errors.append("outcome_mismatch")
 if PLAN_CONFLICTS:disposition="HOLD_LEGACY_PLAN_CONFLICT"
 elif errors:disposition="HOLD_SCHEMA_OR_CONTRACT"
 else:disposition="PASS_AUDIT_MUTATION_RESISTANCE_SCOPED"
 return {"disposition":disposition,"errors":errors,"missing_keys":sorted(EXPECTED_KEYS-set(record)),"unexpected_keys":sorted(set(record)-EXPECTED_KEYS),"case_mismatches":mismatches,"plan_conflicts":list(PLAN_CONFLICTS)}
