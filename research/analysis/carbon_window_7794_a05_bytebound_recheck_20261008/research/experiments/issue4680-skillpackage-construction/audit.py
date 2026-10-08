"""Independent raw-result checker; intentionally does not import skill_package."""
import copy
import hashlib
import json
import sys
from pathlib import Path

result_path=Path(sys.argv[1]); raw=result_path.read_bytes(); data=json.loads(raw)
root=Path('/src')
freeze_bytes=(root/'FREEZE.json').read_bytes(); freeze=json.loads(freeze_bytes)
errors=[]
for rel, digest in freeze.get('sha256',{}).items():
    if hashlib.sha256((root/rel).read_bytes()).hexdigest()!=digest: errors.append('FROZEN_SOURCE:'+rel)
if data.get('freeze_sha256')!=hashlib.sha256(freeze_bytes).hexdigest(): errors.append('FREEZE_DIGEST')
if data.get('source_sha256')!=freeze.get('sha256'): errors.append('SOURCE_LEDGER')
if data.get('package_sha256')!=freeze.get('sha256',{}).get('package.json'): errors.append('PACKAGE_DIGEST')
expected={
"nominal_toggle":{"name":"CLICK","arguments":{"scope_id":"workspace-7","generation":12,"target":"toggle_email_reminders"}},
"multistep_set_field":{"name":"SET_FIELD","arguments":{"scope_id":"workspace-7","generation":12,"field":"digest_frequency","value":"weekly"}},
"multistep_save":{"name":"CLICK","arguments":{"scope_id":"workspace-7","generation":12,"target":"save_settings"}},
"same_state_different_intent":{"name":"SET_FIELD","arguments":{"scope_id":"workspace-7","generation":12,"field":"timezone","value":"Asia/Tokyo"}},
"forbidden_effect":{"name":"YIELD","arguments":{"reason":"forbidden"}},
"ambiguous_missing_value":{"name":"YIELD","arguments":{"reason":"ambiguous"}},
"stale_generation":{"name":"YIELD","arguments":{"reason":"stale_scope"}},
"already_satisfied":{"name":"NO_ACTION","arguments":{"reason":"already_satisfied"}},
"local_correction":{"name":"SET_FIELD","arguments":{"scope_id":"workspace-7","generation":12,"field":"digest_frequency","value":"monthly"}},
"runtime_authority_narrower_than_package":{"name":"YIELD","arguments":{"reason":"unsupported"}},
}
rows=data.get("rows",[])
if data.get("case_count")!=10 or len(rows)!=10 or {r.get("id") for r in rows}!=set(expected): errors.append("CASE_SET")
for row in rows:
    cid=row.get("id")
    if cid not in expected: continue
    if row.get("proposal")!=expected[cid]: errors.append("PROPOSAL:"+cid)
    if row.get("expected")!=expected[cid]: errors.append("FIXTURE_EXPECTED:"+cid)
    if cid=="multistep_save" and (row.get("prior_step_id")!="multistep_set_field" or row.get("prior_step_ok") is not True): errors.append("MULTISTEP_LINEAGE")
    expected_effects={"nominal_toggle":{"email_reminders":True},"multistep_set_field":{},"multistep_save":{"digest_frequency":"weekly","saved":True},"same_state_different_intent":{},"forbidden_effect":{},"ambiguous_missing_value":{},"stale_generation":{},"already_satisfied":{"email_reminders":True},"local_correction":{},"runtime_authority_narrower_than_package":{}}
    if row.get("effect")!=expected_effects[cid]: errors.append("EFFECT:"+cid)
    authority=set(row.get("authority",{}).get("allowed_actions",[]))
    if row.get("proposal",{}).get("name") not in authority: errors.append("AUTHORITY_ACTION:"+cid)
    if row.get("proposal",{}).get("name") in {"CLICK","SET_FIELD"}:
        allowed=set(row.get("authority",{}).get("allowed_effects",[]))
        if not allowed: errors.append("AUTHORITY_EFFECT_EMPTY:"+cid)
if data.get("invalid_candidate_install_accepted") is not False or data.get("invalid_candidate_preserved_active") is not True: errors.append("ACTIVE_MUTATION_ON_REJECTION")
if data.get("valid_candidate_switch_accepted") is not True or data.get("rollback_accepted") is not True or data.get("rollback_restored_active") is not True: errors.append("SWITCH_ROLLBACK")
audit={"schema":"issue4680-independent-audit-v1","decision":"PASS_CONSTRUCTION_SCOPED" if not errors else "FAIL_CONSTRUCTION","errors":errors,"rows_checked":len(rows),"result_sha256":hashlib.sha256(raw).hexdigest()}
print(json.dumps(audit,sort_keys=True))
raise SystemExit(0 if not errors else 1)

