"""Audit R13 evidence and preserve the malformed frozen-condition limitation."""
import hashlib,json
from pathlib import Path
PACKET=Path(__file__).resolve().parent
ROOT=Path(__file__).resolve().parents[3]
RUN=PACKET/"run"
def verify(path, resolver):
    errors=[]
    lines=path.read_text(encoding="ascii").splitlines()
    for line in lines:
        expected,rel=line.split("  ",1)
        target=resolver(rel)
        actual=hashlib.sha256(target.read_bytes()).hexdigest() if target.is_file() else None
        if actual!=expected: errors.append(rel)
    return {"entries":len(lines),"errors":errors}
pretrial=verify(PACKET/"PRETRIAL_SHA256SUMS",lambda rel:(PACKET/rel if rel in {"conditions.json","probe.py"} else ROOT/rel))
raw=verify(RUN/"SHA256SUMS",lambda rel:RUN/rel)
c=json.loads((PACKET/"conditions.effective-postrun.json").read_text(encoding="utf-8"))
d=json.loads((RUN/"probe.json").read_text(encoding="utf-8"))
ready=json.loads((RUN/"ready.json").read_text(encoding="utf-8"))
activation=json.loads((RUN/"computer-use-activation.json").read_text(encoding="utf-8"))
events=[json.loads(row) for row in (RUN/"events.jsonl").read_text(encoding="utf-8").splitlines()]
hwnd=ready["fixture"]["hwnd"]
witness=d.get("state_query_witness",[])
try:
    json.loads((PACKET/"conditions.json").read_text(encoding="utf-8")); frozen_json_valid=True
except json.JSONDecodeError:
    frozen_json_valid=False
observation={
 "activation_joined_to_exact_window":activation.get("attempt_id")==c["attempt_id"] and activation.get("fixture_window_id")==hwnd and activation.get("activate_call_returned") is True and d.get("computer_use_activation")==activation,
 "native_foreground_matches_fixture":d.get("foreground_after_cua")==hwnd and d.get("foreground_matches_fixture") is True,
 "shift_neutral_with_witness":d.get("shift_down") is False and bool(witness) and all(w.get("hwnd")==hwnd and w.get("input_desktop_active") is True for w in witness),
 "no_input_or_task_effect":d.get("input_dispatched") is False and not (RUN/"effect.json").exists() and events==[{"hwnd":hwnd,"kind":"ready"}],
 "fixture_cleanup_and_foreground_restore":d.get("cleanup_pass") is True and d.get("fixture_exit_code")==0 and d.get("foreground_after_restore")==d.get("original_foreground"),
 "frozen_source_matches":c["source_main"]==d.get("source_main"),
}
observed=all(observation.values())
audit={"attempt_id":c["attempt_id"],"disposition":"OBSERVED_SETUP_PASS_AUDIT_HOLD_INVALID_CONDITION_INPUT" if observed and not frozen_json_valid else ("PASS_STATE_READBACK_SETUP" if observed and frozen_json_valid else "HOLD_AUDIT_FAILURE"),"observed_setup_readback_pass":observed,"frozen_conditions_valid_json":frozen_json_valid,"observation_checks":observation,"pretrial_hash_audit":pretrial,"raw_hash_audit":raw,"custody_and_observation_audit_pass":observed and not pretrial["errors"] and not raw["errors"],"setup_acceptance_pass":observed and frozen_json_valid and not pretrial["errors"] and not raw["errors"],"live_expiry_recovery_or_task_effect_tested":False,"limitation":"The post-run interpreted condition file does not repair the malformed frozen conditions.json; setup acceptance is withheld."}
(PACKET/"audit.json").write_text(json.dumps(audit,indent=2,sort_keys=True)+chr(10),encoding="utf-8")
print(json.dumps(audit,indent=2,sort_keys=True))
if not audit["custody_and_observation_audit_pass"]: raise SystemExit(1)